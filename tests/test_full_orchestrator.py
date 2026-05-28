"""Tests for full-project orchestrator."""

from pathlib import Path

from marketplace.core.discovery import discover
from marketplace.core.full_orchestrator import FullProjectOrchestrator


def test_full_orchestrator_loads_multiple_entities() -> None:
    registry = discover("plugins")
    orchestrator = FullProjectOrchestrator(registry, project_root=Path("."))
    context = orchestrator.orchestrate(
        user_prompt="build secure python api",
        min_score=0.5,
        max_per_category=5,
    )
    assert context.total_loaded > 0
    assert len(context.agents) > 0 or len(context.skills) > 0


def test_full_orchestrator_generates_bundle() -> None:
    registry = discover("plugins")
    orchestrator = FullProjectOrchestrator(registry, project_root=Path("."))
    context = orchestrator.orchestrate(
        user_prompt="testing documentation",
        min_score=0.5,
        max_per_category=3,
    )
    bundle = orchestrator.generate_context_bundle(context)
    assert "FULL PROJECT CONTEXT BUNDLE" in bundle
    assert "INSTRUCTIONS FOR KIMI" in bundle
