"""CLI for multi-harness marketplace orchestration."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from marketplace.core.discovery import Registry, discover
from marketplace.core.full_orchestrator import FullProjectOrchestrator
from marketplace.core.matcher import PromptMatcher, find_matches
from marketplace.core.models import Agent
from marketplace.core.orchestrator import MultiHarnessOrchestrator

app = typer.Typer(help="MarOOn DEV — Multi-Harness Agentic Plugin Marketplace CLI")
console = Console()

ALL_HARNESSES = ["source", "claude", "codex", "cursor", "opencode", "gemini", "copilot"]


def _get_registry() -> Registry:
    return discover("plugins")


@app.command(name="ls")
def list_entities(
    show_plugins: bool = typer.Option(False, "--plugins", "-p", help="List plugins"),
    show_agents: bool = typer.Option(False, "--agents", "-a", help="List agents"),
    show_skills: bool = typer.Option(False, "--skills", "-s", help="List skills"),
    show_commands: bool = typer.Option(False, "--commands", "-c", help="List commands"),
    plugin_filter: str = typer.Option("", "--plugin", help="Filter by plugin name"),
) -> None:
    """List marketplace entities."""
    registry = _get_registry()

    # Default to all if none specified
    if not any([show_plugins, show_agents, show_skills, show_commands]):
        show_plugins = show_agents = show_skills = show_commands = True

    if show_plugins:
        table = Table(title="Plugins")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="magenta")
        table.add_column("Agents", justify="right")
        table.add_column("Skills", justify="right")
        table.add_column("Commands", justify="right")
        table.add_column("Description")
        for p in registry.list_plugins():
            if plugin_filter and plugin_filter not in p.name:
                continue
            table.add_row(
                p.name, p.version, str(p.agent_count), str(p.skill_count), str(p.command_count), p.description
            )
        console.print(table)

    if show_agents:
        table = Table(title="Agents")
        table.add_column("Name", style="cyan")
        table.add_column("Plugin", style="magenta")
        table.add_column("Model Tier")
        table.add_column("Description")
        for a in registry.list_agents():
            if plugin_filter and plugin_filter not in a.plugin:
                continue
            table.add_row(f"{a.plugin}__{a.name}", a.plugin, a.model_tier, a.description)
        console.print(table)

    if show_skills:
        table = Table(title="Skills")
        table.add_column("Name", style="cyan")
        table.add_column("Plugin", style="magenta")
        table.add_column("Description")
        for s in registry.list_skills():
            if plugin_filter and plugin_filter not in s.plugin:
                continue
            table.add_row(f"{s.plugin}__{s.name}", s.plugin, s.description)
        console.print(table)

    if show_commands:
        table = Table(title="Commands")
        table.add_column("Name", style="cyan")
        table.add_column("Plugin", style="magenta")
        table.add_column("Description")
        for c in registry.list_commands():
            if plugin_filter and plugin_filter not in c.plugin:
                continue
            table.add_row(f"{c.plugin}__{c.name}", c.plugin, c.description)
        console.print(table)


@app.command()
def stats() -> None:
    """Show MarOOn DEV marketplace statistics."""
    registry = _get_registry()
    s = registry.stats()
    table = Table(title="Marketplace Statistics")
    table.add_column("Entity", style="cyan")
    table.add_column("Count", justify="right", style="green")
    for key, val in s.items():
        table.add_row(key.capitalize(), str(val))
    console.print(table)


@app.command()
def invoke(
    plugin: str = typer.Option("", "--plugin", "-p", help="Plugin name to invoke"),
    agent: str = typer.Option("", "--agent", "-a", help="Agent name to invoke"),
    skill: str = typer.Option("", "--skill", "-s", help="Skill name to invoke"),
    cmd: str = typer.Option("", "--cmd", "-c", help="Command name to invoke"),
    harnesses: list[str] = typer.Option(ALL_HARNESSES, "--harness", "-h", help="Harnesses to target"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    context: str = typer.Option("", "--context", help="JSON context string"),
) -> None:
    """Invoke agent/skill/command/plugin across harnesses simultaneously."""
    registry = _get_registry()
    orchestrator = MultiHarnessOrchestrator(registry, harnesses=harnesses)

    ctx: dict[str, Any] = {}
    if context:
        try:
            ctx = json.loads(context)
        except json.JSONDecodeError as e:
            console.print(f"[red]Invalid JSON context: {e}[/red]")
            raise typer.Exit(1)

    if not any([plugin, agent, skill, cmd]):
        console.print("[red]At least one of --plugin, --agent, --skill, --cmd is required[/red]")
        raise typer.Exit(1)

    results = asyncio.run(
        orchestrator.call_all(
            plugin_name=plugin or None,
            agent_name=agent or None,
            skill_name=skill or None,
            command_name=cmd or None,
            context=ctx,
        )
    )

    if json_output:
        output = {}
        for key, res_list in results.items():
            output[key] = [
                {
                    "harness": r.harness,
                    "target": r.target_name,
                    "success": r.success,
                    "data": r.data,
                    "stderr": r.stderr,
                }
                for r in res_list
            ]
        console.print_json(json.dumps(output))
        return

    for key, res_list in results.items():
        table = Table(title=f"{key.capitalize()} Results")
        table.add_column("Harness", style="cyan")
        table.add_column("Target", style="magenta")
        table.add_column("Status")
        table.add_column("Data")
        for r in res_list:
            status = "[green]✓[/green]" if r.success else "[red]✗[/red]"
            data_str = json.dumps(r.data, indent=2, default=str) if r.data else ""
            if r.stderr:
                data_str = f"[red]{r.stderr}[/red]"
            table.add_row(r.harness, r.target_name, status, data_str)
        console.print(table)


@app.command()
def match(
    prompt: str = typer.Argument(..., help="Task/prompt to match against"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of matches to return"),
    project_aware: bool = typer.Option(True, "--project-aware/--no-project-aware", help="Consider project tech stack"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    agents_only: bool = typer.Option(False, "--agents-only", "-a", help="Only match agents"),
    skills_only: bool = typer.Option(False, "--skills-only", "-s", help="Only match skills"),
) -> None:
    """Find the best agents/skills for a given prompt (project-aware)."""
    registry = _get_registry()
    matcher = PromptMatcher(registry)

    include_agents = not skills_only
    include_skills = not agents_only

    if project_aware:
        results = matcher.match_project_aware(prompt, top_k=top_k)
    else:
        results = matcher.match(prompt, top_k=top_k, include_agents=include_agents, include_skills=include_skills)

    if json_output:
        output = [
            {
                "type": "agent" if isinstance(r.entity, Agent) else "skill",
                "name": f"{r.entity.plugin}__{r.entity.name}",
                "score": round(r.score, 2),
                "path": str(r.entity.path),
                "reason": r.reason,
            }
            for r in results
        ]
        console.print_json(json.dumps(output))
        return

    table = Table(title=f"Top Matches for: {prompt[:60]}...")
    table.add_column("Rank", justify="right", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Name")
    table.add_column("Score", justify="right", style="green")
    table.add_column("Reason")

    for i, r in enumerate(results, 1):
        entity_type = "agent" if isinstance(r.entity, Agent) else "skill"
        name = f"{r.entity.plugin}__{r.entity.name}"
        table.add_row(str(i), entity_type, name, f"{r.score:.1f}", r.reason)
    console.print(table)

    if results:
        console.print("\n[dim]Load any match into Kimi with:[/dim]")
        for r in results[:3]:
            console.print(f"  [yellow]@{r.entity.path}[/yellow]")


@app.command()
def load_project(
    prompt: str = typer.Argument("", help="Optional prompt describing what you want to do"),
    project_dir: Path = typer.Option(Path("."), "--dir", "-d", help="Project directory to analyze"),
    min_score: float = typer.Option(0.05, "--min-score", help="Minimum match score"),
    max_per_category: int = typer.Option(999, "--max", "-m", help="Max entities per category"),
    load_all: bool = typer.Option(True, "--load-all/--top-only", help="Load ALL matching agents/skills (default) or only top N"),
    output: Path = typer.Option(Path("kimi-context-bundle.md"), "--output", "-o", help="Output file"),
    no_tests: bool = typer.Option(False, "--no-tests", help="Skip testing skills"),
    no_security: bool = typer.Option(False, "--no-security", help="Skip security agents/skills"),
    no_infra: bool = typer.Option(False, "--no-infra", help="Skip infrastructure skills"),
    no_docs: bool = typer.Option(False, "--no-docs", help="Skip documentation skills"),
    stdout: bool = typer.Option(False, "--stdout", help="Print to stdout instead of file"),
) -> None:
    """Full A-to-Z orchestration: analyze project + load MAX agents/skills."""
    registry = _get_registry()
    orchestrator = FullProjectOrchestrator(registry, project_root=project_dir)

    console.print(f"[cyan]Analyzing project: {project_dir} ...[/cyan]")
    context = orchestrator.orchestrate(
        user_prompt=prompt,
        min_score=min_score,
        max_per_category=max_per_category,
        load_tests=not no_tests,
        load_security=not no_security,
        load_infra=not no_infra,
        load_docs=not no_docs,
        load_all_matching=load_all,
    )

    console.print(f"[green]✓ Analysis complete[/green]")
    console.print(f"  Agents loaded: {len(context.agents) + len(context.security_agents) + (1 if context.orchestrator_agent else 0)}")
    console.print(f"  Skills loaded: {len(context.skills) + len(context.test_skills) + len(context.infra_skills) + len(context.docs_skills)}")
    console.print(f"  Total: {context.total_loaded} entities")

    bundle = orchestrator.generate_context_bundle(context)

    if stdout:
        console.print(bundle)
    else:
        output.write_text(bundle, encoding="utf-8")
        console.print(f"[green]✓ Context bundle written to: {output}[/green]")
        console.print(f"[dim]Load it into Kimi with: @{output}[/dim]")


@app.command()
def sync(
    harnesses: list[str] = typer.Option(["all"], "--harness", "-h", help="Harnesses to regenerate"),
) -> None:
    """Regenerate harness artifacts."""
    import subprocess

    targets = harnesses
    if "all" in targets:
        targets = ["codex", "cursor", "opencode", "gemini", "copilot"]

    for h in targets:
        console.print(f"[cyan]Generating {h}...[/cyan]")
        result = subprocess.run(
            ["make", "generate", f"HARNESS={h}"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            console.print(f"[green]✓ {h} generated[/green]")
        else:
            console.print(f"[red]✗ {h} failed: {result.stderr}[/red]")


if __name__ == "__main__":
    app()
