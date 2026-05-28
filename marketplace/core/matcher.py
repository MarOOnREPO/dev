"""Prompt-to-agent/skill matcher for auto-loading relevant marketplace entities."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from marketplace.core.discovery import Registry, discover
from marketplace.core.models import Agent, Skill


@dataclass
class MatchResult:
    """A scored match result."""

    entity: Agent | Skill
    score: float
    matched_terms: list[str]
    reason: str


class PromptMatcher:
    """Matches user prompts to the most relevant agents and skills."""

    # Technology stack keywords that boost relevance
    TECH_KEYWORDS: dict[str, list[str]] = {
        "python": ["python", "django", "fastapi", "flask", "pytest", "uv", "poetry", "asyncio"],
        "javascript": ["javascript", "typescript", "react", "vue", "angular", "node", "nextjs", "nestjs"],
        "java": ["java", "spring", "jvm", "kotlin", "gradle", "maven"],
        "go": ["go", "golang", "gin"],
        "rust": ["rust", "cargo", "actix"],
        "devops": ["docker", "kubernetes", "k8s", "terraform", "ansible", "cicd", "github actions"],
        "ml": ["machine learning", "ml", "pytorch", "tensorflow", "llm", "ai", "model"],
        "security": ["security", "auth", "oauth", "jwt", "penetration", "vulnerability", "scan"],
        "database": ["sql", "postgresql", "mysql", "mongodb", "redis", "database", "migration"],
        "frontend": ["html", "css", "tailwind", "ui", "ux", "component", "design system"],
        "backend": ["api", "rest", "graphql", "microservice", "server"],
        "mobile": ["ios", "android", "flutter", "react native", "swift", "kotlin"],
        "blockchain": ["web3", "solidity", "ethereum", "smart contract", "defi"],
        "testing": ["test", "testing", "tdd", "coverage", "mock", "e2e", "integration test"],
        "docs": ["documentation", "readme", "docstring", "markdown", "adr"],
    }

    def __init__(self, registry: Registry | None = None) -> None:
        self.registry = registry or discover("plugins")
        self._index: dict[str, dict[str, Any]] = {}
        self._build_index()

    def _build_index(self) -> None:
        """Build a searchable index of all agents and skills."""
        for agent in self.registry.list_agents():
            text = f"{agent.name} {agent.plugin} {agent.description} {agent.model_tier}"
            self._index[f"agent:{agent.plugin}__{agent.name}"] = {
                "entity": agent,
                "text": text.lower(),
                "type": "agent",
            }
        for skill in self.registry.list_skills():
            text = f"{skill.name} {skill.plugin} {skill.description}"
            # Also read first few lines of skill content for richer matching
            try:
                if skill.path.exists():
                    content = skill.path.read_text(encoding="utf-8")
                    # Extract body after frontmatter
                    if "---" in content:
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            body = parts[2]
                            # Take first 500 chars of body as additional context
                            text += " " + body[:500].lower()
            except Exception:
                pass
            self._index[f"skill:{skill.plugin}__{skill.name}"] = {
                "entity": skill,
                "text": text.lower(),
                "type": "skill",
            }

    def _tokenize(self, text: str) -> list[str]:
        """Extract meaningful tokens from text."""
        # Keep multi-word tech terms together, normalize
        text = text.lower()
        # Replace common separators
        text = re.sub(r"[-_/]", " ", text)
        # Extract words and short phrases
        tokens = re.findall(r"\b[a-z][a-z0-9]+\b", text)
        # Also extract 2-word phrases
        words = text.split()
        phrases = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
        return tokens + phrases

    def _detect_tech_stack(self, prompt: str) -> list[str]:
        """Detect which tech domains are mentioned in the prompt."""
        prompt_lower = prompt.lower()
        detected = []
        for domain, keywords in self.TECH_KEYWORDS.items():
            for kw in keywords:
                if kw in prompt_lower:
                    detected.append(domain)
                    break
        return detected

    def match(
        self,
        prompt: str,
        top_k: int = 5,
        min_score: float = 0.1,
        include_agents: bool = True,
        include_skills: bool = True,
    ) -> list[MatchResult]:
        """Find the best matching agents and skills for a prompt."""
        prompt_tokens = self._tokenize(prompt)
        prompt_lower = prompt.lower()
        detected_tech = self._detect_tech_stack(prompt)

        results: list[MatchResult] = []

        for key, entry in self._index.items():
            entity_type = entry["type"]
            if entity_type == "agent" and not include_agents:
                continue
            if entity_type == "skill" and not include_skills:
                continue

            entity = entry["entity"]
            text = entry["text"]

            score = 0.0
            matched = []

            # Exact name match (high weight)
            name_lower = entity.name.lower().replace("-", " ")
            if name_lower in prompt_lower:
                score += 3.0
                matched.append(entity.name)

            # Plugin name match
            plugin_lower = entity.plugin.lower().replace("-", " ")
            if plugin_lower in prompt_lower:
                score += 2.0
                matched.append(entity.plugin)

            # Token overlap
            for token in prompt_tokens:
                if len(token) < 3:
                    continue
                if token in text:
                    score += 0.5
                    if token not in matched:
                        matched.append(token)

            # Tech stack boost
            for tech in detected_tech:
                tech_kws = self.TECH_KEYWORDS.get(tech, [])
                for kw in tech_kws:
                    if kw in text:
                        score += 0.8
                        if tech not in matched:
                            matched.append(tech)
                        break

            # Agent model tier boost for architecture/security prompts
            if entity_type == "agent" and isinstance(entity, Agent):
                if any(w in prompt_lower for w in ["architecture", "design", "security", "review", "audit"]):
                    if entity.model_tier in ("opus", "tier-1"):
                        score += 0.5

            if score >= min_score:
                reason = self._generate_reason(entity, matched, detected_tech)
                results.append(MatchResult(entity, score, matched, reason))

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def _generate_reason(self, entity: Agent | Skill, matched: list[str], detected_tech: list[str]) -> str:
        """Generate a human-readable reason for the match."""
        parts = []
        if isinstance(entity, Agent):
            parts.append(f"Agent '{entity.name}'")
            if entity.model_tier != "inherit":
                parts.append(f"({entity.model_tier} tier)")
        else:
            parts.append(f"Skill '{entity.name}'")
        parts.append(f"from plugin '{entity.plugin}'")

        if matched:
            top_matches = [m for m in matched[:3] if len(m) > 2]
            if top_matches:
                parts.append(f"— matched on: {', '.join(top_matches)}")

        return " ".join(parts)

    def match_project_aware(
        self,
        prompt: str,
        project_root: Path = Path("."),
        top_k: int = 5,
    ) -> list[MatchResult]:
        """Match with awareness of the project's tech stack."""
        # Detect project tech stack from files
        project_tech = self._detect_project_tech(project_root)
        enriched_prompt = prompt + " " + " ".join(project_tech)
        return self.match(enriched_prompt, top_k=top_k)

    def _detect_project_tech(self, project_root: Path) -> list[str]:
        """Detect project technologies from file presence."""
        tech_signals: dict[str, list[str]] = {
            "python": ["pyproject.toml", "requirements.txt", "setup.py", "Pipfile"],
            "javascript": ["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"],
            "typescript": ["tsconfig.json"],
            "go": ["go.mod", "go.sum"],
            "rust": ["Cargo.toml", "Cargo.lock"],
            "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
            "docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
            "kubernetes": ["k8s/", "manifests/", "helm/"],
            "terraform": [".tf", "main.tf", "variables.tf"],
        }

        detected = []
        for tech, signals in tech_signals.items():
            for signal in signals:
                if signal.endswith("/"):
                    if (project_root / signal).exists():
                        detected.append(tech)
                        break
                else:
                    if (project_root / signal).exists():
                        detected.append(tech)
                        break
        return detected


def find_matches(
    prompt: str,
    top_k: int = 5,
    project_root: Path = Path("."),
    project_aware: bool = True,
) -> list[MatchResult]:
    """Convenience function: find matches for a prompt."""
    matcher = PromptMatcher()
    if project_aware:
        return matcher.match_project_aware(prompt, project_root, top_k)
    return matcher.match(prompt, top_k)
