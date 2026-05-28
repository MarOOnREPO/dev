"""Multi-harness orchestrator for simultaneous agent/skill/plugin invocation."""

from __future__ import annotations

import asyncio
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from marketplace.core.discovery import Registry
from marketplace.core.models import Agent, Command, Plugin, Skill


class Harness(Protocol):
    """Protocol for harness adapters."""

    name: str

    async def invoke_agent(self, agent: Agent, context: dict[str, Any]) -> dict[str, Any]: ...
    async def invoke_skill(self, skill: Skill, context: dict[str, Any]) -> dict[str, Any]: ...
    async def invoke_command(self, command: Command, context: dict[str, Any]) -> dict[str, Any]: ...
    async def invoke_plugin(self, plugin: Plugin, context: dict[str, Any]) -> dict[str, Any]: ...


@dataclass
class InvocationResult:
    """Result of a single harness invocation."""

    harness: str
    target_type: str  # agent, skill, command, plugin
    target_name: str
    success: bool
    stdout: str = ""
    stderr: str = ""
    data: dict[str, Any] = field(default_factory=dict)


class SourceHarness:
    """Source-of-truth harness that reads directly from plugins/."""

    name = "source"

    async def invoke_agent(self, agent: Agent, context: dict[str, Any]) -> dict[str, Any]:
        return {"path": str(agent.path), "model_tier": agent.model_tier}

    async def invoke_skill(self, skill: Skill, context: dict[str, Any]) -> dict[str, Any]:
        return {"path": str(skill.path)}

    async def invoke_command(self, command: Command, context: dict[str, Any]) -> dict[str, Any]:
        return {"path": str(command.path)}

    async def invoke_plugin(self, plugin: Plugin, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "path": str(plugin.path),
            "agents": [a.name for a in plugin.agents],
            "skills": [s.name for s in plugin.skills],
            "commands": [c.name for c in plugin.commands],
        }


class ClaudeHarness:
    """Claude Code harness adapter."""

    name = "claude"

    async def invoke_agent(self, agent: Agent, context: dict[str, Any]) -> dict[str, Any]:
        return {"action": f"/agent {agent.plugin}__{agent.name}", "model_tier": agent.model_tier}

    async def invoke_skill(self, skill: Skill, context: dict[str, Any]) -> dict[str, Any]:
        return {"action": f"/skill {skill.plugin}__{skill.name}"}

    async def invoke_command(self, command: Command, context: dict[str, Any]) -> dict[str, Any]:
        return {"action": f"/command {command.plugin}__{command.name}"}

    async def invoke_plugin(self, plugin: Plugin, context: dict[str, Any]) -> dict[str, Any]:
        return {"action": f"/plugin install {plugin.name}"}


class CodexHarness:
    """OpenAI Codex CLI harness adapter."""

    name = "codex"

    def __init__(self, project_root: Path = Path(".")) -> None:
        self.project_root = project_root

    async def invoke_agent(self, agent: Agent, context: dict[str, Any]) -> dict[str, Any]:
        toml_path = self.project_root / ".codex" / "agents" / f"{agent.plugin}__{agent.name}.toml"
        return {"artifact": str(toml_path), "exists": toml_path.exists()}

    async def invoke_skill(self, skill: Skill, context: dict[str, Any]) -> dict[str, Any]:
        skill_dir = self.project_root / ".codex" / "skills" / f"{skill.plugin}__{skill.name}"
        return {"artifact_dir": str(skill_dir), "exists": skill_dir.exists()}

    async def invoke_command(self, command: Command, context: dict[str, Any]) -> dict[str, Any]:
        skill_dir = self.project_root / ".codex" / "skills" / f"{command.plugin}__{command.name}"
        return {"artifact_dir": str(skill_dir), "exists": skill_dir.exists()}

    async def invoke_plugin(self, plugin: Plugin, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "artifacts": f".codex/skills/{plugin.name}__*",
            "agent_count": len(plugin.agents),
            "skill_count": len(plugin.skills),
        }


