#!/usr/bin/env python3
import json
import sys
from pathlib import Path

results = []

def test(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
        print(f"  PASS: {name}")
    except Exception as e:
        results.append((name, "FAIL", str(e)))
        print(f"  FAIL: {name}: {e}")

print("=" * 60)
print("  BIONIC DAUGHTER - TOOL TEST SUITE")
print("=" * 60)

# 1
print("\n--- Data Quality ---")
def t1():
    sys.path.insert(0, ".")
    from training_data_quality_pipeline import TrainingDataQualityPipeline
    p = TrainingDataQualityPipeline("grpo_train_augmented.jsonl")
    p.validate()
    r = p.generate_report()
    assert r["stats"]["total"] > 0
    assert r["pass_rate"] >= 95.0
test("Data Quality", t1)

# 2
print("\n--- Persona ---")
def t2():
    from persona_consistency_checker import PersonaConsistencyChecker
    c = PersonaConsistencyChecker()
    r = c.generate_report()
    assert r["total_tests"] == 7
test("Persona", t2)

# 3
print("\n--- Knowledge Graph ---")
def t3():
    from attack_technique_knowledge_graph import KnowledgeGraph
    kg = KnowledgeGraph("test")
    kg.load_default_edges()
    assert len(kg.techniques) >= 10
test("Knowledge Graph", t3)

# 4
print("\n--- CVSS ---")
def t4():
    from automated_bounty_submission import calculate_cvss
    r = calculate_cvss(vector="N", ac="L", pr="N", ui="N", s="U", c="H", i="H", a="H")
    assert r["score"] == 9.8
test("CVSS", t4)

# 5
print("\n--- Reporting ---")
def t5():
    from automated_reporting_system import ReportGenerator
    g = ReportGenerator("test_reports")
    g.add_finding(title="SQLi", description="SQLi", severity="Critical", cvss_score=9.8, affected="ex.com", remediation="Patch")
    g.generate_markdown("test.md")
    assert Path("test_reports/test.md").exists()
test("Reporting", t5)

# 6
print("\n--- Threat Modeling ---")
def t6():
    from threat_modeling_engine import ThreatModelingEngine
    e = ThreatModelingEngine()
    m = e.generate("App", ["web", "api"])
    assert len(m["components"]) == 2
test("Threat Modeling", t6)

# 7
print("\n--- Exploit Recs ---")
def t7():
    from exploit_recommendation_engine import ExploitRecommendationEngine
    e = ExploitRecommendationEngine()
    r = e.recommend("SQL Injection")
    assert len(r["exploits"]) >= 3
test("Exploit Recs", t7)

# 8
print("\n--- Augmented Data ---")
def t8():
    total = valid = 0
    with open("grpo_train_augmented.jsonl") as f:
        for line in f:
            total += 1
            rec = json.loads(line.strip())
            if rec.get("prompt", "").strip() and rec.get("completion", "").strip():
                valid += 1
    assert total == 2545
    assert valid == total
test("Augmented Data", t8)

# 9
print("\n--- Reward Engine ---")
def t9():
    from grpo_reward_engine import compute_reward
    r = compute_reward("<reasoning>T</reasoning><solution>T</solution>", "test")
    assert "composite" in r
test("Reward Engine", t9)

# 10
print("\n--- Security KB ---")
def t10():
    from security_knowledge_base import SecurityKnowledgeBase
    kb = SecurityKnowledgeBase("test_kb.json")
    kb.add_finding("SQLi", "Web", "Critical", "desc")
    res = kb.search("sqli")
    assert len(res) >= 1
test("Security KB", t10)

# 11
print("\n--- CVE Converter ---")
def t11():
    from cve_to_training_data import CVEtoTrainingData
    c = CVEtoTrainingData("test_cve.jsonl")
    ex = c.convert("CVE-2024-0001", "RCE", "critical")
    assert len(ex) == 2
test("CVE Converter", t11)

# SUMMARY
print("\n" + "=" * 60)
print("  RESULTS")
print("=" * 60)
passed = sum(1 for _, s, _ in results if s == "PASS")
failed = sum(1 for _, s, _ in results if s == "FAIL")
for n, s, e in results:
    print(f"  {s}: {n}")
print(f"\n  Total: {len(results)} | Passed: {passed} | Failed: {failed}")
print("=" * 60)
