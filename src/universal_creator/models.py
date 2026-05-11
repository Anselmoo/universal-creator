"""Pydantic models for CLI input validation."""

from __future__ import annotations

import re
from typing import Literal, Optional

from pydantic import BaseModel, field_validator


class SkillInstallConfig(BaseModel):
    skill: str
    host: Literal["claude", "copilot", "gemini", "codex"]
    scope: Literal["local", "global"]
    overwrite: bool = False


class AgentInstallConfig(BaseModel):
    agent: str
    host: Literal["claude", "copilot", "gemini", "codex"]
    scope: Literal["local", "global"]
    overwrite: bool = False


class ScaffoldConfig(BaseModel):
    name: str
    mode: Literal["empty", "boilerplate"] = "empty"
    output_dir: str | None = "skills"
    overwrite: bool = False

    @field_validator("name")
    @classmethod
    def name_must_be_kebab(cls, v: str) -> str:
        if not re.match(r"^[a-z][a-z0-9-]*$", v):
            raise ValueError(
                f"Skill name must be lowercase kebab-case (e.g. my-skill). Got: {v!r}"
            )
        return v


class SyncConfig(BaseModel):
    from_skill: str = "agent-generator"
    overwrite: bool = True