class OpenCodeHarness:
    """OpenCode harness adapter."""

    name = "opencode"

    def __init__(self, project_root: Path = Path(".")) -> None:
        self.project_root = project_root

    async def invoke_agent(self, agent: Agent, context: dict[str, Any]) -> dict[str, Any]:
        md_path = self.project_root / ".opencode" / "agents" / f"{agent.plugin}__{agent.name}.md"
        return {"artifact": str(md_path), "exists": md_path.exists()}

    async def invoke_skill(self, skill: Skill, context: dict[str, Any]) -> dict[str, Any]:
        skill_dir = self.project_root / ".opencode" / "skills" / f"{skill.plugin}-{skill.name}"
        return {"artifact_dir": str(skill_dir), "exists": skill_dir.exists()}

    async def invoke_command(self, command: Command, context: dict[str, Any]) -> dict[str, Any]:
        md_path = self.project_root / ".opencode" / "commands" / f"{command.plugin}__{command.name}.md"
        return {"artifact": str(md_path), "exists": md_path.exists()}

    async def invoke_plugin(self, plugin: Plugin, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "artifacts": f".opencode/{{agents,commands,skills}}/{plugin.name}__*",
            "agent_count": len(plugin.agents),
            "skill_count": len(plugin.skills),
            "command_count": len(plugin.commands),
        }


class GeminiHarness:
    """Gemini CLI harness adapter."""

    name = "gemini"

    def __init__(self, project_root: Path = Path(".")) -> None:
        self.project_root = project_root

    async def invoke_agent(self, agent: Agent, context: dict[str, Any]) -> dict[str, Any]:
        md_path = self.project_root / "agents" / f"{agent.plugin}__{agent.name}.md"
        return {"artifact": str(md_path), "exists": md_path.exists()}

    async def invoke_skill(self, skill: Skill, context: dict[str, Any]) -> dict[str, Any]:
        skill_dir = self.project_root / "skills" / f"{skill.plugin}__{skill.name}"
        return {"artifact_dir": str(skill_dir), "exists": skill_dir.exists()}

    async def invoke_command(self, command: Command, context: dict[str, Any]) -> dict[str, Any]:
        toml_path = self.project_root / "commands" / f"{command.plugin}__{command.name}.toml"
        return {"artifact": str(toml_path), "exists": toml_path.exists()}

    async def invoke_plugin(self, plugin: Plugin, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "artifacts": f"{{agents,skills,commands}}/{plugin.name}__*",
            "agent_count": len(plugin.agents),
            "skill_count": len(plugin.skills),
            "command_count": len(plugin.commands),
        }


class CursorHarness:
    """Cursor harness adapter."""

    name = "cursor"

    def __init__(self, project_root: Path = Path(".")) -> None:
        self.project_root = project_root

    async def invoke_agent(self, agent: Agent, context: dict[str, Any]) -> dict[str, Any]:
        md_path = self.project_root / ".cursor" / "rules" / f"{agent.name}.mdc"
        return {"artifact": str(md_path), "exists": md_path.exists()}

    async def invoke_skill(self, skill: Skill, context: dict[str, Any]) -> dict[str, Any]:
        return {"note": "Cursor reads .claude/skills/ directly — no re-emit needed"}

    async def invoke_command(self, command: Command, context: dict[str, Any]) -> dict[str, Any]:
        return {"note": "Cursor reads .claude/commands/ directly — no re-emit needed"}

    async def invoke_plugin(self, plugin: Plugin, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "marketplace": str(self.project_root / ".cursor-plugin" / "marketplace.json"),
            "exists": (self.project_root / ".cursor-plugin" / "marketplace.json").exists(),
        }


class CopilotHarness:
    """GitHub Copilot harness adapter."""

    name = "copilot"

    def __init__(self, project_root: Path = Path(".")) -> None:
        self.project_root = project_root

    async def invoke_agent(self, agent: Agent, context: dict[str, Any]) -> dict[str, Any]:
        md_path = self.project_root / ".copilot" / "agents" / f"{agent.plugin}__{agent.name}.md"
        return {"artifact": str(md_path), "exists": md_path.exists()}

    async def invoke_skill(self, skill: Skill, context: dict[str, Any]) -> dict[str, Any]:
        skill_dir = self.project_root / ".copilot" / "skills" / f"{skill.plugin}__{skill.name}"
        return {"artifact_dir": str(skill_dir), "exists": skill_dir.exists()}

    async def invoke_command(self, command: Command, context: dict[str, Any]) -> dict[str, Any]:
        skill_dir = self.project_root / ".copilot" / "skills" / f"{command.plugin}__{command.name}"
        return {"artifact_dir": str(skill_dir), "exists": skill_dir.exists()}

    async def invoke_plugin(self, plugin: Plugin, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "artifacts": f".copilot/{{agents,skills,commands}}/{plugin.name}__*",
            "agent_count": len(plugin.agents),
            "skill_count": len(plugin.skills),
            "command_count": len(plugin.commands),
        }


