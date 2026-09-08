#!/usr/bin/env python3
import json, os, re
from datetime import datetime
from pathlib import Path

class AutomatedCTIMonitor:
    def __init__(self, db_path="intelligence/cti_database.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.data = {"iocs": [], "alerts": []}
        if self.db_path.exists():
            self.data = json.loads(self.db_path.read_text())
    
    def ingest_ioc(self, ioc_type, value, source, severity="medium", description=""):
        """Ingest a new IOC."""
        ioc = {
            "type": ioc_type,
            "value": value,
            "source": source,
            "severity": severity,
            "description": description,
            "ingested": datetime.utcnow().isoformat() + "Z",
            "active": True,
        }
        # Check for duplicates
        for existing in self.data["iocs"]:
            if existing["value"] == value and existing["type"] == ioc_type:
                return existing
        self.data["iocs"].append(ioc)
        self._save()
        return ioc
    
    def correlate_with_infrastructure(self, infra_assets):
        """Correlate IOCs with our infrastructure."""
        alerts = []
        for asset in infra_assets:
            for ioc in self.data["iocs"]:
                if not ioc.get("active"):
                    continue
                # Check for matches
                if ioc["value"].lower() in asset.lower() or asset.lower() in ioc["value"].lower():
                    alert = {
                        "asset": asset,
                        "ioc": ioc,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "severity": ioc["severity"],
                    }
                    alerts.append(alert)
        self.data["alerts"].extend(alerts)
        self._save()
        return alerts
    
    def get_active_iocs(self, ioc_type=None):
        """Get active IOCs."""
        iocs = [i for i in self.data["iocs"] if i.get("active")]
        if ioc_type:
            iocs = [i for i in iocs if i["type"] == ioc_type]
        return iocs
    
    def deactivate_ioc(self, value):
        """Deactivate an IOC."""
        for ioc in self.data["iocs"]:
            if ioc["value"] == value:
                ioc["active"] = False
        self._save()
    
    def generate_report(self):
        """Generate CTI report."""
        total = len(self.data["iocs"])
        active = len([i for i in self.data["iocs"] if i.get("active")])
        alerts = len(self.data["alerts"])
        
        by_type = {}
        for ioc in self.data["iocs"]:
            t = ioc["type"]
            by_type[t] = by_type.get(t, 0) + 1
        
        by_severity = {}
        for ioc in self.data["iocs"]:
            s = ioc["severity"]
            by_severity[s] = by_severity.get(s, 0) + 1
        
        return {
            "total_iocs": total,
            "active_iocs": active,
            "alerts": alerts,
            "by_type": by_type,
            "by_severity": by_severity,
        }
    
    def _save(self):
        self.db_path.write_text(json.dumps(self.data, indent=2))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    
    p = sub.add_parser("ingest")
    p.add_argument("--type", required=True)
    p.add_argument("--value", required=True)
    p.add_argument("--source", default="manual")
    p.add_argument("--severity", default="medium")
    p.add_argument("--description", default="")
    
    p = sub.add_parser("correlate")
    p.add_argument("--assets", nargs="+", required=True)
    
    p = sub.add_parser("report", action="store_true")
    
    args = parser.parse_args()
    monitor = AutomatedCTIMonitor()
    
    if args.cmd == "ingest":
        ioc = monitor.ingest_ioc(args.type, args.value, args.source, args.severity, args.description)
        print(json.dumps(ioc, indent=2))
    elif args.cmd == "correlate":
        alerts = monitor.correlate_with_infrastructure(args.assets)
        print(json.dumps(alerts, indent=2))
    elif args.cmd == "report":
        print(json.dumps(monitor.generate_report(), indent=2))
