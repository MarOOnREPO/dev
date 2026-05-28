"""Plugin/agent/skill/command discovery from source-of-truth."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from marketplace.core.models import Agent, Command, Plugin, Skill


class Registry:
    """In-memory registry of all discovered marketplace entities."""

    def __init__(self) -> None:
        self.plugins: dict[str, Plugin] = {}
        self.agents: dict[str, Agent] = {}
        self.skills: dict[str, Skill] = {}
        self.commands: dict[str, Command] = {}

    def add_plugin(self, plugin: Plugin) -> None:
        self.plugins[plugin.name] = plugin
        for agent in plugin.agents:
            self.agents[f"{plugin.name}__{agent.name}"] = agent
        for skill in plugin.skills:
            self.skills[f"{plugin.name}__{skill.name}"] = skill
        for command in plugin.commands:
            self.commands[f"{plugin.name}__{command.name}"] = command

    def get_plugin(self, name: str) -> Plugin | None:
        return self.plugins.get(name)

    def get_agent(self, name: str) -> Agent | None:
        return self.agents.get(name)

    def get_skill(self, name: str) -> Skill | None:
        return self.skills.get(name)

    def get_command(self, name: str) -> Command | None:
        return self.commands.get(name)

    def list_plugins(self) -> list[Plugin]:
        return list(self.plugins.values())

    def list_agents(self) -> list[Agent]:
        return list(self.agents.values())

    def list_skills(self) -> list[Skill]:
        return list(self.skills.values())

    def list_commands(self) -> list[Command]:
        return list(self.commands.values())

    def stats(self) -> dict[str, int]:
        return {
            "plugins": len(self.plugins),
            "agents": len(self.agents),
            "skills": len(self.skills),
            "commands": len(self.commands),
        }


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _read_md_frontmatter(path: Path) -> dict[str, Any]:
    """Read YAML frontmatter from a markdown file."""
    with path.open("r", encoding="utf-8") as f:
        content = f.read()
    if not content.startswith("---"):
        return {}
    try:
        _, frontmatter, _ = content.split("---", 2)
        return yaml.safe_load(frontmatter) or {}
    except ValueError:
        return {}


def discover(plugins_dir: Path | str = "plugins") -> Registry:
    """Discover all plugins from the source-of-truth directory."""
    root = Path(plugins_dir)
    registry = Registry()

    if not root.exists():
        return registry

    for plugin_path in sorted(root.iterdir()):
        if not plugin_path.is_dir():
            continue
        if plugin_path.name.startswith(".") or plugin_path.name.startswith("__"):
            continue

        plugin = _discover_plugin(plugin_path)
        if plugin:
            registry.add_plugin(plugin)

    return registry


def _discover_plugin(path: Path) -> Plugin | None:
    """Discover a single plugin from its directory."""
    # Read plugin metadata from .claude-plugin/plugin.json
    meta_path = path / ".claude-plugin" / "plugin.json"
    metadata: dict[str, Any] = {}
    if meta_path.exists():
        try:
            metadata = _load_json(meta_path)
        except Exception:
            pass

    name = metadata.get("name", path.name)
    description = metadata.get("description", "")
    version = metadata.get("version", "0.1.0")

    plugin = Plugin(
        name=name,
        path=path,
        description=description,
        version=version,
        metadata=metadata,
    )

    # Discover agents
    agents_dir = path / "agents"
    if agents_dir.exists():
        for agent_path in sorted(agents_dir.iterdir()):
            if agent_path.suffix == ".md":
                frontmatter = _read_md_frontmatter(agent_path)
                plugin.agents.append(
                    Agent(
                        name=agent_path.stem,
                        plugin=name,
                        path=agent_path,
                        description=frontmatter.get("description", ""),
                        model_tier=frontmatter.get("model", "inherit"),
                        metadata=frontmatter,
                    )
                )

    # Discover skills
    skills_dir = path / "skills"
    if skills_dir.exists():
        for skill_path in sorted(skills_dir.rglob("SKILL.md")):
            frontmatter = _read_md_frontmatter(skill_path)
            skill_name = skill_path.parent.name
            plugin.skills.append(
                Skill(
                    name=skill_name,
                    plugin=name,
                    path=skill_path,
                    description=frontmatter.get("description", ""),
                    metadata=frontmatter,
                )
            )

    # Discover commands
    commands_dir = path / "commands"
    if commands_dir.exists():
        for cmd_path in sorted(commands_dir.iterdir()):
            if cmd_path.suffix == ".md":
                frontmatter = _read_md_frontmatter(cmd_path)
                plugin.commands.append(
                    Command(
                        name=cmd_path.stem,
                        plugin=name,
                        path=cmd_path,
                        description=frontmatter.get("description", ""),
                        metadata=frontmatter,
                    )
                )

    return plugin
