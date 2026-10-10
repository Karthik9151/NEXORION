"""Strict, versioned API request and response contracts."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RegisterRequest(StrictModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    workspace_name: str | None = Field(default=None, min_length=2, max_length=100)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("workspace_name")
    @classmethod
    def normalize_workspace_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Workspace name cannot be blank.")
        return cleaned


class LoginRequest(StrictModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class UserPublic(StrictModel):
    id: str
    email: EmailStr
    created_at: datetime


class WorkspacePublic(StrictModel):
    id: str
    name: str
    role: str
    created_at: datetime


class AuthResponse(StrictModel):
    user: UserPublic
    workspaces: list[WorkspacePublic]


ScenarioId = Annotated[str, Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,99}$", max_length=100)]


class MissionScope(StrictModel):
    mode: Literal["synthetic_only"]
    scenario_ids: list[ScenarioId] = Field(min_length=1, max_length=10)
    entity_ids: list[str] = Field(default_factory=list, max_length=100)
    excluded_targets: list[str] = Field(min_length=1, max_length=100)

    @field_validator("entity_ids", "excluded_targets")
    @classmethod
    def trim_items(cls, values: list[str]) -> list[str]:
        cleaned = [item.strip() for item in values]
        if any(not item for item in cleaned):
            raise ValueError("List values cannot be blank.")
        return cleaned


class MissionCreate(StrictModel):
    objective: str = Field(min_length=10, max_length=500)
    scope: MissionScope
    autonomy_tier: Literal["observe_explain", "plan", "simulate_synthetic"] = "observe_explain"

    @field_validator("objective")
    @classmethod
    def trim_objective(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 10:
            raise ValueError("Objective must contain at least 10 non-whitespace characters.")
        return cleaned


class MissionPublic(StrictModel):
    id: str
    schema_version: str
    workspace_id: str
    requester_id: str
    objective: str
    scope: MissionScope
    autonomy_tier: str
    state: str
    version: int
    created_at: datetime
    updated_at: datetime


SafeAttributeValue = str | int | float | bool | None
SensitiveAttributeTokens = ("password", "secret", "token", "cookie", "credential",
    "api_key", "private_key")


class WorldEntityCreate(StrictModel):
    entity_type: Literal["host", "service", "identity", "log_source", "dataset", "control", "other"]
    name: str = Field(min_length=1, max_length=120)
    environment_id: str = Field(default="synthetic-lab", pattern=r"^[A-Za-z0-9._-]{1,64}$")
    attributes: dict[str, SafeAttributeValue] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Entity name cannot be blank.")
        return cleaned

    @field_validator("attributes")
    @classmethod
    def validate_attributes(cls, value: dict[str, SafeAttributeValue]) -> dict[str,
        SafeAttributeValue]:
        if len(value) > 30:
            raise ValueError("At most 30 attributes are allowed.")
        for key in value:
            normalized = key.strip().lower().replace("-", "_")
            if not normalized or len(normalized) > 64:
                raise ValueError("Attribute keys must contain 1 to 64 characters.")
            if any(token in normalized for token in SensitiveAttributeTokens):
                raise ValueError("Sensitive values must not be stored in world attributes.")
        return value


class WorldEntityPublic(StrictModel):
    id: str
    schema_version: str
    workspace_id: str
    entity_type: str
    name: str
    environment_id: str
    source_class: Literal["synthetic"]
    attributes: dict[str, SafeAttributeValue]
    created_by: str
    created_at: datetime
    updated_at: datetime


class WorldRelationshipCreate(StrictModel):
    from_entity_id: str = Field(min_length=1, max_length=64)
    to_entity_id: str = Field(min_length=1, max_length=64)
    relationship_type: Literal["depends_on", "authenticates_to", "emits", "belongs_to",
        "observed_by"]


class WorldRelationshipPublic(StrictModel):
    id: str
    schema_version: str
    workspace_id: str
    from_entity_id: str
    to_entity_id: str
    relationship_type: str
    source_class: Literal["synthetic"]
    attributes: dict[str, SafeAttributeValue]
    created_by: str
    created_at: datetime


class WorldSnapshotPublic(StrictModel):
    id: str
    schema_version: str
    workspace_id: str
    mission_id: str
    sequence: int
    graph_digest: str
    entity_count: int
    relationship_count: int
    snapshot: dict[str, object]
    captured_by: str
    created_at: datetime


class SimulationRunCreate(StrictModel):
    scenario_id: ScenarioId


class EvidencePublic(StrictModel):
    id: str
    schema_version: str
    workspace_id: str
    mission_id: str
    run_id: str
    evidence_type: str
    source_class: Literal["synthetic"]
    source_ref: str
    producer: str
    producer_version: str
    content_digest: str
    payload: dict[str, object]
    limitations: list[str]
    created_at: datetime


class SimulationRunPublic(StrictModel):
    id: str
    schema_version: str
    workspace_id: str
    mission_id: str
    baseline_id: str
    scenario_id: str
    fixture_version: str
    rule_set_version: str
    input_digest: str
    output_digest: str
    outcome: str
    status: Literal["completed"]
    result: dict[str, object]
    evidence: list[EvidencePublic]
    started_at: datetime
    completed_at: datetime
