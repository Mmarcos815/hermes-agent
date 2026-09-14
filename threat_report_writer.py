#!/usr/bin/env python3
import json, os, re
from datetime import datetime
from pathlib import Path

class ThreatReportWriter:
    def __init__(self, output_dir="reports/threat_intel"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def threat_report_template(self, title, iocs, ttps, targets, severity="medium"):
        """Generate a threat report template."""
        report = f"""# {title}

**Severity:** {severity}
**Date:** {datetime.now().strftime('%Y-%m-%d')}

## Executive Summary

Threat report for {title}.

## Indicators of Compromise (IOCs)
"""
        for ioc in iocs:
            report += f"- **{ioc['type']}**: {ioc['value']} ({ioc.get('source', 'unknown')})\n"
        
        report += "\n## TTPs (Tactics, Techniques, Procedures)\n"
        for ttp in ttps:
            report += f"- **{ttp['id']}**: {ttp['name']} ({ttp['tactic']})\n"
        
        report += "\n## Targeted Sectors\n"
        for target in targets:
            report += f"- {target}\n"
        
        report += """
## Recommendations
1. Monitor for listed IOCs
2. Implement detection rules for TTPs
3. Review affected systems
"""
        return report
    
    def generate_report(self, title, iocs, ttps, targets, severity="medium"):
        """Generate threat report and save to file."""
        report = self.threat_report_template(title, iocs, ttps, targets, severity)
        output_file = self.output_dir / f"{title.lower().replace(' ', '_')}.md"
        output_file.write_text(report)
        return {"report": report, "file": str(output_file)}
    
    def generate_html(self, title, iocs, ttps, targets, severity="medium"):
        """Generate HTML threat report."""
        report = self.generate_report(title, iocs, ttps, targets, severity)
        html = f"""<!DOCTYPE html>
<html>
<head><title>{title}</title></head>
<body>
<pre>{report['report']}</pre>
</body>
</html>"""
        return html
