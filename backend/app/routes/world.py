"""Workspace-scoped synthetic digital-world graph and baseline snapshots."""

import hashlib
import json

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_csrf, require_workspace_membership
from app.errors import ApiError
from app.models import (
    AuditEvent,
    Mission,
    User,
    WorldEntity,
    WorldRelationship,
    WorldSnapshot,
    new_id,
    utcnow,
)
from app.schemas import (
    WorldEntityCreate,
    WorldEntityPublic,
    WorldRelationshipCreate,
    WorldRelationshipPublic,
    WorldSnapshotPublic,
)

router = APIRouter(tags=["digital-world"])


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _entity_public(entity: WorldEntity) -> WorldEntityPublic:
    return WorldEntityPublic(
        id=entity.id,
        schema_version=entity.schema_version,
        workspace_id=entity.workspace_id,
        entity_type=entity.entity_type,
        name=entity.name,
        environment_id=entity.environment_id,
        source_class="synthetic",
        attributes=entity.attributes,
        created_by=entity.created_by,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def _relationship_public(relationship: WorldRelationship) -> WorldRelationshipPublic:
    return WorldRelationshipPublic(
        id=relationship.id,
        schema_version=relationship.schema_version,
        workspace_id=relationship.workspace_id,
        from_entity_id=relationship.from_entity_id,
        to_entity_id=relationship.to_entity_id,
        relationship_type=relationship.relationship_type,
        source_class="synthetic",
        attributes=relationship.attributes,
        created_by=relationship.created_by,
        created_at=relationship.created_at,
    )


def _snapshot_public(snapshot: WorldSnapshot) -> WorldSnapshotPublic:
    graph = snapshot.snapshot
    return WorldSnapshotPublic(
        id=snapshot.id,
        schema_version=snapshot.schema_version,
        workspace_id=snapshot.workspace_id,
        mission_id=snapshot.mission_id,
        sequence=snapshot.sequence,
        graph_digest=snapshot.graph_digest,
        entity_count=len(graph.get("entities", [])),
        relationship_count=len(graph.get("relationships", [])),
        snapshot=graph,
        captured_by=snapshot.captured_by,
        created_at=snapshot.created_at,
    )


def _require_mission(db: Session, workspace_id: str, mission_id: str) -> Mission:
    mission = db.scalar(
        select(Mission).where(Mission.id == mission_id, Mission.workspace_id == workspace_id)
    )
    if mission is None:
        raise ApiError(404, "MISSION_NOT_FOUND", "The requested mission was not found.")
    return mission


def _audit(
    request: Request,
    user: User,
    workspace_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    reason: str,
) -> AuditEvent:
    return AuditEvent(
        actor_id=user.id,
        workspace_id=workspace_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        decision="allow",
        reason=reason,
        request_id=request.state.request_id,
    )


@router.post("/world/entities", response_model=WorldEntityPublic, status_code=201)
def create_world_entity(
    payload: WorldEntityCreate,
    request: Request,
    user: User = Depends(get_current_user),
    _csrf_ok: None = Depends(require_csrf),
    db: Session = Depends(get_db),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
) -> WorldEntityPublic:
    require_workspace_membership(db, user_id=user.id, workspace_id=workspace_id)
    entity = WorldEntity(
        id=new_id(),
        workspace_id=workspace_id,
        entity_type=payload.entity_type,
        name=payload.name,
        environment_id=payload.environment_id,
        source_class="synthetic",
        attributes=payload.attributes,
        created_by=user.id,
    )
    db.add(entity)
    db.flush()
    db.add(_audit(request, user, workspace_id, "world.entity.created", "world_entity", entity.id, "synthetic_entity_created"))
    db.commit()
    db.refresh(entity)
    return _entity_public(entity)


@router.get("/world/entities", response_model=list[WorldEntityPublic])
def list_world_entities(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0, le=10000),
) -> list[WorldEntityPublic]:
    require_workspace_membership(db, user_id=user.id, workspace_id=workspace_id)
    rows = db.scalars(
        select(WorldEntity)
        .where(WorldEntity.workspace_id == workspace_id)
        .order_by(WorldEntity.created_at.asc(), WorldEntity.id.asc())
        .limit(limit)
        .offset(offset)
    ).all()
    return [_entity_public(entity) for entity in rows]


