#!/usr/bin/env python3
"""
Kimi Full Orchestrator — A-to-Z project analysis with MAX agents/skills.

Usage:
    python scripts/kimi-full-orchestrate.py "your prompt" [project_dir]

Outputs a massive context bundle to stdout for Kimi to consume directly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from marketplace.core.discovery import discover
from marketplace.core.full_orchestrator import FullProjectOrchestrator


def main() -> None:
    prompt = sys.argv[1] if len(sys.argv) > 1 else ""
    project_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".")

    registry = discover("plugins")
    orchestrator = FullProjectOrchestrator(registry, project_root=project_dir)

    context = orchestrator.orchestrate(
        user_prompt=prompt,
        min_score=0.4,
        max_per_category=15,
        load_tests=True,
        load_security=True,
        load_infra=True,
        load_docs=True,
        load_orchestrator=True,
    )

    bundle = orchestrator.generate_context_bundle(context)
    print(bundle)


if __name__ == "__main__":
    main()
