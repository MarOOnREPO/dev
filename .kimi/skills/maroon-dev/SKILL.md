# MarOOn DEV Skill

## Description

MarOOn DEV is a Multi-Harness Agentic Plugin Marketplace with 83 plugins, 191 agents, 156 skills, and 102 commands. This skill teaches Kimi how to use the marketplace to build complete projects with multiple AI agents working simultaneously.

## When to Use

Use this skill whenever the user describes a software project, asks for code, or wants to build something. Instead of answering directly, first load the appropriate marketplace agents and skills to respond with expert-level context.

## How to Use MarOOn DEV

### Step 1: Analyze the Prompt

Determine what the user wants:
- **Technology stack**: Python, JavaScript, Go, Rust, etc.
- **Domain**: Web, mobile, AI/ML, DevOps, security, etc.
- **Task**: Build, refactor, debug, review, deploy
- **Scale**: MVP, production, enterprise

### Step 2: Load Relevant Agents/Skills

Run the marketplace orchestrator to discover matches:

```bash
.venv/bin/marketplace match "USER_PROMPT" --top-k 10
```

Or load the full context bundle:

```bash
.venv/bin/marketplace load-project "USER_PROMPT" --stdout
```

### Step 3: Read and Apply

Read the matched agent markdown files and skill SKILL.md files. Then:

1. **Adopt the persona** of the highest-scoring agent
2. **Apply ALL relevant skills** in your answer
3. **Cross-reference** patterns from multiple skills
4. **Include**: testing, security, and infrastructure awareness

### Step 4: Multi-Agent Coordination

For complex projects, load multiple agents:

| Role | Agent | When to Load |
|---|---|---|
| Architect | `ship-mate__architect` | Complex projects requiring planning |
| Backend | `api-scaffolding__fastapi-pro` or `backend-development__backend-architect` | API/DB work |
| Frontend | `frontend-mobile-development__frontend-developer` | UI/UX work |
| Security | `backend-api-security__backend-architect` | Auth, encryption, audit |
| DevOps | `cicd-automation__kubernetes-architect` | Docker, K8s, CI/CD |
| Testing | `backend-development__tdd-orchestrator` | TDD, coverage, E2E |
| Design | `ui-design__ui-designer` + `ui-ux-pro-max` | Visual design, design system |

## Design System Generation

For any UI project, generate a design system first:

```bash
python3 plugins/ui-ux-pro-max/skills/ui-ux-pro-max/scripts/search.py \
  "PROJECT_TYPE_AND_STYLE" \
  --design-system \
  -p "ProjectName"
```

This outputs colors, typography, effects, and anti-patterns. Apply these in your response.

## Key Commands

```bash
marketplace stats                          # Show stats
marketplace ls --agents --plugin python    # List Python agents
marketplace load-project "..." --stdout    # Full orchestration
marketplace invoke --agent NAME --json     # Invoke across harnesses
```

## Harness Awareness

MarOOn DEV generates artifacts for 7 harnesses:
- **Kimi Code** (this environment)
- Claude Code
- Codex CLI
- Cursor
- OpenCode
- Gemini CLI
- GitHub Copilot

When responding, you are the **universal orchestrator** with access to all harness contexts.

## Best Practices

1. Always load agents BEFORE implementing
2. Use the Design System for any UI work
3. Include security considerations in every response
4. Suggest tests for any code you write
5. Reference the source files (`@plugins/...`) when giving advice
