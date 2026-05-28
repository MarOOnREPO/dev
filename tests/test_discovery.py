"""Tests for marketplace discovery."""

from pathlib import Path

from marketplace.core.discovery import Registry, discover
from marketplace.core.models import Agent, Command, Plugin, Skill


def test_registry_empty() -> None:
    reg = Registry()
    assert reg.stats() == {"plugins": 0, "agents": 0, "skills": 0, "commands": 0}


def test_registry_add_plugin() -> None:
    reg = Registry()
    plugin = Plugin(
        name="test-plugin",
        path=Path("."),
        agents=[Agent(name="agent1", plugin="test-plugin", path=Path("."))],
        skills=[Skill(name="skill1", plugin="test-plugin", path=Path("."))],
        commands=[Command(name="cmd1", plugin="test-plugin", path=Path("."))],
    )
    reg.add_plugin(plugin)
    assert reg.stats() == {"plugins": 1, "agents": 1, "skills": 1, "commands": 1}
    assert reg.get_plugin("test-plugin") == plugin
    assert reg.get_agent("test-plugin__agent1") is not None
    assert reg.get_skill("test-plugin__skill1") is not None
    assert reg.get_command("test-plugin__cmd1") is not None


def test_discover_finds_plugins() -> None:
    reg = discover("plugins")
    assert reg.stats()["plugins"] > 0
    assert "python-development" in reg.plugins or "python-dev" in reg.plugins
