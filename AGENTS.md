# MarOOn DEV — Multi-Harness Agentic Plugin Marketplace

Production-ready agentic-workflow building blocks: **83 plugins**, **191 agents**, **156 skills**, **102 commands**. Native source-of-truth for Claude Code and Kimi Code; also consumed by OpenAI Codex CLI, Cursor, OpenCode, and Gemini CLI from a single Markdown source.

This file is the canonical context file. Codex / Cursor / OpenCode read it directly. Claude Code reads it via `@AGENTS.md` import in `CLAUDE.md`. **Kimi Code reads it directly as the project context file.** Gemini CLI reads it via `.gemini/settings.json` (`context.fileName`).

> **Read this file like a table of contents.** Detail lives in `docs/`. Authoring conventions live in `docs/authoring.md`. Per-harness setup and capability deltas live in [`docs/harnesses.md`](docs/harnesses.md). Gemini-specific setup is in `GEMINI.md` (also auto-loaded by Gemini CLI).

## Map

- **[README.md](README.md)** — Quick start, stats, commands
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — top-level architectural overview
- **[docs/architecture.md](docs/architecture.md)** — detailed design principles
- **[docs/plugins.md](docs/plugins.md)** — full plugin catalog (83 plugins)
- **[docs/agents.md](docs/agents.md)** — agent reference (191 agents, model tiers)
- **[docs/agent-skills.md](docs/agent-skills.md)** — skill reference (progressive disclosure)
- **[docs/usage.md](docs/usage.md)** — commands, workflows, examples
- **[docs/authoring.md](docs/authoring.md)** — portable-content style guide
- **[docs/harnesses.md](docs/harnesses.md)** — per-harness capability matrix
- **[docs/plugin-eval.md](docs/plugin-eval.md)** — three-layer quality evaluation
- **[docs/round-trip-results.md](docs/round-trip-results.md)** — real-CLI verification
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — how to contribute

## Kimi Code Integration

**MarOOn DEV** is optimized for Kimi Code CLI. When working in this project:

### Automatic Agent Loading

Kimi should use the marketplace orchestrator to automatically load relevant agents and skills for any user prompt:

```bash
# Run this command to get a full context bundle
.venv/bin/marketplace load-project "USER_PROMPT_HERE" --stdout
```

Then read the output and respond as the loaded agents.

### Manual Agent Reference

Reference any agent or skill directly:
- `@plugins/<plugin>/agents/<name>.md` — load an agent persona
- `@plugins/<plugin>/skills/<name>/SKILL.md` — load a skill

### Multi-Agent Coordination

For complex projects, coordinate between multiple agents:
1. Load the Architect Agent (`ship-mate__architect`) for planning
2. Load domain-specific agents for implementation
3. Load the Security Agent for review
4. Load the DevOps Agent for deployment

### Available Commands

```bash
marketplace stats              # Show marketplace statistics
marketplace ls                 # List all entities
marketplace match "prompt"     # Find best matches
marketplace load-project "..." # Full A-to-Z orchestration
marketplace invoke --agent ... # Invoke across harnesses
```

## Working in this repo

- Python tooling: **uv** (package manager), **ruff** (lint/format)
- Plugins live under `plugins/<name>/` with auto-discovery
- Plugin names: lowercase, hyphen-separated
- Never commit secrets

## Quality gates

```bash
make validate STRICT=1     # structural validation
make garden                # drift detection
make test                  # pytest suite
make smoke-test            # real-CLI tests
```

## Regenerating per-harness artifacts

```bash
make generate HARNESS=codex      # emits .codex/skills, .codex/agents
make generate HARNESS=cursor     # emits .cursor-plugin/, .cursor/rules/
make generate HARNESS=opencode   # emits .opencode/
make generate HARNESS=gemini     # emits skills/, agents/, commands/
make generate-all                # all harnesses
```

## Skills (cross-harness)

156 skills under `plugins/*/skills/<n>/SKILL.md` — discoverable by every harness.

## Subagents (cross-harness)

191 subagents under `plugins/*/agents/<name>.md`.

## Why this file is short

Per OpenAI's harness-engineering practice: this file is a **map**, not an encyclopedia. Procedural detail lives in skills (loaded on demand by agents). Reference material lives in `docs/`.
