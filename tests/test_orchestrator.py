"""Tests for multi-harness orchestrator."""

import asyncio
from pathlib import Path

import pytest

from marketplace.core.discovery import Registry, discover
from marketplace.core.orchestrator import (
    ClaudeHarness,
    CodexHarness,
    GeminiHarness,
    MultiHarnessOrchestrator,
    OpenCodeHarness,
    SourceHarness,
)


@pytest.fixture
def registry() -> Registry:
    return discover("plugins")


@pytest.fixture
def orchestrator(registry: Registry) -> MultiHarnessOrchestrator:
    return MultiHarnessOrchestrator(
        registry,
        harnesses=["source", "claude", "codex", "opencode", "gemini"],
        project_root=Path("."),
    )


@pytest.mark.asyncio
async def test_call_agent(orchestrator: MultiHarnessOrchestrator) -> None:
    results = await orchestrator.call_agent("python-development__python-pro")
    assert len(results) == 5
    for r in results:
        assert r.success
        assert r.target_type == "agent"


@pytest.mark.asyncio
async def test_call_skill(orchestrator: MultiHarnessOrchestrator) -> None:
    results = await orchestrator.call_skill("python-development__python-testing-patterns")
    assert len(results) == 5
    for r in results:
        assert r.success
        assert r.target_type == "skill"


@pytest.mark.asyncio
async def test_call_command(orchestrator: MultiHarnessOrchestrator) -> None:
    results = await orchestrator.call_command("python-development__python-scaffold")
    assert len(results) == 5
    for r in results:
        assert r.success
        assert r.target_type == "command"


@pytest.mark.asyncio
async def test_call_plugin(orchestrator: MultiHarnessOrchestrator) -> None:
    results = await orchestrator.call_plugin("python-development")
    assert len(results) == 5
    for r in results:
        assert r.success
        assert r.target_type == "plugin"


@pytest.mark.asyncio
async def test_call_all(orchestrator: MultiHarnessOrchestrator) -> None:
    results = await orchestrator.call_all(
        plugin_name="python-development",
        agent_name="python-development__python-pro",
        skill_name="python-development__python-testing-patterns",
    )
    assert "plugin" in results
    assert "agent" in results
    assert "skill" in results
    for key, res_list in results.items():
        assert len(res_list) == 5
        for r in res_list:
            assert r.success


def test_harness_names() -> None:
    assert SourceHarness().name == "source"
    assert ClaudeHarness().name == "claude"
    assert CodexHarness().name == "codex"
    assert OpenCodeHarness().name == "opencode"
    assert GeminiHarness().name == "gemini"
