"""Tests for skills/productivity/cloud-red-team-playbook/SKILL.md — frontmatter and structure."""

import re
from pathlib import Path

import pytest
import yaml

SKILL_PATH = Path(__file__).resolve().parents[2] / "skills" / "productivity" / "cloud-red-team-playbook" / "SKILL.md"
PLAYBOOK_PATH = Path(__file__).resolve().parents[2] / "cloud_red_team_playbook.py"


def _parse_frontmatter(content: str) -> dict:
    assert content.startswith("---"), "SKILL.md must start with ---"
    m = re.search(r"\n---\s*\n", content[3:])
    assert m, "SKILL.md must close frontmatter with ---"
    return yaml.safe_load(content[3 : m.start() + 3])


class TestFrontmatter:
    def test_file_exists(self):
        assert SKILL_PATH.exists(), f"SKILL.md not found at {SKILL_PATH}"

    def test_required_fields_present(self):
        fm = _parse_frontmatter(SKILL_PATH.read_text())
        for field in ("name", "description", "version", "author", "license", "platforms", "metadata"):
            assert field in fm, f"Missing required field: {field}"

    def test_description_length(self):
        fm = _parse_frontmatter(SKILL_PATH.read_text())
        assert len(fm["description"]) <= 60, f"description is {len(fm['description'])} chars (max 60)"

    def test_description_ends_with_period(self):
        fm = _parse_frontmatter(SKILL_PATH.read_text())
        assert fm["description"].endswith("."), "description must end with a period"

    def test_metadata_hermes_fields(self):
        fm = _parse_frontmatter(SKILL_PATH.read_text())
        hermes = fm["metadata"]["hermes"]
        assert "tags" in hermes, "metadata.hermes.tags required"
        assert "related_skills" in hermes, "metadata.hermes.related_skills required"
        assert isinstance(hermes["tags"], list)
        assert isinstance(hermes["related_skills"], list)

    def test_platforms_is_list(self):
        fm = _parse_frontmatter(SKILL_PATH.read_text())
        assert isinstance(fm["platforms"], list)
        assert len(fm["platforms"]) >= 1

    def test_no_localhost_paths(self):
        content = SKILL_PATH.read_text()
        assert "C:\\Users" not in content, "SKILL.md must not contain machine-local paths"
        assert "/home/" not in content, "SKILL.md must not contain machine-local paths"


class TestBodyStructure:
    def test_required_sections_present(self):
        content = SKILL_PATH.read_text()
        for section in ("## When to Use", "## Prerequisites", "## How to Run", "## Quick Reference", "## Procedure", "## Pitfalls", "## Verification"):
            assert section in content, f"Missing section: {section}"

    def test_section_order(self):
        content = SKILL_PATH.read_text()
        sections = ["## When to Use", "## Prerequisites", "## How to Run", "## Quick Reference", "## Procedure", "## Pitfalls", "## Verification"]
        positions = [content.index(s) for s in sections]
        assert positions == sorted(positions), "Sections must appear in standard order"

    def test_hermes_tools_referenced(self):
        content = SKILL_PATH.read_text()
        for tool in ("terminal", "search_files", "read_file"):
            assert f"`{tool}`" in content, f"Skill should reference `{tool}`"

    def test_no_shell_wrappers(self):
        content = SKILL_PATH.read_text()
        assert "`grep`" not in content, "Use search_files, not grep"
        assert "`cat " not in content, "Use read_file, not cat"


class TestPlaybookGenerator:
    def test_playbook_exists(self):
        assert PLAYBOOK_PATH.exists(), f"cloud_red_team_playbook.py not found at {PLAYBOOK_PATH}"

    def test_playbook_imports(self):
        spec = __import__("importlib.util").util.spec_from_file_location("cloud_red_team_playbook", PLAYBOOK_PATH)
        mod = __import__("importlib.util").util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, "build_scenarios"), "Module must define build_scenarios"
        assert hasattr(mod, "generate_markdown_report"), "Module must define generate_markdown_report"
        assert hasattr(mod, "generate_json_report"), "Module must define generate_json_report"

    def test_five_scenarios(self):
        spec = __import__("importlib.util").util.spec_from_file_location("cloud_red_team_playbook", PLAYBOOK_PATH)
        mod = __import__("importlib.util").util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        scenarios = mod.build_scenarios()
        assert len(scenarios) == 5, f"Expected 5 scenarios, got {len(scenarios)}"
        ids = [s.scenario_id for s in scenarios]
        assert ids == ["AWS-001", "AWS-002", "AWS-003", "AWS-004", "AWS-005"]

    def test_eleven_detection_rules(self):
        spec = __import__("importlib.util").util.spec_from_file_location("cloud_red_team_playbook", PLAYBOOK_PATH)
        mod = __import__("importlib.util").util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        scenarios = mod.build_scenarios()
        total_rules = sum(len(r) for s in scenarios for step in s.steps for r in [step.detection_rules])
        assert total_rules == 11, f"Expected 11 detection rules, got {total_rules}"

    def test_markdown_report_generation(self):
        spec = __import__("importlib.util").util.spec_from_file_location("cloud_red_team_playbook", PLAYBOOK_PATH)
        mod = __import__("importlib.util").util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        scenarios = mod.build_scenarios()
        report = mod.generate_markdown_report(scenarios)
        assert "# Cloud Red Team Playbook" in report
        assert "AWS-001" in report
        assert "AWS-005" in report
        assert "DET-AWS-001a" in report
        assert "DET-AWS-005b" in report

    def test_json_report_generation(self):
        spec = __import__("importlib.util").util.spec_from_file_location("cloud_red_team_playbook", PLAYBOOK_PATH)
        mod = __import__("importlib.util").util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        scenarios = mod.build_scenarios()
        report = mod.generate_json_report(scenarios)
        import json
        data = json.loads(report)
        assert data["metadata"]["scenario_count"] == 5
        assert len(data["scenarios"]) == 5
