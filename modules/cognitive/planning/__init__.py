# src.modules.cognitive.planning — planning module
"""Cognitive Planning Module — task decomposition & prioritization.

Provides a ``Planner`` class that breaks goals into ordered sub-tasks,
tracks their status, and can report on progress.

Example::

    p = Planner()
    tasks = p.decompose("Write a blog post", ["Outline", "Draft", "Edit"])
    ordered = p.prioritize(tasks)
    for t in ordered:
        p.execute(t)
        p.monitor()
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class Task:
    """A single planning unit."""

    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0
    dependencies: list[str] = field(default_factory=list)
    result: Any = None
    error: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        data = dict(data)
        data["status"] = TaskStatus(data["status"])
        return cls(**data)


class Planner:
    """Task decomposition, prioritization, execution stubs, and monitoring.

    Parameters
    -------
    persist_path:
        Optional path to a JSON file for durable plan storage.
    """

    def __init__(self, persist_path: str | Path | None = None) -> None:
        self._tasks: dict[str, Task] = {}
        self._persist_path = Path(persist_path) if persist_path else None
        if self._persist_path and self._persist_path.exists():
            self._load()

    # ------------------------------------------------------------------ #
    # task registry helpers                                               #
    # ------------------------------------------------------------------ #
    def _add(self, task: Task) -> None:
        self._tasks[task.id] = task
        self._save()

    def _get(self, task_id: str) -> Task:
        if task_id not in self._tasks:
            raise KeyError(f"Task {task_id!r} not found")
        return self._tasks[task_id]

    def _save(self) -> None:
        if not self._persist_path:
            return
        data = [t.to_dict() for t in self._tasks.values()]
        self._persist_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _load(self) -> None:
        raw = json.loads(self._persist_path.read_text(encoding="utf-8"))
        for item in raw:
            t = Task.from_dict(item)
            self._tasks[t.id] = t

    @property
    def tasks(self) -> list[Task]:
        """Return all tasks ordered by descending priority."""
        return sorted(self._tasks.values(), key=lambda t: -t.priority)

    # ------------------------------------------------------------------ #
    # core API                                                            #
    # ------------------------------------------------------------------ #
    def decompose(
        self,
        goal: str,
        steps: list[str],
        *,
        priorities: list[int] | None = None,
        dependencies: dict[str, list[str]] | None = None,
    ) -> list[Task]:
        """Break *goal* into ordered sub-tasks given by *steps*.

        Each step becomes a ``Task`` with an auto-generated id derived from
        the goal slug and step index.  Optional *priorities* and
        *dependencies* maps can be supplied to control ordering.
        """
        import re

        slug = re.sub(r"[^a-z0-9]+", "_", goal.lower()).strip("_")[:30]
        tasks: list[Task] = []
        for i, step in enumerate(steps):
            tid = f"{slug}_{i:03d}"
            pri = priorities[i] if priorities and i < len(priorities) else 0
            deps: list[str] = []
            if dependencies and tid in dependencies:
                deps = dependencies[tid]
            task = Task(
                id=tid,
                description=step,
                priority=pri,
                dependencies=deps,
            )
            self._add(task)
            tasks.append(task)
        return tasks

    def prioritize(self, tasks: list[Task] | None = None) -> list[Task]:
        """Return tasks sorted by descending priority (highest first).

        Respects dependency ordering: a task whose dependencies are not all
        ``DONE`` is sorted *after* tasks with the same priority.
        """
        if tasks is None:
            tasks = list(self._tasks.values())

        def _ready(t: Task) -> bool:
            return all(
                self._tasks[dep].status == TaskStatus.DONE
                for dep in t.dependencies
                if dep in self._tasks
            )

        return sorted(
            tasks,
            key=lambda t: (0 if _ready(t) else 1, -t.priority),
        )

    def execute(self, task: Task | str, *, result: Any = None) -> Task:
        """Mark a task as completed (or update its result).

        Accepts a ``Task`` object or task-id string.  Executes
        dependency checks before marking progress.
        """
        if isinstance(task, str):
            task = self._get(task)

        blocked = [
            dep
            for dep in task.dependencies
            if dep in self._tasks
            and self._tasks[dep].status != TaskStatus.DONE
        ]
        if blocked:
            task.status = TaskStatus.BLOCKED
            task.error = f"Blocked by: {blocked}"
            task.updated_at = datetime.now(timezone.utc).isoformat()
            self._save()
            return task

        task.status = TaskStatus.DONE
        task.result = result
        task.error = None
        task.updated_at = datetime.now(timezone.utc).isoformat()
        self._save()
        return task

    def monitor(self) -> dict[str, Any]:
        """Return a summary dict of all task statuses and overall progress."""
        total = len(self._tasks)
        counts: dict[str, int] = {s.value: 0 for s in TaskStatus}
        for t in self._tasks.values():
            counts[t.status.value] += 1

        pct = (counts[TaskStatus.DONE.value] / total * 100) if total else 0.0
        return {
            "total": total,
            "counts": counts,
            "progress_pct": round(pct, 1),
            "tasks": [t.to_dict() for t in self.tasks],
        }

    def reset(self) -> int:
        """Remove all tasks.  Returns count of cleared tasks."""
        n = len(self._tasks)
        self._tasks.clear()
        self._save()
        return n

    def export(self) -> list[dict[str, Any]]:
        """Return all tasks as a list of plain dicts."""
        return [t.to_dict() for t in self.tasks]

    def __len__(self) -> int:
        return len(self._tasks)

    def __repr__(self) -> str:
        done = sum(1 for t in self._tasks.values() if t.status == TaskStatus.DONE)
        return f"<Planner tasks={len(self)} done={done}>"
