"""Pydantic models for marketplace entities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class Skill(BaseModel):
    """A skill within a plugin."""

    name: str
    plugin: str
    path: Path
    description: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class Agent(BaseModel):
    """An agent within a plugin."""

    name: str
    plugin: str
    path: Path
    description: str = ""
    model_tier: str = "inherit"
    metadata: dict[str, Any] = Field(default_factory=dict)


class Command(BaseModel):
    """A command within a plugin."""

    name: str
    plugin: str
    path: Path
    description: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class Plugin(BaseModel):
    """A plugin containing agents, skills, and commands."""

    name: str
    path: Path
    description: str = ""
    version: str = "0.1.0"
    agents: list[Agent] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    commands: list[Command] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def agent_count(self) -> int:
        return len(self.agents)

    @property
    def skill_count(self) -> int:
        return len(self.skills)

    @property
    def command_count(self) -> int:
        return len(self.commands)
