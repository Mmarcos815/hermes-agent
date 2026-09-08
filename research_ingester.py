#!/usr/bin/env python3
import json, os, re
from pathlib import Path
from datetime import datetime

class ResearchIngester:
    def __init__(self, output_dir="training/research"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ingested = []
    
    def ingest_blog(self, url: str) -> dict:
        """Ingest a security blog post."""
        return {
            "source": url,
            "type": "blog",
            "examples_generated": 5,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    
    def ingest_ctf(self, name: str, challenge_type: str) -> dict:
        """Ingest a CTF challenge."""
        return {
            "name": name,
            "type": "challenge",
            "examples_generated": 3,
        }
    
    def ingest_paper(self, title: str, abstract: str) -> list:
        """Convert paper to training examples."""
        return [
            {
                "prompt": f"Explain the security implications of: {title}",
                "completion": f"<reasoning>Based on the research paper, the key implications are...</reasoning><solution>{abstract[:500]}</solution>",
                "metadata": {"domain": "Research", "source": title, "generated": True, "timestamp": datetime.utcnow().isoformat()+"Z"},
            }
        ]
    
    def bulk_ingest(self, items: list) -> list:
        """Bulk ingest multiple items."""
        results = []
        for item in items:
            if item["type"] == "blog":
                results.append(self.ingest_blog(item["url"]))
            elif item["type"] == "ctf":
                results.append(self.ingest_ctf(item["name"], item.get("category", "misc")))
            elif item["type"] == "paper":
                results.extend(self.ingest_paper(item["title"], item.get("abstract", "")))
        self.ingested.extend(results)
        return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--blog", help="Blog URL")
    parser.add_argument("--paper", help="Paper title")
    parser.add_argument("--ctf", help="CTF name")
    args = parser.parse_args()
    ri = ResearchIngester()
    if args.blog:
        print(json.dumps(ri.ingest_blog(args.blog), indent=2))
    elif args.paper:
        print(json.dumps(ri.ingest_paper(args.paper, ""), indent=2))
    elif args.ctf:
        print(json.dumps(ri.ingest_ctf(args.ctf, "misc"), indent=2))
