<div align="center">

<pre>
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     ███╗   ███╗ █████╗ ██████╗  ██████╗  ███╗   ██╗             ║
║     ████╗ ████║██╔══██╗██╔══██╗██╔═══██╗████╗  ██║             ║
║     ██╔████╔██║███████║██████╔╝██║   ██║██╔██╗ ██║             ║
║     ██║╚██╔╝██║██╔══██║██╔══██╗██║   ██║██║╚██╗██║             ║
║     ██║ ╚═╝ ██║██║  ██║██║  ██║╚██████╔╝██║ ╚████║             ║
║     ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝             ║
║                                                                  ║
║              ██████╗ ███████╗██╗   ██╗                          ║
║              ██╔══██╗██╔════╝██║   ██║                          ║
║              ██║  ██║█████╗  ██║   ██║                          ║
║              ██║  ██║██╔══╝  ╚██╗ ██╔╝                          ║
║              ██████╔╝███████╗ ╚████╔╝                           ║
║              ╚═════╝ ╚══════╝  ╚═══╝                            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
</pre>

<h3>Multi-Harness Agentic Plugin Marketplace</h3>

<p>
  <img src="https://img.shields.io/badge/python-3.12+-blue.svg?style=flat-square&logo=python&logoColor=white" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/tests-15%2F15%20passing-brightgreen.svg?style=flat-square&logo=pytest&logoColor=white" alt="Tests">
  <img src="https://img.shields.io/badge/plugins-83-purple.svg?style=flat-square" alt="83 Plugins">
  <img src="https://img.shields.io/badge/agents-191-orange.svg?style=flat-square" alt="191 Agents">
  <img src="https://img.shields.io/badge/skills-156-pink.svg?style=flat-square" alt="156 Skills">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License">
</p>

<p><strong>One prompt &rarr; All phases &rarr; Working code &rarr; Push to GitHub</strong></p>

<p>
  <code>189 agents + 169 skills working simultaneously</code>
</p>

</div>

---

## What is MarOOn DEV?

**MarOOn DEV** is an AI-native development environment where you describe your project in **one prompt** and the system automatically loads **ALL relevant agents and skills** (up to 358 entities). Multiple AI experts work simultaneously — Architect, Backend, Frontend, Security, DevOps, Testing — producing a **complete project** with code, tests, Docker, and deployment configs.

Built for **Kimi Code**, Claude Code, OpenAI Codex CLI, Cursor, OpenCode, Gemini CLI, and GitHub Copilot.

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/MarOOnREPO/dev.git
cd dev

# 2. Install
uv sync

# 3. Load agents & skills for your project
.venv/bin/marketplace load-project "Your project description here" --stdout

# 4. Your AI assistant reads the context bundle and responds as the loaded agents
```

---

## Marketplace at a Glance

| Entity | Count | Description |
|--------|------:|-------------|
| **Plugins** | 83 | Modular capability packs |
| **Agents** | 191 | Specialized AI personas |
| **Skills** | 156 | Reusable workflows & tools |
| **Commands** | 102 | One-shot CLI actions |
| **Harnesses** | 7 | Native IDE/CLI integrations |

---

## The 7-Phase Workflow

```
PHASE 0  DISCOVERY      →  Load 189 agents + 169 skills
PHASE 1  DESIGN SYSTEM  →  UI-UX-Pro-Max generates colors, typography, anti-patterns
PHASE 2  ARCHITECTURE   →  Architect Agent plans A-Z
PHASE 3  PARALLEL DEV   →  Backend + Frontend + Security + DevOps  (ALL AT ONCE)
PHASE 4  QUALITY        →  Tests + Security scans + Evaluation
PHASE 5  DEPLOY         →  Docker + CI/CD + VPS configs
PHASE 6  PUSH           →  New folder + Git branch on MarOOnREPO
```

---

## Multi-Harness Support

MarOOn DEV generates native artifacts for 7 agentic harnesses simultaneously:

| Harness | Artifacts | Status |
|---------|-----------|--------|
| **Kimi Code** | `.kimi/skills/` + `AGENTS.md` | ✅ Native |
| **Claude Code** | `.claude-plugin/` + `plugins/` | ✅ Source of truth |
| **Codex CLI** | `.codex/skills/` + `.codex/agents/` | ✅ Generated |
| **Cursor** | `.cursor-plugin/` + `.cursor/rules/` | ✅ Generated |
| **OpenCode** | `.opencode/` | ✅ Generated |
| **Gemini CLI** | `skills/` + `agents/` + `commands/` | ✅ Generated |
| **Copilot** | `.copilot/` | ✅ Generated |

```bash
# Regenerate all harness artifacts
make generate-all
```

---

## CLI Commands

```bash
# Show marketplace stats
marketplace stats

# List all plugins / agents / skills / commands
marketplace ls
marketplace ls --plugins
marketplace ls --agents
marketplace ls --skills
marketplace ls --commands

# Match agents & skills to a prompt
marketplace match "Build a fintech dashboard" --top-k 20

# Full project orchestration (NUCLEAR MAX MODE)
marketplace load-project "Your project description" --stdout

# Invoke a specific agent or skill across all harnesses
marketplace invoke --agent python-development__python-pro --json
marketplace invoke --skill ui-ux-pro-max__ui-ux-pro-max --json

# Sync harness artifacts
marketplace sync
```

---

## Kimi Code Integration

### Option 1 — Auto-Load (Recommended)

Just tell Kimi your project idea. The system automatically:

1. Analyzes your prompt
2. Loads matching agents & skills
3. Generates a context bundle
4. Kimi responds as the loaded agents

### Option 2 — Manual Load

```bash
# Match only
.venv/bin/marketplace match "Build a fintech dashboard" --top-k 20

# Full orchestration
.venv/bin/marketplace load-project "Build a fintech dashboard" --stdout
```

### Option 3 — Programmatic API

```python
from marketplace.core.discovery import discover
from marketplace.core.orchestrator import MultiHarnessOrchestrator

registry = discover("plugins")
orchestrator = MultiHarnessOrchestrator(
    registry,
    harnesses=["source", "kimi", "claude", "codex"]
)

results = asyncio.run(orchestrator.call_all(
    plugin_name="python-development",
    agent_name="python-development__python-pro",
    skill_name="python-development__python-testing-patterns",
))
```

---

## Project Structure

```
dev/
├── marketplace/              # Core orchestrator
│   ├── core/                 # Discovery + Matcher + Orchestrator
│   ├── cli/                  # Typer CLI
│   └── harnesses/            # 7 harness adapters
├── plugins/                  # 83 plugins (source of truth)
│   ├── ui-ux-pro-max/        # Design intelligence
│   ├── python-development/
│   ├── backend-development/
│   ├── frontend-mobile-development/
│   ├── security-scanning/
│   ├── cicd-automation/
│   └── ... (76 more)
├── tests/                    # Pytest suite (15/15 passing)
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
├── AGENTS.md                 # Canonical context file
└── README.md                 # You are here
```

---

## Quality Gates

```bash
# Run the full test suite
uv run pytest tests/ -v

# Validate harness artifacts
make validate STRICT=1

# Check for drift / dead links
make garden

# Evaluate plugin quality
uv run plugin-eval score plugins/your-plugin --depth quick
uv run plugin-eval certify plugins/your-plugin
```

---

## License

MIT — See [LICENSE](LICENSE)

---

<div align="center">

**Built with ❤️ by MarOOn** using agents & custom orchestration layer.

</div>
