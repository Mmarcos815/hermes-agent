#!/usr/bin/env python3
import json, os, re
from datetime import datetime
from pathlib import Path

class ThreatReportWriter:
    def __init__(self, output_dir="reports/threat_intel"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(self, title, iocs, ttps, targets, severity="medium"):
        """Generate a threat intelligence report."""
        report = {
            "title": title,
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "severity": severity,
            "iocs": iocs,
            "ttps": ttps,
            "targets": targets,
            "summary": f"Threat intelligence report: {title}",
        }
        
        # Generate Markdown
        md = f"""# {title}

**Date:** {report['date']}  
**Severity:** {severity.upper()}

## Executive Summary
{threat_report_template(title, iocs, ttps, targets)}

## Indicators of Compromise (IOCs)
"""
        for ioc in iocs:
            md += f"- **{ioc['type']}**: {ioc['value']} ({ioc.get('source', 'unknown')})
"
        
        md += "
## TTPs (Tactics, Techniques, Procedures)
"
        for ttp in ttps:
            md += f"- **{ttp['id']}**: {ttp['name']} ({ttp['tactic']})
"
        
        md += "
## Targeted Sectors
"
        for target in targets:
            md += f"- {target}
"
        
        md += "
## Recommendations
"
        md += "1. Monitor for listed IOCs
"
        md += "2. Implement detection rules for TTPs
"
        md += "3. Review affected systems
"
        
        # Save
        output_file = self.output_dir / f"{title.lower().replace(' ', '_')}.md"
        output_file.write_text(md)
        return {"report": report, "file": str(output_file)}
    
    def generate_html(self, title, iocs, ttps, targets, severity="medium"):
        """Generate HTML threat report."""
        md = self.generate_report(title, iocs, ttps, targets, severity)
        html = f"""<!DOCTYPE html>
<html><head><title>{title}</title></head><body>
<h1>{title}</h1>
<p>Date: {datetime.utcnow().strftime('%Y-%m-%d')}</p>
<p>Severity: {severity.upper()}</p>
</body></html>"""
        output_file = self.output_dir / f"{title.lower().replace(' ', '_')}.html"
        output_file.write_text(html)
        return {"file": str(output_file)}

def threat_report_template(title, iocs, ttps, targets):
    return f"Analysis of {title} affecting {len(targets)} sectors with {len(iocs)} IOCs and {len(ttps)} TTPs."

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("title")
    parser.add_argument("--iocs", type=json.loads, default="[]")
    parser.add_argument("--ttps", type=json.loads, default="[]")
    parser.add_argument("--targets", nargs="+", default=[])
    parser.add_argument("--severity", default="medium")
    args = parser.parse_args()
    writer = ThreatReportWriter()
    result = writer.generate_report(args.title, args.iocs, args.ttps, args.targets, args.severity)
    print(json.dumps(result, indent=2))
