"""Deep project analyzer for multi-agent orchestration."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ProjectProfile:
    """Complete profile of a project."""

    root: Path
    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    patterns: list[str] = field(default_factory=list)
    testing_setup: list[str] = field(default_factory=list)
    infra: list[str] = field(default_factory=list)
    security_concerns: list[str] = field(default_factory=list)
    file_counts: dict[str, int] = field(default_factory=dict)
    entry_points: list[str] = field(default_factory=list)
    config_files: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)

    def to_prompt(self) -> str:
        """Convert profile to an enriched prompt for the matcher."""
        parts = [
            f"Project uses {', '.join(self.languages)}" if self.languages else "",
            f"Frameworks: {', '.join(self.frameworks)}" if self.frameworks else "",
            f"Domains: {', '.join(self.domains)}" if self.domains else "",
            f"Patterns: {', '.join(self.patterns)}" if self.patterns else "",
            f"Testing: {', '.join(self.testing_setup)}" if self.testing_setup else "",
            f"Infrastructure: {', '.join(self.infra)}" if self.infra else "",
            f"Security: {', '.join(self.security_concerns)}" if self.security_concerns else "",
        ]
        return ". ".join(p for p in parts if p)


class ProjectAnalyzer:
    """Analyzes a project directory to extract its full tech profile."""

    LANGUAGE_PATTERNS: dict[str, list[str]] = {
        "python": ["*.py", "pyproject.toml", "requirements.txt", "setup.py", "Pipfile"],
        "javascript": ["*.js", "package.json"],
        "typescript": ["*.ts", "*.tsx", "tsconfig.json"],
        "go": ["*.go", "go.mod"],
        "rust": ["*.rs", "Cargo.toml"],
        "java": ["*.java", "pom.xml", "build.gradle"],
        "kotlin": ["*.kt", "*.kts"],
        "ruby": ["*.rb", "Gemfile"],
        "elixir": ["*.ex", "*.exs", "mix.exs"],
        "cpp": ["*.cpp", "*.hpp", "CMakeLists.txt"],
        "c": ["*.c", "*.h"],
        "shell": ["*.sh", "Makefile"],
    }

    FRAMEWORK_PATTERNS: dict[str, list[str]] = {
        "fastapi": ["fastapi", "main.py"],
        "django": ["django", "settings.py", "manage.py"],
        "flask": ["flask", "app.py"],
        "react": ["react", "next.config.js", "vite.config.ts"],
        "vue": ["vue", "nuxt.config.ts"],
        "angular": ["angular", "angular.json"],
        "express": ["express", "app.js"],
        "nestjs": ["nestjs", "@nestjs"],
        "spring": ["spring-boot", "application.properties"],
        "rails": ["rails", "config/routes.rb"],
        "laravel": ["laravel", "artisan"],
        "flutter": ["flutter", "pubspec.yaml"],
        "actix": ["actix-web"],
        "gin": ["gin-gonic"],
    }

    TEST_PATTERNS: dict[str, list[str]] = {
        "pytest": ["pytest.ini", "conftest.py", "test_*.py", "*_test.py"],
        "jest": ["jest.config.js", "*.test.js", "*.spec.js"],
        "vitest": ["vitest.config.ts", "*.test.ts"],
        "mocha": ["mocha", ".mocharc.js"],
        "unittest": ["unittest", "TestCase"],
        "go-test": ["*_test.go"],
        "rs-test": ["#[cfg(test)]"],
    }

    INFRA_PATTERNS: dict[str, list[str]] = {
        "docker": ["Dockerfile", "docker-compose.yml", ".dockerignore"],
        "kubernetes": ["k8s/", "manifests/", "helm/", "*.yaml"],
        "terraform": ["*.tf", "main.tf"],
        "github-actions": [".github/workflows/"],
        "gitlab-ci": [".gitlab-ci.yml"],
        "ansible": ["ansible/", "*.yml"],
        "aws": ["serverless.yml", "samconfig.toml"],
    }

    SECURITY_FILES: dict[str, list[str]] = {
        "auth": ["auth", "login", "jwt", "oauth", "password", "session"],
        "api-security": ["api-key", "rate-limit", "cors", "csrf", "xss"],
        "secrets": [".env", "secrets", "vault", "kms"],
        "compliance": ["gdpr", "hipaa", "pci", "soc2"],
    }

    def __init__(self, root: Path | str = ".") -> None:
        self.root = Path(root).resolve()

    def analyze(self) -> ProjectProfile:
        """Run full project analysis."""
        profile = ProjectProfile(root=self.root)

        # Count files by extension
        profile.file_counts = self._count_files()

        # Detect languages
        profile.languages = self._detect_languages()

        # Detect frameworks
        profile.frameworks = self._detect_frameworks()

        # Detect patterns
        profile.patterns = self._detect_patterns()

        # Detect testing setup
        profile.testing_setup = self._detect_testing()

        # Detect infrastructure
        profile.infra = self._detect_infra()

        # Detect security concerns
        profile.security_concerns = self._detect_security()

        # Find entry points
        profile.entry_points = self._find_entry_points()

        # Find config files
        profile.config_files = self._find_configs()

        # Extract dependencies
        profile.dependencies = self._extract_dependencies()

        # Infer domains
        profile.domains = self._infer_domains(profile)

        return profile

    def _count_files(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for ext in [".py", ".js", ".ts", ".tsx", ".go", ".rs", ".java", ".kt", ".rb", ".ex", ".cpp", ".c"]:
            counts[ext] = len(list(self.root.rglob(f"*{ext}")))
        return {k: v for k, v in counts.items() if v > 0}

    def _detect_languages(self) -> list[str]:
        found = []
        for lang, patterns in self.LANGUAGE_PATTERNS.items():
            for pattern in patterns:
                if "*" in pattern:
                    if any(self.root.rglob(pattern)):
                        found.append(lang)
                        break
                else:
                    if (self.root / pattern).exists() or any(self.root.rglob(pattern)):
                        found.append(lang)
                        break
        return found

    def _detect_frameworks(self) -> list[str]:
        found = []
        for framework, signals in self.FRAMEWORK_PATTERNS.items():
            for signal in signals:
                if "/" in signal or signal.endswith(".py") or signal.endswith(".js") or signal.endswith(".ts"):
                    if any(self.root.rglob(signal)):
                        found.append(framework)
                        break
                else:
                    # Check in dependency files
                    deps = self._read_dependency_files()
                    if signal.lower() in deps.lower():
                        found.append(framework)
                        break
        return list(dict.fromkeys(found))  # dedup preserve order

    def _detect_patterns(self) -> list[str]:
        patterns = []
        # Check for common architecture patterns
        if (self.root / "src" / "domain").exists() or (self.root / "domain").exists():
            patterns.append("domain-driven-design")
        if (self.root / "src" / "usecases").exists() or (self.root / "use_cases").exists():
            patterns.append("clean-architecture")
        if any(self.root.rglob("*repository*")):
            patterns.append("repository-pattern")
        if any(self.root.rglob("*controller*")):
            patterns.append("mvc")
        if any(self.root.rglob("*handler*")):
            patterns.append("event-driven")
        if (self.root / "microservices").exists() or (self.root / "services").exists():
            patterns.append("microservices")
        if any(self.root.rglob("*grpc*")):
            patterns.append("grpc")
        if any(self.root.rglob("*graphql*")) or any(self.root.rglob("*gql*")):
            patterns.append("graphql")
        return patterns

    def _detect_testing(self) -> list[str]:
        found = []
        for test_framework, signals in self.TEST_PATTERNS.items():
            for signal in signals:
                if "*" in signal:
                    if any(self.root.rglob(signal)):
                        found.append(test_framework)
                        break
                else:
                    if any(self.root.rglob(signal)) or (self.root / signal).exists():
                        found.append(test_framework)
                        break
        return found

    def _detect_infra(self) -> list[str]:
        found = []
        for infra, signals in self.INFRA_PATTERNS.items():
            for signal in signals:
                if signal.endswith("/"):
                    if (self.root / signal).exists():
                        found.append(infra)
                        break
                elif "*" in signal:
                    if any(self.root.rglob(signal)):
                        found.append(infra)
                        break
                else:
                    if (self.root / signal).exists() or any(self.root.rglob(signal)):
                        found.append(infra)
                        break
        return found

    def _detect_security(self) -> list[str]:
        found = []
        # Read key source files for security keywords
        all_code = ""
        for f in self.root.rglob("*.py"):
            if f.stat().st_size < 100_000:
                try:
                    all_code += f.read_text(encoding="utf-8", errors="ignore")[:5000]
                except Exception:
                    pass
            if len(all_code) > 50_000:
                break

        for concern, keywords in self.SECURITY_FILES.items():
            for kw in keywords:
                if kw in all_code.lower() or any(self.root.rglob(f"*{kw}*")):
                    found.append(concern)
                    break
        return found

    def _find_entry_points(self) -> list[str]:
        entries = []
        common = ["main.py", "app.py", "index.js", "server.js", "main.go", "src/main.rs", "Application.java"]
        for c in common:
            matches = list(self.root.rglob(c))
            for m in matches:
                entries.append(str(m.relative_to(self.root)))
        return entries[:10]

    def _find_configs(self) -> list[str]:
        configs = []
        for c in ["pyproject.toml", "package.json", "tsconfig.json", "go.mod", "Cargo.toml", "docker-compose.yml", ".env.example"]:
            if (self.root / c).exists():
                configs.append(c)
        return configs

    def _read_dependency_files(self) -> str:
        text = ""
        for dep_file in ["pyproject.toml", "requirements.txt", "package.json", "go.mod", "Cargo.toml"]:
            path = self.root / dep_file
            if path.exists():
                try:
                    text += path.read_text(encoding="utf-8", errors="ignore")[:10000]
                except Exception:
                    pass
        return text

    def _extract_dependencies(self) -> list[str]:
        deps = []
        text = self._read_dependency_files()
        # Simple extraction of quoted package names
        quoted = re.findall(r'"([^"]+)"', text)
        deps.extend([q for q in quoted if len(q) > 2 and not q.startswith("http")])
        return list(dict.fromkeys(deps))[:30]

    def _infer_domains(self, profile: ProjectProfile) -> list[str]:
        domains = []
        if "python" in profile.languages and "fastapi" in profile.frameworks:
            domains.extend(["backend-api", "async-python"])
        if "docker" in profile.infra or "kubernetes" in profile.infra:
            domains.append("devops")
        if "pytest" in profile.testing_setup or any("test" in t for t in profile.testing_setup):
            domains.append("testing")
        if profile.security_concerns:
            domains.append("security")
        if "react" in profile.frameworks or "vue" in profile.frameworks:
            domains.append("frontend")
        if "ml" in str(profile.dependencies).lower() or any(x in str(profile.dependencies).lower() for x in ["torch", "tensorflow", "sklearn", "pandas"]):
            domains.append("machine-learning")
        if "blockchain" in str(profile.dependencies).lower() or "web3" in str(profile.dependencies).lower():
            domains.append("blockchain")
        if "django" in profile.frameworks:
            domains.append("full-stack-web")
        return list(dict.fromkeys(domains))

    def generate_markdown_report(self) -> str:
        """Generate a human-readable analysis report."""
        profile = self.analyze()
        lines = [
            "# Project Analysis Report",
            "",
            f"**Root:** `{profile.root}`",
            "",
            "## Languages",
            ", ".join(profile.languages) or "Not detected",
            "",
            "## Frameworks",
            ", ".join(profile.frameworks) or "Not detected",
            "",
            "## Architecture Patterns",
            ", ".join(profile.patterns) or "Not detected",
            "",
            "## Testing Setup",
            ", ".join(profile.testing_setup) or "Not detected",
            "",
            "## Infrastructure",
            ", ".join(profile.infra) or "Not detected",
            "",
            "## Security Concerns",
            ", ".join(profile.security_concerns) or "None detected",
            "",
            "## Domains",
            ", ".join(profile.domains) or "General",
            "",
            "## File Counts",
        ]
        for ext, count in profile.file_counts.items():
            lines.append(f"- `{ext}`: {count}")
        lines.extend([
            "",
            "## Entry Points",
        ])
        for ep in profile.entry_points:
            lines.append(f"- `{ep}`")
        lines.extend([
            "",
            "## Config Files",
        ])
        for cf in profile.config_files:
            lines.append(f"- `{cf}`")
        lines.extend([
            "",
            "## Key Dependencies",
            ", ".join(profile.dependencies[:20]) or "Not extracted",
        ])
        return "\n".join(lines)
