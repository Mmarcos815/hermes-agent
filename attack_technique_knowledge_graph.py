#!/usr/bin/env python3
import json
from pathlib import Path

TECHNIQUES = {
    "T1001": {"name": "Data Obfuscified", "tactic": "Command and Control"},
    "T1003": {"name": "OS Credential Dumping", "tactic": "Credential Access"},
    "T1055": {"name": "Process Injection", "tactic": "Defense Evasion"},
    "T1059": {"name": "Command and Scripting Interpreter", "tactic": "Execution"},
    "T1071": {"name": "Application Layer Protocol", "tactic": "Command and Control"},
    "T1080": {"name": "Taint Shared Content", "tactic": "Lateral Movement"},
    "T1082": {"name": "System Information Discovery", "tactic": "Discovery"},
    "T1105": {"name": "Ingress Tool Transfer", "tactic": "Command and Control"},
    "T1190": {"name": "Exploit Public-Facing Application", "tactic": "Initial Access"},
    "T1485": {"name": "Data Destruction", "tactic": "Impact"},
    "T1498": {"name": "Network Denial of Service", "tactic": "Impact"},
    "T1566": {"name": "Phishing", "tactic": "Initial Access"},
    "T1574": {"name": "Hijack Execution Flow", "tactic": "Persistence"},
}

class KnowledgeGraph:
    def __init__(self, data_dir="knowledge/graph"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.techniques = TECHNIQUES.copy()
        self.edges = []
    
    def add_edge(self, from_id, to_id, rel_type="leads-to"):
        self.edges.append({"from": from_id, "to": to_id, "type": rel_type})
    
    def get_neighbors(self, tid):
        return [(e["to"], e["type"]) for e in self.edges if e["from"] == tid]
    
    def find_path(self, start_id, end_id, max_depth=5):
        visited = set()
        def dfs(current, path):
            if current == end_id:
                return path
            if len(path) >= max_depth or current in visited:
                return None
            visited.add(current)
            for neighbor, rel in self.get_neighbors(current):
                result = dfs(neighbor, path + [(current, rel)])
                if result:
                    return result
            return None
        return dfs(start_id, [])
    
    def export_json(self, output="knowledge/graph/attack_graph.json"):
        data = {"techniques": self.techniques, "edges": self.edges}
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(json.dumps(data, indent=2))
        return output
    
    def export_html(self, output="knowledge/graph/attack_graph.html"):
        html = "<html><head><title>Attack Graph</title></head><body>"
        html += "<h1>MITRE ATT&CK Knowledge Graph</h1>"
        html += "<p>Techniques: " + str(len(self.techniques)) + "</p>"
        html += "<p>Edges: " + str(len(self.edges)) + "</p>"
        html += "</body></html>"
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(html)
        return output
    
    def load_default_edges(self):
        edges = [
            ("T1190", "T1055"), ("T1566", "T1059"), ("T1059", "T1003"),
            ("T1003", "T1574"), ("T1574", "T1055"), ("T1055", "T1071"),
            ("T1071", "T1105"), ("T1105", "T1485"), ("T1082", "T1003"),
        ]
        for from_id, to_id in edges:
            self.add_edge(from_id, to_id)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    kg = KnowledgeGraph()
    kg.load_default_edges()
    if args.html:
        print("HTML: " + kg.export_html())
    elif args.json:
        print("JSON: " + kg.export_json())
    else:
        print("Techniques: " + str(len(kg.techniques)))
        print("Edges: " + str(len(kg.edges)))
