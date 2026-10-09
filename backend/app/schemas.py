"""Versioned API request and response contracts."""

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
