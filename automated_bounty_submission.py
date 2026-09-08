#!/usr/bin/env python3
"""
automated_bounty_submission.py - Automated bug bounty submission tool.

Formats findings to HackerOne/Bugcrowd templates, generates reproduction steps,
calculates CVSS v3.1 scores, submits via API, and tracks submission status.

DISCLAIMER: Only use on programs you are authorized to test. Unauthorized
access to computer systems is illegal.
"""

import argparse, base64, csv, datetime, json, sys, urllib.request, urllib.error
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent
TRACKING_DB = WORKSPACE / "bounty_submissions.json"
HACKERONE_API = "https://api.hackerone.com/v1"
BUGCROWD_API = "https://api.bugcrowd.com/v1"

# CVSS v3.1 weights
_W = {
    "AV": {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.20},
    "AC": {"L": 0.77, "H": 0.44},
    "PR": {"N": 0.85, "L": 0.62, "H": 0.27},
    "PRc": {"N": 0.85, "L": 0.68, "H": 0.50},
    "UI": {"N": 0.85, "R": 0.62},
    "CIA": {"N": 0.0, "L": 0.22, "H": 0.56},
}
_SEV = [(0.0, 0.0, "None"), (0.1, 3.9, "Low"), (4.0, 6.9, "Medium"),
        (7.0, 8.9, "High"), (9.0, 10.0, "Critical")]

def calculate_cvss(vector: str) -> dict:
    """Calculate CVSS v3.1 base score from vector string."""
    p = dict(m.split(":") for m in vector.replace("CVSS:3.1/", "").split("/"))
    av = _W["AV"].get(p.get("AV", "N"), 0.85)
    ac = _W["AC"].get(p.get("AC", "L"), 0.77)
    scope = p.get("S", "U") == "C"
    pr_key = p.get("PR", "N")
    pr = (_W["PRc"] if scope else _W["PR"]).get(pr_key, 0.85)
    ui = _W["UI"].get(p.get("UI", "N"), 0.85)
    c = _W["CIA"].get(p.get("C", "N"), 0.0)
    i = _W["CIA"].get(p.get("I", "N"), 0.0)
    a = _W["CIA"].get(p.get("A", "N"), 0.0)

    iss = 1 - ((1 - c) * (1 - i) * (1 - a))
    if iss <= 0:
        iss = 0.0
    impact = (7.52 * (iss - 0.029) - 3.25 * ((iss - 0.02) ** 15)) if scope else 6.42 * iss
    exploit = 8.22 * av * ac * pr * ui

    if impact <= 0:
        score = 0.0
    elif scope:
        score = min(1.08 * (impact + exploit), 10.0)
    else:
        score = min(impact + exploit, 10.0)
    score = round(score, 1)

    severity = "None"
    for lo, hi, label in _SEV:
        if lo <= score <= hi:
            severity = label
            break
    return {"score": score, "severity": severity, "vector": vector,
            "impact_sub": round(iss, 3), "exploit_sub": round(exploit, 3), "scope": scope}


def format_report(finding: dict, platform: str) -> str:
    """Format finding dict into platform-specific report."""
    cvss = calculate_cvss(finding.get("cvss_vector", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N"))
    steps = finding.get("reproduction_steps", [])
    steps_md = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps)) if steps else "1. No steps provided."

    data = {
        "title": finding.get("title", "Untitled"),
        "description": finding.get("description", "N/A"),
        "impact": finding.get("impact", "N/A"),
        "reproduction_steps": steps_md,
        "affected_url": finding.get("affected_url", "N/A"),
        "poc": finding.get("poc", "N/A"),
        "remediation": finding.get("remediation", "N/A"),
        "cvss_score": cvss["score"], "cvss_vector": cvss["vector"],
        "severity": cvss["severity"],
        "severity_rationale": finding.get("severity_rationale",
            f"CVSS {cvss['score']} = {cvss['severity']} severity."),
    }

    if platform == "hackerone":
        return (
            f"# {data['title']}\n\n## Description\n{data['description']}\n\n"
            f"## Impact\n{data['impact']}\n\n## Steps to Reproduce\n{data['reproduction_steps']}\n\n"
            f"## Affected Component\n{data['affected_url']}\n\n## Proof of Concept\n{data['poc']}\n\n"
            f"## Remediation\n{data['remediation']}\n\n"
            f"## CVSS Score\n**Score:** {data['cvss_score']} ({data['severity']})\n"
            f"**Vector:** {data['cvss_vector']}\n\n"
            f"## Severity Assessment Rationale\n{data['severity_rationale']}\n"
        )
    else:  # bugcrowd
        return (
            f"# {data['title']}\n\n## Description\n{data['description']}\n\n"
            f"## Impact\n{data['impact']}\n\n## Steps to Reproduce\n{data['reproduction_steps']}\n\n"
            f"## Affected Hosts/URLs\n{data['affected_url']}\n\n## Proof of Concept\n{data['poc']}\n\n"
            f"## Suggested Fix\n{data['remediation']}\n\n"
            f"## CVSS\n**Score:** {data['cvss_score']}\n**Vector:** {data['cvss_vector']}\n"
            f"**Severity:** {data['severity']}\n\n## Severity Rationale\n{data['severity_rationale']}\n"
        )