HARNESS_MAP: dict[str, type[Harness]] = {
    "source": SourceHarness,
    "claude": ClaudeHarness,
    "codex": CodexHarness,
    "opencode": OpenCodeHarness,
    "gemini": GeminiHarness,
    "cursor": CursorHarness,
    "copilot": CopilotHarness,
}


class MultiHarnessOrchestrator:
    """Orchestrate simultaneous invocations across multiple harnesses."""

    def __init__(
        self,
        registry: Registry,
        harnesses: list[str] | None = None,
        project_root: Path = Path("."),
    ) -> None:
        self.registry = registry
        self.project_root = project_root
        self.harnesses: list[Harness] = []
        for name in harnesses or list(HARNESS_MAP.keys()):
            cls = HARNESS_MAP.get(name)
            if cls:
                if name in ("codex", "opencode", "gemini", "cursor", "copilot"):
                    self.harnesses.append(cls(project_root=project_root))
                else:
                    self.harnesses.append(cls())

    async def call_agent(
        self,
        agent_name: str,
        context: dict[str, Any] | None = None,
        harnesses: list[str] | None = None,
    ) -> list[InvocationResult]:
        agent = self.registry.get_agent(agent_name)
        if not agent:
            raise ValueError(f"Agent not found: {agent_name}")
        return await self._invoke_across_harnesses(
            "agent", agent_name, lambda h: h.invoke_agent(agent, context or {}), harnesses
        )

    async def call_skill(
        self,
        skill_name: str,
        context: dict[str, Any] | None = None,
        harnesses: list[str] | None = None,
    ) -> list[InvocationResult]:
        skill = self.registry.get_skill(skill_name)
        if not skill:
            raise ValueError(f"Skill not found: {skill_name}")
        return await self._invoke_across_harnesses(
            "skill", skill_name, lambda h: h.invoke_skill(skill, context or {}), harnesses
        )

    async def call_command(
        self,
        command_name: str,
        context: dict[str, Any] | None = None,
        harnesses: list[str] | None = None,
    ) -> list[InvocationResult]:
        command = self.registry.get_command(command_name)
        if not command:
            raise ValueError(f"Command not found: {command_name}")
        return await self._invoke_across_harnesses(
            "command", command_name, lambda h: h.invoke_command(command, context or {}), harnesses
        )

    async def call_plugin(
        self,
        plugin_name: str,
        context: dict[str, Any] | None = None,
        harnesses: list[str] | None = None,
    ) -> list[InvocationResult]:
        plugin = self.registry.get_plugin(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin not found: {plugin_name}")
        return await self._invoke_across_harnesses(
            "plugin", plugin_name, lambda h: h.invoke_plugin(plugin, context or {}), harnesses
        )

    async def call_all(
        self,
        plugin_name: str | None = None,
        agent_name: str | None = None,
        skill_name: str | None = None,
        command_name: str | None = None,
        context: dict[str, Any] | None = None,
        harnesses: list[str] | None = None,
    ) -> dict[str, list[InvocationResult]]:
        """Call any combination of plugin/agent/skill/command simultaneously."""
        results: dict[str, list[InvocationResult]] = {}
        tasks = []

        if plugin_name:
            tasks.append(("plugin", self.call_plugin(plugin_name, context, harnesses)))
        if agent_name:
            tasks.append(("agent", self.call_agent(agent_name, context, harnesses)))
        if skill_name:
            tasks.append(("skill", self.call_skill(skill_name, context, harnesses)))
        if command_name:
            tasks.append(("command", self.call_command(command_name, context, harnesses)))

        for key, coro in tasks:
            results[key] = await coro

        return results

    async def _invoke_across_harnesses(
        self,
        target_type: str,
        target_name: str,
        invoker: Any,
        harness_filter: list[str] | None = None,
    ) -> list[InvocationResult]:
        harnesses = self.harnesses
        if harness_filter:
            harnesses = [h for h in harnesses if h.name in harness_filter]

        async def _run(h: Harness) -> InvocationResult:
            try:
                data = await invoker(h)
                return InvocationResult(
                    harness=h.name,
                    target_type=target_type,
                    target_name=target_name,
                    success=True,
                    data=data,
                )
            except Exception as e:
                return InvocationResult(
                    harness=h.name,
                    target_type=target_type,
                    target_name=target_name,
                    success=False,
                    stderr=str(e),
                )

        return await asyncio.gather(*[_run(h) for h in harnesses])
