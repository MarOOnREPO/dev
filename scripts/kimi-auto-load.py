#!/usr/bin/env python3
"""
Kimi Auto-Loader for Multi-Harness Marketplace

Usage (from Kimi):
    python scripts/kimi-auto-load.py "your prompt here"

Outputs a context bundle of the top-matching agents + skills for Kimi to consume.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from marketplace.core.discovery import discover
from marketplace.core.matcher import PromptMatcher
from marketplace.core.models import Agent


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python kimi-auto-load.py '<your prompt>'")
        sys.exit(1)

    prompt = sys.argv[1]
    registry = discover("plugins")
    matcher = PromptMatcher(registry)
    results = matcher.match_project_aware(prompt, top_k=6)

    if not results:
        print("# No matching agents or skills found for this prompt.")
        print("# Try a more specific description of your task.")
        return

    agents = [r for r in results if isinstance(r.entity, Agent)]
    skills = [r for r in results if not isinstance(r.entity, Agent)]

    print("=" * 70)
    print("# KIMI CONTEXT BUNDLE — Auto-loaded from Multi-Harness Marketplace")
    print("=" * 70)
    print(f"# Prompt: {prompt}")
    print(f"# Matched: {len(agents)} agent(s), {len(skills)} skill(s)")
    print("=" * 70)
    print()

    # Load agents first (they set the role/persona)
    for r in agents:
        agent = r.entity
        print(f"\n{'='*70}")
        print(f"# AGENT: {agent.plugin}__{agent.name}")
        print(f"# Score: {r.score:.1f} | {r.reason}")
        print(f"# File: {agent.path}")
        print(f"{'='*70}\n")
        try:
            content = agent.path.read_text(encoding="utf-8")
            print(content)
        except Exception as e:
            print(f"# Error reading agent: {e}")

    # Load skills (they provide domain knowledge)
    for r in skills:
        skill = r.entity
        print(f"\n{'='*70}")
        print(f"# SKILL: {skill.plugin}__{skill.name}")
        print(f"# Score: {r.score:.1f} | {r.reason}")
        print(f"# File: {skill.path}")
        print(f"{'='*70}\n")
        try:
            content = skill.path.read_text(encoding="utf-8")
            print(content)
        except Exception as e:
            print(f"# Error reading skill: {e}")

    print(f"\n{'='*70}")
    print("# END OF CONTEXT BUNDLE")
    print("# You may now respond as the loaded agent(s) using the skill(s) above.")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
