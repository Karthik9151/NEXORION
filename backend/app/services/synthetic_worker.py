"""In-process worker for durable, registered synthetic jobs.

The worker intentionally uses the database as the queue and keeps execution
inside the existing API process: no broker or separately billed worker is
required. Unknown execution outcomes remain uncertain and are never replayed.
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AuditEvent,
    EvidenceRecord,
    Mission,
    SimulationRun,
    WorldSnapshot,
    new_id,
    utcnow,
)
from app.services.job_leases import (
    claim_next_job,
    confirm_job_stopped,
    reconcile_expired_leases,
)
from app.services.lifecycle import transition_mission
from app.simulation import (
    LIMITATIONS,
    RULE_SET_VERSION,
    SCENARIO_REGISTRY,
    SIMULATOR_VERSION,
    digest,
    evaluate_fixture,
    get_fixture,
    verify_fixture_result,
)
from app.stage5_models import MissionJob, MissionJobAttempt

logger = logging.getLogger("nexorion.worker")


def _review_required(db: Session, job: MissionJob, mission: Mission | None,
                     reason: str, request_id: str) -> None:
    """Persist a fail-closed outcome when work cannot be safely executed."""
    now = utcnow()
    job.status = "review_required"
    job.outcome = "execution_precondition_failed"
    job.lease_owner = None
    job.lease_expires_at = None
    job.updated_at = now
    attempt = db.scalar(select(MissionJobAttempt).where(
        MissionJobAttempt.job_id == job.id,
        MissionJobAttempt.attempt_number == job.attempt_count,
    ).with_for_update())
    if attempt is not None:
        attempt.status = "failed"
        attempt.error_category = "execution_precondition_failed"
        attempt.ended_at = now
        # No fixture execution began, so this worker has stopped its own attempt.
        attempt.termination_confirmed = True
    if mission is not None and mission.state == "running":
        transition_mission(
            db, mission=mission, actor_id=None, actor_kind="worker",
            command="fail", expected_version=mission.version,
            reason=reason, request_id=request_id,
        )
    db.add(AuditEvent(
        actor_id=None, workspace_id=job.workspace_id,
        action="mission.job_execution_blocked", resource_type="mission_job",
        resource_id=job.id, decision="deny", reason=reason[:200],
        request_id=request_id,
    ))
    db.commit()


def execute_claimed_job(
    db: Session, *, job_id: str, worker_id: str, request_id: str,
) -> SimulationRun | None:
    """Execute one claimed job, persisting run/evidence and the verification gate atomically."""
    job = db.scalar(select(MissionJob).where(
        MissionJob.id == job_id,
    ).with_for_update())
    if job is None:
        return None
    if job.lease_owner != worker_id:
        # Another worker owns it, or it has already been finalized.
        return None

    if job.status == "cancelling" and job.cancel_requested_at is not None:
        confirm_job_stopped(db, job_id=job.id, worker_id=worker_id)
        db.commit()
        return None
    if job.status != "running":
        return None
    if job.cancel_requested_at is not None:
        # The cancellation timestamp is authoritative even if status is stale.
        job.status = "cancelling"
        mission_for_cancel = db.scalar(select(Mission).where(
            Mission.id == job.mission_id,
            Mission.workspace_id == job.workspace_id,
        ).with_for_update())
        if mission_for_cancel is not None and mission_for_cancel.state == "running":
            transition_mission(
                db, mission=mission_for_cancel, actor_id=None, actor_kind="worker",
                command="cancel", expected_version=mission_for_cancel.version,
                reason="worker observed a persisted cancellation request",
                request_id=request_id,
            )
        confirm_job_stopped(db, job_id=job.id, worker_id=worker_id)
        db.commit()
        return None

    mission = db.scalar(select(Mission).where(
        Mission.id == job.mission_id,
        Mission.workspace_id == job.workspace_id,
    ).with_for_update())
    if mission is None:
        _review_required(db, job, None, "mission_missing_at_execution", request_id)
        return None
    if mission.state != "running":
        _review_required(
            db, job, mission, "mission_state_mismatch_at_execution", request_id,
        )
        return None
    if (
        mission.autonomy_tier != "simulate_synthetic"
        or mission.scope.get("mode") != "synthetic_only"
        or job.scenario_id not in mission.scope.get("scenario_ids", [])
        or job.scenario_id not in SCENARIO_REGISTRY
    ):
        _review_required(db, job, mission, "synthetic_scope_revalidation_failed", request_id)
        return None

    baseline = db.scalar(select(WorldSnapshot).where(
        WorldSnapshot.workspace_id == job.workspace_id,
        WorldSnapshot.mission_id == mission.id,
    ).order_by(WorldSnapshot.sequence.desc()).limit(1))
    if baseline is None or digest(baseline.snapshot) != baseline.graph_digest:
        _review_required(db, job, mission, "baseline_missing_or_integrity_failed", request_id)
        return None
    fixture = get_fixture(job.scenario_id)
    if fixture is None:
        _review_required(db, job, mission, "registered_fixture_missing_at_execution", request_id)
        return None

    started_at = utcnow()
    analysis = evaluate_fixture(job.scenario_id, fixture)
    fixture_consistency = verify_fixture_result(job.scenario_id, fixture, analysis)
    result = {
        **analysis,
        "fixture_consistency": fixture_consistency,
        "simulator_version": SIMULATOR_VERSION,
        "capabilities_used": [
            "read_registered_synthetic_fixture",
            "deterministic_rule_evaluation",
            "record_synthetic_evidence",
        ],
        "capabilities_not_available": [
            "external_network", "host_commands", "real_credentials", "live_system_mutation",
        ],
    }
    input_digest = digest({
        "scenario_id": job.scenario_id,
        "fixture_version": fixture["fixture_version"],
        "rule_set_version": RULE_SET_VERSION,
        "events": fixture["events"],
    })
    output_digest = digest(result)
    run_id = new_id()
    evidence_payload = {
        "payload_schema_version": "1.0",
        "scenario_id": job.scenario_id,
        "fixture_version": fixture["fixture_version"],
        "outcome": analysis["outcome"],
        "supporting_event_ids": analysis["supporting_event_ids"],
        "event_count": analysis["event_count"],
        "rule_set_version": RULE_SET_VERSION,
        "events": fixture["events"],
    }
    evidence_record = EvidenceRecord(
        id=new_id(),
        workspace_id=job.workspace_id,
        mission_id=mission.id,
        run_id=run_id,
        evidence_type="synthetic_auth_event_cluster",
        source_class="synthetic",
        source_ref=fixture["source_ref"],
        producer="nexorion-synthetic-simulator",
        producer_version=SIMULATOR_VERSION,
        content_digest=digest(evidence_payload),
        payload=evidence_payload,
        limitations=list(LIMITATIONS),
    )
    completed_at = utcnow()
    run = SimulationRun(
        id=run_id,
        workspace_id=job.workspace_id,
        mission_id=mission.id,
        baseline_id=baseline.id,
        scenario_id=job.scenario_id,
        fixture_version=fixture["fixture_version"],
        rule_set_version=RULE_SET_VERSION,
        idempotency_key=job.idempotency_key,
        input_digest=input_digest,
        output_digest=output_digest,
        outcome=analysis["outcome"],
        status="completed",
        result=result,
        started_at=started_at,
        completed_at=completed_at,
    )
    db.add(run)
    db.flush()
    db.add(evidence_record)

    # Execution completion is not a security verdict: Origo remains a separate,
    # persisted verifier operation and owns the terminal verdict.
    transition_mission(
        db, mission=mission, actor_id=None, actor_kind="synthetic-worker",
        command="begin_verification", expected_version=mission.version,
        reason="registered deterministic scenario execution completed",
        request_id=request_id,
    )
    job.status = "succeeded"
    job.outcome = "simulation_completed_pending_origo"
    job.lease_owner = None
    job.lease_expires_at = None
    job.updated_at = completed_at
    attempt = db.scalar(select(MissionJobAttempt).where(
        MissionJobAttempt.job_id == job.id,
        MissionJobAttempt.attempt_number == job.attempt_count,
    ).with_for_update())
    if attempt is not None:
        attempt.status = "completed"
        attempt.ended_at = completed_at
        attempt.termination_confirmed = True
        attempt.evidence_refs = [evidence_record.id]
    job.evidence_refs = [evidence_record.id]
    db.add(AuditEvent(
        actor_id=None, workspace_id=job.workspace_id, action="mission.job_execution_completed",
        resource_type="mission_job", resource_id=job.id, decision="allow",
        reason="deterministic_synthetic_execution_finished_verification_pending",
        request_id=request_id,
    ))
    db.add(AuditEvent(
        actor_id=None, workspace_id=job.workspace_id, action="simulation.completed",
        resource_type="simulation_run", resource_id=run.id, decision="allow",
        reason="fixed_synthetic_scenario_completed_verification_pending",
        request_id=request_id,
    ))
    db.commit()
    db.refresh(run)
    return run


def run_worker_once(
    session_factory: Callable[[], Session], *, worker_id: str,
    reconcile_expired: bool = False,
) -> bool:
    """Run one safe queue iteration; return True if a job was claimed."""
    db = session_factory()
    try:
        if reconcile_expired:
            reconcile_expired_leases(db)
            db.commit()
        claimed = claim_next_job(db, worker_id=worker_id, lease_seconds=60)
        if claimed is None:
            # claim_next_job may have persisted a fail-closed review_required row.
            db.commit()
            return False
        job_id = claimed.id
        db.commit()  # Persist the lease before any fixture evaluation starts.
        execute_claimed_job(
            db, job_id=job_id, worker_id=worker_id,
            request_id=f"worker:{worker_id}",
        )
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def worker_loop(
    session_factory: Callable[[], Session], stop_event: asyncio.Event, *, worker_id: str,
    poll_seconds: float = 1.0, recovery_seconds: float = 10.0,
) -> None:
    """Process only approved database jobs and periodically reconcile expired leases."""
    next_recovery = 0.0
    while not stop_event.is_set():
        reconcile = time.monotonic() >= next_recovery
        try:
            did_work = await asyncio.to_thread(
                run_worker_once, session_factory, worker_id=worker_id,
                reconcile_expired=reconcile,
            )
            if reconcile:
                next_recovery = time.monotonic() + recovery_seconds
        except Exception as exc:
            # Avoid logging exception messages that could contain connection details/secrets.
            logger.warning("synthetic_worker_iteration_failed exception_type=%s",
                           type(exc).__name__)
            did_work = False
        delay = min(poll_seconds, 0.1) if did_work else poll_seconds
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=delay)
        except TimeoutError:
            pass