# --- API Clients ---

class HackerOneClient:
    def __init__(self, token: str, username: str):
        self.token, self.user, self.base = token, username, HACKERONE_API

    def _req(self, method: str, endpoint: str, data=None):
        url = f"{self.base}/{endpoint}"
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Basic {base64.b64encode(f'{self.user}:{self.token}'.encode()).decode()}")
        req.add_header("User-Agent", "bounty-sub/1.0")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return {"error": True, "status": e.code, "message": e.read().decode(errors="replace")}
        except Exception as e:
            return {"error": True, "message": str(e)}

    def submit(self, program: str, report: dict):
        return self._req("POST", "reports", {"data": {"type": "report", "attributes": report}})

    def get_report(self, rid: str):
        return self._req("GET", f"reports/{rid}")


class BugcrowdClient:
    def __init__(self, token: str):
        self.token, self.base = token, BUGCROWD_API

    def _req(self, method: str, endpoint: str, data=None):
        url = f"{self.base}/{endpoint}"
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Token {self.token}")
        req.add_header("User-Agent", "bounty-sub/1.0")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return {"error": True, "status": e.code, "message": e.read().decode(errors="replace")}
        except Exception as e:
            return {"error": True, "message": str(e)}

    def submit(self, program: str, report: dict):
        return self._req("POST", f"programs/{program}/submissions",
                         {"data": {"type": "submission", "attributes": report}})

    def get_submission(self, sid: str):
        return self._req("GET", f"submissions/{sid}")


# --- Tracking DB ---

def _load_db() -> list:
    return json.loads(TRACKING_DB.read_text()) if TRACKING_DB.exists() else []

def _save_db(entries: list):
    TRACKING_DB.write_text(json.dumps(entries, indent=2, ensure_ascii=False))

def add_entry(entry: dict) -> dict:
    db = _load_db()
    entry["id"] = len(db) + 1
    entry["created_at"] = entry["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
    entry.setdefault("status", "submitted")
    db.append(entry)
    _save_db(db)
    return entry

def update_status(eid: int, status: str):
    db = _load_db()
    for e in db:
        if e.get("id") == eid:
            e["status"] = status
            e["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
    _save_db(db)

def list_entries(platform: str = None) -> list:
    db = _load_db()
    return [e for e in db if not platform or e.get("platform") == platform]

def export_csv(path: str):
    db = _load_db()
    if not db:
        print("No submissions to export."); return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "platform", "submission_id", "title",
                          "status", "severity", "cvss_score", "created_at", "updated_at"],
                          extrasaction="ignore")
        w.writeheader(); w.writerows(db)
    print(f"Exported {len(db)} to {path}")


# --- CLI Commands ---

def cmd_cvss(args):
    r = calculate_cvss(args.vector)
    print(f"CVSS Score: {r['score']}\nSeverity:  {r['severity']}\nVector:     {r['vector']}")
    print(f"Impact Sub-Score:         {r['impact_sub']}")
    print(f"Exploitability Sub-Score: {r['exploit_sub']}\nScope Changed: {r['scope']}")

def cmd_format(args):
    finding = json.loads(Path(args.finding).read_text())
    report = format_report(finding, args.platform)
    if args.output:
        Path(args.output).write_text(report)
        print(f"Report written to {args.output}")
    else:
        print(report)

