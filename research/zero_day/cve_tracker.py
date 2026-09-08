"""Track CVE discoveries through the disclosure lifecycle."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from typing import Optional


class CVEStatus(Enum):
    DISCOVERED = "discovered"
    VENDOR_NOTIFIED = "vendor_notified"
    PATCH_IN_PROGRESS = "patch_in_progress"
    PUBLIC_DISCLOSURE = "public_disclosure"
    RESOLVED = "resolved"
    CLOSED = "closed"


@dataclass
class CVEDiscovery:
    cve_id: Optional[str] = None
    description: str = ""
    target: str = ""
    severity: str = ""
    crash_type: str = ""
    discovery_date: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: CVEStatus = CVEStatus.DISCOVERED
    vendor_notified_date: str | None = None
    expected_disclosure_date: str | None = None
    patch_version: str | None = None
    notes: list[str] = field(default_factory=list)


class CVETracker:
    def __init__(self, db_path: str = "./cves.json"):
        self.db_path = db_path
        self.entries: list[CVEDiscovery] = []
        self._load()

    def register(self, crash_report) -> CVEDiscovery:
        discovery = CVEDiscovery(
            description=f"{getattr(crash_report, 'crash_type', 'unknown')} in target",
            severity=getattr(crash_report, 'severity', 'none'),
            crash_type=getattr(crash_report, 'crash_type', 'unknown'),
        )
        discovery.expected_disclosure_date = (
            datetime.utcnow() + timedelta(days=90)
        ).isoformat()
        self.entries.append(discovery)
        self._save()
        return discovery

    def update_status(self, index: int, status: CVEStatus, note: str = "") -> None:
        if 0 <= index < len(self.entries):
            entry = self.entries[index]
            entry.status = status
            if status == CVEStatus.VENDOR_NOTIFIED:
                entry.vendor_notified_date = datetime.utcnow().isoformat()
            if note:
                entry.notes.append(note)
            self._save()

    def assign_cve(self, index: int, cve_id: str) -> None:
        if 0 <= index < len(self.entries):
            self.entries[index].cve_id = cve_id
            self._save()

    def pending_disclosure(self) -> list[tuple[int, CVEDiscovery]]:
        now = datetime.utcnow()
        return [
            (i, e) for i, e in enumerate(self.entries)
            if e.expected_disclosure_date
            and e.status not in (CVEStatus.RESOLVED, CVEStatus.CLOSED)
            and now >= datetime.fromisoformat(e.expected_disclosure_date)
        ]

    def stats(self) -> dict[str, int]:
        counts = {s.value: sum(1 for e in self.entries if e.status == s) for s in CVEStatus}
        counts["total"] = len(self.entries)
        return counts

    def to_dict(self) -> list[dict]:
        return [
            {
                "cve_id": e.cve_id, "description": e.description, "target": e.target,
                "severity": e.severity, "crash_type": e.crash_type,
                "discovery_date": e.discovery_date, "status": e.status.value,
                "vendor_notified_date": e.vendor_notified_date,
                "expected_disclosure_date": e.expected_disclosure_date,
                "patch_version": e.patch_version, "notes": e.notes,
            }
            for e in self.entries
        ]

    def _load(self) -> None:
        try:
            with open(self.db_path, "r") as f:
                data = json.load(f)
                for row in data:
                    self.entries.append(CVEDiscovery(
                        cve_id=row.get("cve_id"), description=row.get("description", ""),
                        target=row.get("target", ""), severity=row.get("severity", ""),
                        crash_type=row.get("crash_type", ""),
                        discovery_date=row.get("discovery_date", datetime.utcnow().isoformat()),
                        status=CVEStatus(row.get("status", "discovered")),
                        vendor_notified_date=row.get("vendor_notified_date"),
                        expected_disclosure_date=row.get("expected_disclosure_date"),
                        patch_version=row.get("patch_version"), notes=row.get("notes", []),
                    ))
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def _save(self) -> None:
        with open(self.db_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
