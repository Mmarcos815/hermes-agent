"""Tests for cognitive architecture modules."""

import pytest
from modules.cognitive.memory import Memory
from modules.cognitive.planning import Planner, Task, TaskStatus
from modules.cognitive.reasoning import Reasoner, ThoughtStep, Decision


class TestMemory:
    def test_store_and_retrieve(self):
        m = Memory(":memory:")
        m.store("key1", "value1")
        assert m.retrieve("key1") == "value1"

    def test_store_dict(self):
        m = Memory(":memory:")
        m.store("config", {"debug": True, "level": 3})
        assert m.retrieve("config") == {"debug": True, "level": 3}

    def test_retrieve_default(self):
        m = Memory(":memory:")
        assert m.retrieve("missing") is None
        assert m.retrieve("missing", "default") == "default"

    def test_search(self):
        m = Memory(":memory:")
        m.store("greeting", "hello world", tags=["basic"])
        m.store("farewell", "goodbye world")
        results = m.search("world")
        assert len(results) == 2
        keys = {r["key"] for r in results}
        assert keys == {"greeting", "farewell"}

    def test_search_tags(self):
        m = Memory(":memory:")
        m.store("key1", "value1", tags=["important"])
        m.store("key2", "value2")
        results = m.search("important")
        assert len(results) == 1
        assert results[0]["key"] == "key1"

    def test_delete(self):
        m = Memory(":memory:")
        m.store("key1", "value1")
        assert m.delete("key1") is True
        assert m.retrieve("key1") is None
        assert m.delete("key1") is False

    def test_update(self):
        m = Memory(":memory:")
        m.store("key1", "value1")
        m.store("key1", "value2")
        assert m.retrieve("key1") == "value2"
        assert len(m) == 1

    def test_keys(self):
        m = Memory(":memory:")
        m.store("a", 1)
        m.store("b", 2)
        assert set(m.keys()) == {"a", "b"}

    def test_len(self):
        m = Memory(":memory:")
        assert len(m) == 0
        m.store("a", 1)
        assert len(m) == 1

    def test_contains(self):
        m = Memory(":memory:")
        m.store("key1", "value1")
        assert "key1" in m
        assert "missing" not in m

    def test_clear(self):
        m = Memory(":memory:")
        m.store("a", 1)
        m.store("b", 2)
        assert m.clear() == 2
        assert len(m) == 0

    def test_repr(self):
        m = Memory(":memory:")
        m.store("a", 1)
        assert "entries=1" in repr(m)


class TestPlanner:
    def test_decompose(self):
        p = Planner()
        tasks = p.decompose("Write blog", ["Outline", "Draft", "Edit"])
        assert len(tasks) == 3
        assert tasks[0].description == "Outline"
        assert tasks[2].description == "Edit"

    def test_decompose_with_priorities(self):
        p = Planner()
        tasks = p.decompose("Goal", ["A", "B", "C"], priorities=[3, 1, 2])
        assert tasks[0].priority == 3
        assert tasks[1].priority == 1

    def test_prioritize(self):
        p = Planner()
        tasks = p.decompose("Goal", ["A", "B", "C"], priorities=[1, 3, 2])
        ordered = p.prioritize()
        assert ordered[0].description == "B"
        assert ordered[1].description == "C"
        assert ordered[2].description == "A"

    def test_execute(self):
        p = Planner()
        tasks = p.decompose("Goal", ["A", "B"])
        p.execute(tasks[0], result="done")
        assert tasks[0].status == TaskStatus.DONE
        assert tasks[0].result == "done"

    def test_execute_by_id(self):
        p = Planner()
        tasks = p.decompose("Goal", ["A"])
        p.execute(tasks[0].id, result="ok")
        assert tasks[0].status == TaskStatus.DONE

    def test_execute_blocked_by_dependency(self):
        p = Planner()
        tasks = p.decompose("Goal", ["A", "B"])
        tasks[1].dependencies = [tasks[0].id]
        p.execute(tasks[1])
        assert tasks[1].status == TaskStatus.BLOCKED

    def test_monitor(self):
        p = Planner()
        tasks = p.decompose("Goal", ["A", "B"])
        p.execute(tasks[0])
        mon = p.monitor()
        assert mon["total"] == 2
        assert mon["counts"]["done"] == 1
        assert mon["counts"]["pending"] == 1
        assert mon["progress_pct"] == 50.0

    def test_reset(self):
        p = Planner()
        p.decompose("Goal", ["A", "B"])
        assert p.reset() == 2
        assert len(p) == 0

    def test_export(self):
        p = Planner()
        p.decompose("Goal", ["A"])
        data = p.export()
        assert len(data) == 1
        assert "id" in data[0]
        assert "status" in data[0]

    def test_repr(self):
        p = Planner()
        p.decompose("Goal", ["A", "B"])
        assert "tasks=2" in repr(p)


class TestReasoner:
    def test_think(self):
        r = Reasoner()
        steps = r.think("What is 2+2?")
        assert len(steps) >= 3
        assert steps[0].label == "restate"
        assert steps[1].label == "analyze"

    def test_think_with_perspectives(self):
        r = Reasoner()
        steps = r.think("Deploy?", perspectives=["dev", "ops"])
        labels = [s.label for s in steps]
        assert "perspectives" in labels

    def test_evaluate(self):
        r = Reasoner()
        steps = r.think("Test question")
        scores = r.evaluate(steps)
        assert "relevance" in scores
        assert "coherence" in scores
        assert "_weighted" in scores

    def test_decide_proceed(self):
        r = Reasoner()
        steps = r.think("Test")
        scores = r.evaluate(steps)
        decision = r.decide(scores, threshold=0.5)
        assert decision.verdict == "proceed"
        assert decision.confidence > 0

    def test_decide_reconsider(self):
        r = Reasoner()
        decision = r.decide({"_weighted": 0.3}, threshold=0.6)
        assert decision.verdict == "reconsider"

    def test_decide_with_options(self):
        r = Reasoner()
        decision = r.decide({"_weighted": 0.8}, options=["deploy", "wait"])
        assert decision.verdict in ["deploy", "wait"]
        assert len(decision.alternatives) == 1

    def test_explain(self):
        r = Reasoner()
        steps = r.think("Test")
        scores = r.evaluate(steps)
        decision = r.decide(scores)
        explanation = r.explain(decision)
        assert "Verdict" in explanation
        assert "Confidence" in explanation

    def test_trace(self):
        r = Reasoner()
        r.think("Q1")
        r.think("Q2")
        assert len(r.trace) >= 6  # at least 3 steps per think

    def test_reset(self):
        r = Reasoner()
        r.think("Test")
        r.reset()
        assert len(r) == 0

    def test_trace_json(self):
        r = Reasoner()
        r.think("Test")
        json_str = r.trace_json()
        assert "restate" in json_str

    def test_repr(self):
        r = Reasoner()
        r.think("Test")
        assert "steps=" in repr(r)
