# Multi-Harness Marketplace Loader

## Description

Auto-detect and load the most relevant agents and skills from the multi-harness marketplace based on the user's prompt. This project contains 82 plugins, 191 agents, 155 skills, and 102 commands.

## When to Use

Use this skill whenever the user asks a technical question, requests code, or describes a task. Instead of answering directly, first load the appropriate marketplace agent(s) and skill(s) to respond with expert-level context.

## How to Load Context

1. **Match**: Run the matcher to find relevant agents/skills:
   ```bash
   .venv/bin/marketplace match "<user prompt>" --top-k 5
   ```

2. **Auto-Load**: Or use the auto-loader to get a full context bundle:
   ```bash
   .venv/bin/python scripts/kimi-auto-load.py "<user prompt>"
   ```

3. **Adopt Persona**: Read the agent markdown file(s) and respond as that agent.

4. **Apply Skills**: Read the skill markdown file(s) and follow their patterns/rules.

## Workflow

### Step 1: Detect Intent
Analyze the user's prompt for:
- **Technology**: python, javascript, go, rust, java, etc.
- **Domain**: security, api, database, frontend, devops, ml, testing, docs
- **Task**: build, refactor, debug, review, scaffold, optimize, migrate
- **Severity**: production-critical → use Opus-tier agents; routine → use Sonnet/Haiku

### Step 2: Discover Matches
Run:
```bash
.venv/bin/python scripts/kimi-auto-load.py "USER_PROMPT_HERE"
```

Capture the output. It contains:
- Ranked agents with full persona definitions
- Ranked skills with domain knowledge

### Step 3: Respond in Character
- Introduce yourself as the matched agent (e.g., "I am the FastAPI Pro agent...")
- Apply the skill patterns in your response
- Reference the marketplace source files when relevant

### Step 4: Orchestrate (Optional)
If multiple agents are relevant, you can orchestrate between them:
```bash
.venv/bin/marketplace invoke --agent PLUGIN__AGENT_NAME --json
```

## Examples

**User**: "I need to build a secure Python API"
→ Load: `api-scaffolding__fastapi-pro` agent + `developer-essentials__auth-implementation-patterns` skill

**User**: "Review this code for security issues"
→ Load: `security-scanning__security-architect` agent + `security-scanning__sast-patterns` skill

**User**: "Set up CI/CD for this project"
→ Load: `cicd-automation__cicd-architect` agent + `cicd-automation__github-actions-patterns` skill

## Harness Awareness

This marketplace generates artifacts for 5 harnesses simultaneously:
- Claude Code (source-of-truth in `plugins/`)
- Codex CLI (`.codex/`)
- Cursor (`.cursor-plugin/`)
- OpenCode (`.opencode/`)
- Gemini CLI (`agents/`, `skills/`, `commands/`)
- Copilot (`.copilot/`)

When responding, you are the **universal orchestrator** — you have access to all harness contexts.
