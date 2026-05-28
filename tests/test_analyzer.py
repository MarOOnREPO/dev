"""Tests for project analyzer."""

from pathlib import Path

from marketplace.core.analyzer import ProjectAnalyzer


def test_analyzer_detects_python() -> None:
    # The current project is a Python project
    analyzer = ProjectAnalyzer(".")
    profile = analyzer.analyze()
    assert "python" in profile.languages


def test_analyzer_detects_pytest() -> None:
    analyzer = ProjectAnalyzer(".")
    profile = analyzer.analyze()
    assert "pytest" in profile.testing_setup


def test_analyzer_generates_prompt() -> None:
    analyzer = ProjectAnalyzer(".")
    profile = analyzer.analyze()
    prompt = profile.to_prompt()
    assert "python" in prompt.lower()


def test_analyzer_generates_markdown() -> None:
    analyzer = ProjectAnalyzer(".")
    report = analyzer.generate_markdown_report()
    assert "# Project Analysis Report" in report
    assert "Languages" in report