@router.post("/world/relationships", response_model=WorldRelationshipPublic, status_code=201)
def create_world_relationship(
    payload: WorldRelationshipCreate,
    request: Request,
    user: User = Depends(get_current_user),
    _csrf_ok: None = Depends(require_csrf),
    db: Session = Depends(get_db),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
) -> WorldRelationshipPublic:
    require_workspace_membership(db, user_id=user.id, workspace_id=workspace_id)
    if payload.from_entity_id == payload.to_entity_id:
        raise ApiError(422, "INVALID_WORLD_RELATIONSHIP", "A relationship must connect two distinct entities.")
    endpoint_ids = {payload.from_entity_id, payload.to_entity_id}
    endpoints = db.scalars(
        select(WorldEntity).where(
            WorldEntity.workspace_id == workspace_id,
            WorldEntity.id.in_(endpoint_ids),
        )
    ).all()
    if {entity.id for entity in endpoints} != endpoint_ids:
        raise ApiError(404, "WORLD_ENTITY_NOT_FOUND", "One or more entities were not found in this workspace.")

    relationship = WorldRelationship(
        id=new_id(),
        workspace_id=workspace_id,
        from_entity_id=payload.from_entity_id,
        to_entity_id=payload.to_entity_id,
        relationship_type=payload.relationship_type,
        source_class="synthetic",
        attributes={},
        created_by=user.id,
    )
    db.add(relationship)
    db.flush()
    db.add(_audit(request, user, workspace_id, "world.relationship.created", "world_relationship", relationship.id, "synthetic_relationship_created"))
    db.commit()
    db.refresh(relationship)
    return _relationship_public(relationship)


@router.get("/world/relationships", response_model=list[WorldRelationshipPublic])
def list_world_relationships(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0, le=10000),
) -> list[WorldRelationshipPublic]:
    require_workspace_membership(db, user_id=user.id, workspace_id=workspace_id)
    rows = db.scalars(
        select(WorldRelationship)
        .where(WorldRelationship.workspace_id == workspace_id)
        .order_by(WorldRelationship.created_at.asc(), WorldRelationship.id.asc())
        .limit(limit)
        .offset(offset)
    ).all()
    return [_relationship_public(relationship) for relationship in rows]


@router.post("/missions/{mission_id}/baselines", response_model=WorldSnapshotPublic, status_code=201)
def capture_mission_baseline(
    mission_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    _csrf_ok: None = Depends(require_csrf),
    db: Session = Depends(get_db),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
) -> WorldSnapshotPublic:
    require_workspace_membership(db, user_id=user.id, workspace_id=workspace_id)
    mission = _require_mission(db, workspace_id, mission_id)
    scoped_entity_ids = mission.scope.get("entity_ids", [])
    entity_query = select(WorldEntity).where(WorldEntity.workspace_id == workspace_id)
    if scoped_entity_ids:
        entity_query = entity_query.where(WorldEntity.id.in_(scoped_entity_ids))
    entities = db.scalars(entity_query.order_by(WorldEntity.id.asc())).all()
    if scoped_entity_ids and {entity.id for entity in entities} != set(scoped_entity_ids):
        raise ApiError(404, "WORLD_ENTITY_NOT_FOUND", "A scoped entity was not found in this workspace.")
    selected_ids = {entity.id for entity in entities}
    relationship_query = select(WorldRelationship).where(WorldRelationship.workspace_id == workspace_id)
    relationships = db.scalars(relationship_query.order_by(WorldRelationship.id.asc())).all()
    relationships = [
        relationship for relationship in relationships
        if relationship.from_entity_id in selected_ids and relationship.to_entity_id in selected_ids
    ]
    graph = {
        "schema_version": "1.0",
        "source_class": "synthetic",
        "mission_id": mission.id,
        "entities": [
            {
                "id": item.id,
                "entity_type": item.entity_type,
                "name": item.name,
                "environment_id": item.environment_id,
                "source_class": item.source_class,
                "attributes": item.attributes,
                "created_by": item.created_by,
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat(),
            }
            for item in entities
        ],
        "relationships": [
            {
                "id": item.id,
                "from_entity_id": item.from_entity_id,
                "to_entity_id": item.to_entity_id,
                "relationship_type": item.relationship_type,
                "source_class": item.source_class,
                "attributes": item.attributes,
                "created_by": item.created_by,
                "created_at": item.created_at.isoformat(),
            }
            for item in relationships
        ],
    }
    next_sequence = (db.scalar(
        select(func.max(WorldSnapshot.sequence)).where(WorldSnapshot.mission_id == mission.id)
    ) or 0) + 1
    snapshot = WorldSnapshot(
        id=new_id(),
        workspace_id=workspace_id,
        mission_id=mission.id,
        sequence=next_sequence,
        graph_digest=_canonical_digest(graph),
        snapshot=graph,
        captured_by=user.id,
    )
    db.add(snapshot)
    db.flush()
    db.add(_audit(request, user, workspace_id, "world.baseline.captured", "world_snapshot", snapshot.id, "versioned_synthetic_baseline_captured"))
    db.commit()
    db.refresh(snapshot)
    return _snapshot_public(snapshot)


@router.get("/missions/{mission_id}/baselines", response_model=list[WorldSnapshotPublic])
def list_mission_baselines(
    mission_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
) -> list[WorldSnapshotPublic]:
    require_workspace_membership(db, user_id=user.id, workspace_id=workspace_id)
    _require_mission(db, workspace_id, mission_id)
    rows = db.scalars(
        select(WorldSnapshot)
        .where(WorldSnapshot.mission_id == mission_id, WorldSnapshot.workspace_id == workspace_id)
        .order_by(WorldSnapshot.sequence.asc())
    ).all()
    return [_snapshot_public(item) for item in rows]