def cmd_submit(args):
    finding = json.loads(Path(args.finding).read_text())
    report_body = format_report(finding, args.platform)
    cvss = calculate_cvss(finding.get("cvss_vector", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N"))

    if args.platform == "hackerone":
        if not all([args.api_token, args.username, args.program]):
            print("Error: --api-token, --username, --program required"); sys.exit(1)
        client = HackerOneClient(args.api_token, args.username)
        result = client.submit(args.program, {
            "title": finding.get("title", "Untitled"),
            "vulnerability_information": report_body,
            "severity_rating": cvss["severity"].lower(),
        })
    else:
        if not all([args.api_token, args.program]):
            print("Error: --api-token and --program required"); sys.exit(1)
        client = BugcrowdClient(args.api_token)
        sev_map = {"None": 1, "Low": 2, "Medium": 3, "High": 4, "Critical": 4}
        result = client.submit(args.program, {
            "title": finding.get("title", "Untitled"),
            "description": report_body,
            "severity": sev_map.get(cvss["severity"], 2),
        })

    if result.get("error"):
        print(f"Submission failed: {result.get('message', 'Unknown error')}"); sys.exit(1)

    sid = result.get("data", {}).get("id")
    entry = add_entry({
        "platform": args.platform, "submission_id": sid,
        "title": finding.get("title", "Untitled"), "severity": cvss["severity"],
        "cvss_score": cvss["score"], "cvss_vector": finding.get("cvss_vector", ""),
        "program": args.program, "api_response": result,
    })
    print(f"Submission successful!\n  Platform ID: {sid}\n  Local ID: {entry['id']}\n  Status: {entry['status']}")

def cmd_track(args):
    if args.platform == "hackerone":
        if not all([args.api_token, args.username]):
            print("Error: --api-token and --username required"); sys.exit(1)
        r = HackerOneClient(args.api_token, args.username).get_report(args.submission_id)
    else:
        if not args.api_token:
            print("Error: --api-token required"); sys.exit(1)
        r = BugcrowdClient(args.api_token).get_submission(args.submission_id)

    if r.get("error"):
        print(f"Error: {r.get('message')}"); sys.exit(1)

    state = (r.get("data", {}).get("attributes", {}).get("state", "unknown")
            if args.platform == "hackerone" else
            r.get("data", {}).get("attributes", {}).get("state", "unknown"))
    print(f"Submission {args.submission_id} status: {state}")

    for e in _load_db():
        if str(e.get("submission_id")) == str(args.submission_id):
            update_status(e["id"], state)
            print(f"Local entry #{e['id']} updated.")

def cmd_list(args):
    entries = list_entries(args.platform)
    if not entries:
        print("No submissions tracked."); return
    print(f"{'ID':<5} {'Platform':<12} {'Sub ID':<15} {'Severity':<10} {'Status':<15} {'Title'}")
    print("-" * 85)
    for e in entries:
        print(f"{e.get('id','?'):<5} {e.get('platform','?'):<12} "
              f"{str(e.get('submission_id','?')):<15} {e.get('severity','?'):<10} "
              f"{e.get('status','?'):<15} {e.get('title','?')[:35]}")
    if args.export:
        export_csv(args.export)

def cmd_generate_template(args):
    template = {
        "title": "Reflected XSS in Search Parameter",
        "description": "The search parameter reflects user input without sanitization.",
        "impact": "Attacker can execute JavaScript in victim's session, leading to account takeover.",
        "reproduction_steps": [
            "Navigate to https://example.com/search?q=test",
            "Replace 'test' with: <script>alert(document.cookie)</script>",
            "Press Enter and observe the alert popup",
        ],
        "affected_url": "https://example.com/search",
        "poc": "https://example.com/search?q=%3Cscript%3Ealert(document.cookie)%3C/script%3E",
        "remediation": "Apply context-aware output encoding to all user-supplied input.",
        "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N",
        "severity_rationale": "Network vector, low complexity, requires user interaction.",
    }
    Path(args.output).write_text(json.dumps(template, indent=2))
    print(f"Sample template written to {args.output}")


def main():
    p = argparse.ArgumentParser(description="Automated bug bounty submission tool.")
    sp = p.add_subparsers(dest="command")

    cvss_p = sp.add_parser("cvss", help="Calculate CVSS v3.1 score")
    cvss_p.add_argument("--vector", required=True)

    fmt_p = sp.add_parser("format", help="Format finding to platform template")
    fmt_p.add_argument("--platform", choices=["hackerone", "bugcrowd"], required=True)
    fmt_p.add_argument("--finding", required=True)
    fmt_p.add_argument("--output", "-o")

    sub_p = sp.add_parser("submit", help="Submit finding to platform")
    sub_p.add_argument("--platform", choices=["hackerone", "bugcrowd"], required=True)
    sub_p.add_argument("--finding", required=True)
    sub_p.add_argument("--api-token")
    sub_p.add_argument("--username")
    sub_p.add_argument("--program")

    trk_p = sp.add_parser("track", help="Track submission status")
    trk_p.add_argument("--platform", choices=["hackerone", "bugcrowd"], required=True)
    trk_p.add_argument("--submission-id", required=True)
    trk_p.add_argument("--api-token")
    trk_p.add_argument("--username")

    lst_p = sp.add_parser("list", help="List tracked submissions")
    lst_p.add_argument("--platform", choices=["hackerone", "bugcrowd"])
    lst_p.add_argument("--export")

    gen_p = sp.add_parser("generate-template", help="Generate sample finding JSON")
    gen_p.add_argument("--output", "-o", default="finding_template.json")

    args = p.parse_args()
    if not args.command:
        p.print_help(); sys.exit(1)

    {"cvss": cmd_cvss, "format": cmd_format, "submit": cmd_submit,
     "track": cmd_track, "list": cmd_list, "generate-template": cmd_generate_template
    }[args.command](args)


if __name__ == "__main__":
    main()
