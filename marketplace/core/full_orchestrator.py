"""Full-project orchestrator — loads MAXIMUM relevant agents + skills from A to Z."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from marketplace.core.analyzer import ProjectAnalyzer
from marketplace.core.discovery import Registry, discover
from marketplace.core.matcher import MatchResult, PromptMatcher
from marketplace.core.models import Agent, Skill


@dataclass
class LoadedContext:
    """Complete loaded context for a project."""

    project_root: Path
    profile: Any  # ProjectProfile
    agents: list[MatchResult] = field(default_factory=list)
    skills: list[MatchResult] = field(default_factory=list)
    test_skills: list[MatchResult] = field(default_factory=list)
    security_agents: list[MatchResult] = field(default_factory=list)
    infra_skills: list[MatchResult] = field(default_factory=list)
    docs_skills: list[MatchResult] = field(default_factory=list)
    orchestrator_agent: MatchResult | None = None

    @property
    def total_loaded(self) -> int:
        return (
            len(self.agents)
            + len(self.skills)
            + len(self.test_skills)
            + len(self.security_agents)
            + len(self.infra_skills)
            + len(self.docs_skills)
            + (1 if self.orchestrator_agent else 0)
        )

    @property
    def all_entities(self) -> list[MatchResult]:
        """Return all loaded entities as a flat list."""
        all_results: list[MatchResult] = []
        all_results.extend(self.agents)
        all_results.extend(self.skills)
        all_results.extend(self.test_skills)
        all_results.extend(self.security_agents)
        all_results.extend(self.infra_skills)
        all_results.extend(self.docs_skills)
        if self.orchestrator_agent:
            all_results.append(self.orchestrator_agent)
        # Sort by score descending
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results


class FullProjectOrchestrator:
    """Orchestrator that loads the MAXIMUM relevant context for a project."""

    def __init__(self, registry: Registry | None = None, project_root: Path = Path(".")) -> None:
        self.registry = registry or discover("plugins")
        self.matcher = PromptMatcher(self.registry)
        self.analyzer = ProjectAnalyzer(project_root)
        self.project_root = project_root

    def orchestrate(
        self,
        user_prompt: str = "",
        min_score: float = 0.05,
        max_per_category: int = 999,
        load_tests: bool = True,
        load_security: bool = True,
        load_infra: bool = True,
        load_docs: bool = True,
        load_orchestrator: bool = True,
        load_all_matching: bool = True,
    ) -> LoadedContext:
        """
        Full A-to-Z orchestration:
        1. Analyze project structure
        2. Match ALL relevant agents (not just top 5)
        3. Match ALL relevant skills by domain
        4. Add specialized skills (testing, security, infra, docs)
        5. Add an orchestrator agent if needed
        """
        profile = self.analyzer.analyze()
        context = LoadedContext(project_root=self.project_root, profile=profile)

        # Build enriched prompt from user input + project analysis
        enriched = f"{user_prompt}. {profile.to_prompt()}"

        # 1. Match ALL agents above threshold (use top_k=500 for MAX coverage)
        all_agent_matches = self.matcher.match(
            enriched,
            top_k=500,
            min_score=min_score,
            include_agents=True,
            include_skills=False,
        )
        context.agents = all_agent_matches[:max_per_category] if not load_all_matching else all_agent_matches

        # 2. Match ALL skills above threshold (use top_k=500 for MAX coverage)
        all_skill_matches = self.matcher.match(
            enriched,
            top_k=500,
            min_score=min_score,
            include_agents=False,
            include_skills=True,
        )
        context.skills = all_skill_matches[:max_per_category] if not load_all_matching else all_skill_matches

        # 3. Load testing skills if requested
        if load_tests and (profile.testing_setup or "test" in user_prompt.lower()):
            test_matches = self.matcher.match(
                f"testing tdd unit test coverage pytest jest {enriched}",
                top_k=max_per_category,
                min_score=min_score - 0.2,  # slightly lower threshold
                include_agents=False,
                include_skills=True,
            )
            context.test_skills = [m for m in test_matches if m not in context.skills][:5]

        # 4. Load security agents/skills if needed
        if load_security and (profile.security_concerns or any(w in user_prompt.lower() for w in ["security", "auth", "safe", "protect"])):
            sec_matches = self.matcher.match(
                f"security authentication authorization jwt oauth vulnerability scan audit {enriched}",
                top_k=max_per_category,
                min_score=min_score - 0.2,
                include_agents=True,
                include_skills=True,
            )
            context.security_agents = [m for m in sec_matches if isinstance(m.entity, Agent)][:3]
            # Add security skills to main skills if not already there
            sec_skills = [m for m in sec_matches if isinstance(m.entity, Skill) and m not in context.skills][:3]
            context.skills.extend(sec_skills)

        # 5. Load infrastructure skills
        if load_infra and profile.infra:
            infra_matches = self.matcher.match(
                f"docker kubernetes terraform cicd deployment devops {enriched}",
                top_k=max_per_category,
                min_score=min_score - 0.2,
                include_agents=False,
                include_skills=True,
            )
            context.infra_skills = [m for m in infra_matches if m not in context.skills][:5]

        # 6. Load documentation skills
        if load_docs and any(w in user_prompt.lower() for w in ["doc", "readme", "adr", "explain"]):
            docs_matches = self.matcher.match(
                f"documentation readme adr markdown docstring {enriched}",
                top_k=max_per_category,
                min_score=min_score - 0.3,
                include_agents=False,
                include_skills=True,
            )
            context.docs_skills = [m for m in docs_matches if m not in context.skills][:3]

        # 7. Add orchestrator agent for complex multi-domain projects
        if load_orchestrator and len(profile.domains) > 1:
            orch_matches = self.matcher.match(
                "full-stack orchestration multi-agent coordination architecture",
                top_k=5,
                min_score=0.1,
                include_agents=True,
                include_skills=False,
            )
            if orch_matches:
                context.orchestrator_agent = orch_matches[0]

        return context

    def generate_context_bundle(self, context: LoadedContext) -> str:
        """Generate a massive context bundle with ALL loaded entities."""
        lines = [
            "=" * 80,
            "# FULL PROJECT CONTEXT BUNDLE — Multi-Harness Marketplace",
            "=" * 80,
            f"# Project: {context.project_root}",
            f"# Total entities loaded: {context.total_loaded}",
            f"# Agents: {len(context.agents) + len(context.security_agents) + (1 if context.orchestrator_agent else 0)}",
            f"# Skills: {len(context.skills) + len(context.test_skills) + len(context.infra_skills) + len(context.docs_skills)}",
            "=" * 80,
            "",
            "## PROJECT ANALYSIS",
            "",
        ]

        profile = context.profile
        lines.extend([
            f"- **Languages:** {', '.join(profile.languages) or 'N/A'}",
            f"- **Frameworks:** {', '.join(profile.frameworks) or 'N/A'}",
            f"- **Patterns:** {', '.join(profile.patterns) or 'N/A'}",
            f"- **Testing:** {', '.join(profile.testing_setup) or 'N/A'}",
            f"- **Infrastructure:** {', '.join(profile.infra) or 'N/A'}",
            f"- **Security:** {', '.join(profile.security_concerns) or 'N/A'}",
            f"- **Domains:** {', '.join(profile.domains) or 'General'}",
            "",
        ])

        # Orchestrator first
        if context.orchestrator_agent:
            lines.extend(self._render_entity(context.orchestrator_agent, "ORCHESTRATOR AGENT"))

        # Core agents
        if context.agents:
            lines.append(f"\n{'='*80}")
            lines.append(f"# CORE AGENTS ({len(context.agents)})")
            lines.append(f"{'='*80}\n")
            for r in context.agents:
                lines.extend(self._render_entity(r, "AGENT"))

        # Security agents
        if context.security_agents:
            lines.append(f"\n{'='*80}")
            lines.append(f"# SECURITY AGENTS ({len(context.security_agents)})")
            lines.append(f"{'='*80}\n")
            for r in context.security_agents:
                lines.extend(self._render_entity(r, "SECURITY AGENT"))

        # Core skills
        if context.skills:
            lines.append(f"\n{'='*80}")
            lines.append(f"# CORE SKILLS ({len(context.skills)})")
            lines.append(f"{'='*80}\n")
            for r in context.skills:
                lines.extend(self._render_entity(r, "SKILL"))

        # Test skills
        if context.test_skills:
            lines.append(f"\n{'='*80}")
            lines.append(f"# TESTING SKILLS ({len(context.test_skills)})")
            lines.append(f"{'='*80}\n")
            for r in context.test_skills:
                lines.extend(self._render_entity(r, "TEST SKILL"))

        # Infra skills
        if context.infra_skills:
            lines.append(f"\n{'='*80}")
            lines.append(f"# INFRASTRUCTURE SKILLS ({len(context.infra_skills)})")
            lines.append(f"{'='*80}\n")
            for r in context.infra_skills:
                lines.extend(self._render_entity(r, "INFRA SKILL"))

        # Docs skills
        if context.docs_skills:
            lines.append(f"\n{'='*80}")
            lines.append(f"# DOCUMENTATION SKILLS ({len(context.docs_skills)})")
            lines.append(f"{'='*80}\n")
            for r in context.docs_skills:
                lines.extend(self._render_entity(r, "DOCS SKILL"))

        lines.extend([
            f"\n{'='*80}",
            "# END OF FULL CONTEXT BUNDLE",
            f"{'='*80}",
            "",
            "## INSTRUCTIONS FOR KIMI",
            "",
            "You have been loaded with the MAXIMUM relevant agents and skills for this project.",
            "",
            "1. **Adopt the persona** of the highest-scoring agent(s) for your response.",
            "2. **Apply ALL relevant skills** in your answer — cross-reference patterns from multiple skills.",
            "3. **If an orchestrator is present**, coordinate between multiple agent perspectives.",
            "4. **Always include**: testing strategy, security considerations, and infrastructure awareness.",
            "5. **Structure your response** with clear sections matching the skill categories above.",
            "",
        ])

        return "\n".join(lines)

    def _render_entity(self, result: MatchResult, label: str) -> list[str]:
        entity = result.entity
        lines = [
            f"\n{'-'*60}",
            f"## {label}: {entity.plugin}__{entity.name}",
            f"- **Score:** {result.score:.1f}",
            f"- **Reason:** {result.reason}",
            f"- **Path:** {entity.path}",
            f"{'-'*60}",
            "",
        ]
        try:
            content = entity.path.read_text(encoding="utf-8")
            lines.append(content)
        except Exception as e:
            lines.append(f"[Error reading file: {e}]")
        lines.append("")
        return lines
