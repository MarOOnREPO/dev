# 🚀 MarOOn DEV

> **Multi-Harness Agentic Plugin Marketplace** — 83 plugins, 191 agents, 156 skills, 102 commands. 
> Built for **Kimi Code**, Claude Code, OpenAI Codex CLI, Cursor, OpenCode, Gemini CLI, and GitHub Copilot.

```
┌─────────────────────────────────────────────────────────────┐
│  ONE PROMPT → ALL PHASES → NEW FOLDER → PUSH TO GITHUB      │
│  189 agents + 169 skills working simultaneously             │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start (Kimi Code)

```bash
# 1. Clone
git clone https://github.com/MarOOnREPO/MarOOn-DEV.git
cd MarOOn-DEV

# 2. Install
uv sync

# 3. Load agents/skills for your project
.venv/bin/marketplace load-project "Your project description here" --stdout

# 4. Kimi automatically reads the context bundle and responds as the loaded agents
```

## What is MarOOn DEV?

**MarOOn DEV** is an AI-native development environment where:
- You describe your project in **one prompt**
- The system automatically loads **ALL relevant agents and skills** (up to 358 entities)
- **Multiple AI experts** work simultaneously: Architect, Backend, Frontend, Security, DevOps, Testing
- The output is a **complete project** with code, tests, Docker, and deployment configs

## Marketplace Stats

| Entity | Count |
|---|---|
| **Plugins** | 83 |
| **Agents** | 191 |
| **Skills** | 156 |
| **Commands** | 102 |
| **Harnesses** | 7 (Kimi, Claude, Codex, Cursor, OpenCode, Gemini, Copilot) |

## The 7-Phase Workflow

```
PHASE 0: Discovery        → Load 189 agents + 169 skills
PHASE 1: Design System    → UI-UX-Pro-Max generates colors/typography
PHASE 2: Architecture     → Architect Agent plans A-Z
PHASE 3: Parallel Dev     → Backend + Frontend + Security + DevOps (ALL AT ONCE)
PHASE 4: Quality          → Tests + Security scans + Evaluation
PHASE 5: Deploy           → Docker + CI/CD + VPS configs
PHASE 6: Push             → New folder + Git branch on MarOOnREPO
```

## Kimi Code Integration

### Option 1: Auto-Load (Recommended)

Just tell Kimi your project idea. The system automatically:
1. Analyzes your prompt
2. Loads matching agents/skills
3. Generates a context bundle
4. Kimi responds as the loaded agents

### Option 2: Manual Load

```bash
# Match only
.venv/bin/marketplace match "Build a fintech dashboard" --top-k 20

# Full orchestration
.venv/bin/marketplace load-project "Build a fintech dashboard" --stdout

# Quick auto-load
.venv/bin/python scripts/kimi-auto-load.py "Your prompt"
```

### Option 3: Programmatic API

```python
from marketplace.core.discovery import discover
from marketplace.core.orchestrator import MultiHarnessOrchestrator

registry = discover("plugins")
orchestrator = MultiHarnessOrchestrator(registry, harnesses=["source", "kimi", "claude", "codex"])

results = asyncio.run(orchestrator.call_all(
    plugin_name="python-development",
    agent_name="python-development__python-pro",
    skill_name="python-development__python-testing-patterns",
))
```

## Multi-Harness Support

MarOOn DEV generates native artifacts for 7 agentic harnesses simultaneously:

| Harness | Artifacts | Status |
|---|---|---|
| **Kimi Code** | `.kimi/skills/` + AGENTS.md | ✅ Native |
| **Claude Code** | `.claude-plugin/` + `plugins/` | ✅ Source of truth |
| **Codex CLI** | `.codex/skills/` + `.codex/agents/` | ✅ Generated |
| **Cursor** | `.cursor-plugin/` + `.cursor/rules/` | ✅ Generated |
| **OpenCode** | `.opencode/` | ✅ Generated |
| **Gemini CLI** | `skills/` + `agents/` + `commands/` | ✅ Generated |
| **Copilot** | `.copilot/` | ✅ Generated |

```bash
# Regenerate all harnesses
make generate-all
```

## Commands

```bash
# Show marketplace stats
marketplace stats

# List all plugins/agents/skills/commands
marketplace ls
marketplace ls --plugins
marketplace ls --agents -a
marketplace ls --skills -s
marketplace ls --commands -c

# Full project orchestration (MAX MODE)
marketplace load-project "Your project description" --stdout

# Invoke specific agent/skill across all harnesses
marketplace invoke --agent python-development__python-pro --json
marketplace invoke --skill ui-ux-pro-max__ui-ux-pro-max --json

# Sync harness artifacts
marketplace sync
```

## Project Structure

```
MarOOn-DEV/
├── marketplace/              # Core orchestrator
│   ├── core/                 # Discovery + Matcher + Orchestrator
│   ├── cli/                  # Typer CLI
│   └── harnesses/            # 7 harness adapters
├── plugins/                  # 83 plugins (source of truth)
│   ├── ui-ux-pro-max/        # Design intelligence (NEW)
│   ├── python-development/
│   ├── backend-development/
│   ├── frontend-mobile-development/
│   ├── security-scanning/
│   ├── cicd-automation/
│   └── ... (76 more)
├── tests/                    # Pytest suite
├── docs/                     # Full documentation
├── tools/                    # Multi-harness generators
├── .kimi/skills/             # Kimi Code native skills
├── .claude-plugin/           # Claude Code marketplace
├── .codex/                   # Codex CLI artifacts
├── .cursor-plugin/           # Cursor artifacts
├── .opencode/                # OpenCode artifacts
├── .copilot/                 # Copilot artifacts
├── agents/                   # Gemini CLI agents
├── skills/                   # Gemini CLI skills
├── commands/                 # Gemini CLI commands
└── AGENTS.md                 # Canonical context file
```

## Quality Gates

```bash
# Run tests
uv run pytest tests/ -v

# Validate harness artifacts
make validate STRICT=1

# Check for drift/dead links
make garden

# Evaluate plugin quality
uv run plugin-eval score plugins/your-plugin --depth quick
uv run plugin-eval certify plugins/your-plugin
```

## License

MIT — See [LICENSE](LICENSE)

---

**Built with ❤️ by MarOOn** using the wshobson/agents marketplace + custom orchestration layer.
