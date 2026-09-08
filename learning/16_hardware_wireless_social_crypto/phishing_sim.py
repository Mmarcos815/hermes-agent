#!/usr/bin/env python3
"""Phishing Campaign Simulation — Educational/Authorized Testing Only."""

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse


@dataclass
class PhishingTemplate:
    name: str
    subject: str
    sender: str
    body: str
    landing_page: str
    technique: str
    indicators: list = field(default_factory=list)


@dataclass
class CloneAnalysis:
    url: str
    original_url: str
    similarity_score: float
    suspicious_elements: list = field(default_factory=list)
    risk_level: str = "LOW"


class PhishingSimulator:
    """Generate phishing templates and detect cloned landing pages."""

    TEMPLATE_LIBRARY = {
        'password_reset': {
            'subject': 'Action Required: Password Reset',
            'technique': 'Urgency + Authority',
            'body_template': '''Dear {target_name},

Our security system detected unusual activity on your account.
Please verify your identity within 24 hours to avoid suspension.

Click here to reset: {phishing_url}

IT Security Team''',
        },
        'invoice': {
            'subject': 'Invoice #{invoice_number} Overdue',
            'technique': 'Financial Urgency',
            'body_template': '''Hello {target_name},

Your invoice #{invoice_number} for ${amount} is overdue.
Please review the attached document and submit payment.

View invoice: {phishing_url}

Accounts Payable''',
        },
        'shared_document': {
            'subject': '{sender_name} shared a document with you',
            'technique': 'Curiosity + Trust',
            'body_template': '''Hi {target_name},

{sender_name} has shared "{document_name}" with you.
Click below to view the document:

{phishing_url}

This link expires in 48 hours.''',
        },
        'account_verification': {
            'subject': 'Verify Your Account - Unusual Login Attempt',
            'technique': 'Fear + Urgency',
            'body_template': '''Dear {target_name},

We detected a login attempt from {location} at {time}.
If this wasn't you, secure your account immediately:

{phishing_url}

Failure to verify within 12 hours will result in account lockout.

Security Team''',
        },
    }

    def generate_template(self, template_type: str, **kwargs) -> PhishingTemplate:
        """Generate a phishing template for authorized testing."""
        if template_type not in self.TEMPLATE_LIBRARY:
            available = ', '.join(self.TEMPLATE_LIBRARY.keys())
            raise ValueError(f"Unknown template: {template_type}. Available: {available}")

        template = self.TEMPLATE_LIBRARY[template_type]
        body = template['body_template'].format(**kwargs)

        return PhishingTemplate(
            name=template_type,
            subject=template['subject'],
            sender=kwargs.get('sender', 'security@company.com'),
            body=body,
            landing_page=kwargs.get('phishing_url', 'https://example.com'),
            technique=template['technique'],
            indicators=self._identify_indicators(body),
        )

    def _identify_indicators(self, body: str) -> list[str]:
        """Identify red flags that would reveal the phishing attempt."""
        indicators = []

        urgency_patterns = [
            r'within\s+\d+\s+hours',
            r'immediately',
            r'urgent',
            r'expires?\s+in',
            r'24\s+hours',
        ]
        for pattern in urgency_patterns:
            if re.search(pattern, body, re.IGNORECASE):
                indicators.append(f"Urgency language: '{pattern}'")

        if 'click' in body.lower() or 'here' in body.lower():
            indicators.append("Generic call-to-action (click here)")

        if 'suspend' in body.lower() or 'lockout' in body.lower():
            indicators.append("Threat language (suspension/lockout)")

        if 'verify' in body.lower() or 'confirm' in body.lower():
            indicators.append("Credential harvesting language")

        return indicators

    def generate_landing_page(self, target_brand: str, redirect_url: str) -> str:
        """Generate a simple landing page clone for testing awareness."""
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>{target_brand} - Secure Login</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 400px; margin: 50px auto; }}
        .login-box {{ border: 1px solid #ddd; padding: 30px; border-radius: 8px; }}
        input {{ width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box; }}
        button {{ width: 100%; padding: 12px; background: #0066cc; color: white; border: none; }}
    </style>
</head>
<body>
    <div class="login-box">
        <h2>{target_brand}</h2>
        <p>Please sign in to continue</p>
        <form action="{redirect_url}" method="POST">
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Sign In</button>
        </form>
    </div>
</body>
</html>"""

    def detect_clone(self, suspicious_url: str, original_url: str,
                     suspicious_html: str = "", original_html: str = "") -> CloneAnalysis:
        """Analyze a URL/page for signs of being a clone of a legitimate site."""
        suspicious = urlparse(suspicious_url)
        original = urlparse(original_url)

        analysis = CloneAnalysis(
            url=suspicious_url,
            original_url=original_url,
            similarity_score=0.0,
        )

        # Domain similarity analysis
        susp_domain = suspicious.hostname or ""
        orig_domain = original.hostname or ""

        # Check for typosquatting
        if self._levenshtein_distance(susp_domain, orig_domain) <= 3 and susp_domain != orig_domain:
            analysis.suspicious_elements.append(
                f"Typosquatting: '{susp_domain}' is similar to '{orig_domain}'"
            )

        # Check for extra subdomains
        if susp_domain.count('.') > orig_domain.count('.'):
            analysis.suspicious_elements.append(
                f"Excessive subdomains: {susp_domain.count('.')} vs {orig_domain.count('.')}"
            )

        # Check for HTTPS
        if suspicious.scheme != 'https':
            analysis.suspicious_elements.append("No HTTPS encryption")

        # Check for IP address instead of domain
        if re.match(r'\d+\.\d+\.\d+\.\d+', susp_domain):
            analysis.suspicious_elements.append("Uses IP address instead of domain name")

        # Check for suspicious TLDs
        suspicious_tlds = ['.xyz', '.top', '.pw', '.cc', '.tk', '.ml']
        if any(susp_domain.endswith(tld) for tld in suspicious_tlds):
            analysis.suspicious_elements.append(f"Suspicious TLD in {susp_domain}")

        # HTML similarity (if provided)
        if suspicious_html and original_html:
            similarity = self._html_similarity(suspicious_html, original_html)
            analysis.similarity_score = similarity
            if similarity > 0.8:
                analysis.suspicious_elements.append(
                    f"High HTML similarity: {similarity:.1%} — likely cloned"
                )

        # Determine risk level
        num_issues = len(analysis.suspicious_elements)
        if num_issues >= 3 or analysis.similarity_score > 0.85:
            analysis.risk_level = "CRITICAL"
        elif num_issues >= 2 or analysis.similarity_score > 0.7:
            analysis.risk_level = "HIGH"
        elif num_issues >= 1:
            analysis.risk_level = "MEDIUM"

        return analysis

    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate edit distance between two strings."""
        if len(s1) < len(s2):
            return PhishingSimulator._levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)

        prev_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (c1 != c2)
                curr_row.append(min(insertions, deletions, substitutions))
            prev_row = curr_row

        return prev_row[-1]

    @staticmethod
    def _html_similarity(html1: str, html2: str) -> float:
        """Simple structural similarity based on tag sequences."""
        tags1 = re.findall(r'<(\w+)', html1.lower())
        tags2 = re.findall(r'<(\w+)', html2.lower())

        if not tags1 or not tags2:
            return 0.0

        # Longest common subsequence ratio
        m, n = len(tags1), len(tags2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if tags1[i - 1] == tags2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        lcs_length = dp[m][n]
        return (2 * lcs_length) / (m + n)

    def generate_report(self, analysis: CloneAnalysis) -> str:
        """Generate a human-readable analysis report."""
        lines = [
            "=" * 50,
            "Phishing Clone Detection Report",
            "=" * 50,
            f"Suspicious URL: {analysis.url}",
            f"Original URL:   {analysis.original_url}",
            f"Risk Level:     {analysis.risk_level}",
            f"Similarity:     {analysis.similarity_score:.1%}",
            "",
        ]

        if analysis.suspicious_elements:
            lines.append("Suspicious Indicators:")
            for elem in analysis.suspicious_elements:
                lines.append(f"  ⚠ {elem}")
        else:
            lines.append("No obvious suspicious indicators found.")

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='Phishing Simulation (Educational)')
    subparsers = parser.add_subparsers(dest='action')

    # Template generation
    gen_parser = subparsers.add_parser('generate-template', help='Generate phishing template')
    gen_parser.add_argument('--type', required=True,
                           choices=['password_reset', 'invoice', 'shared_document', 'account_verification'])
    gen_parser.add_argument('--target-name', default='User')
    gen_parser.add_argument('--phishing-url', default='https://evil.com/login')
    gen_parser.add_argument('--output', help='Output file for template')

    # Clone detection
    detect_parser = subparsers.add_parser('detect-clone', help='Detect cloned landing page')
    detect_parser.add_argument('--url', required=True, help='Suspicious URL')
    detect_parser.add_argument('--original', required=True, help='Original legitimate URL')

    args = parser.parse_args()
    sim = PhishingSimulator()

    if args.action == 'generate-template':
        template = sim.generate_template(
            args.type,
            target_name=args.target_name,
            phishing_url=args.phishing_url,
        )
        print(f"\nPhishing Template: {template.name}")
        print(f"Technique: {template.technique}")
        print(f"Subject: {template.subject}")
        print(f"\nBody:\n{template.body}")
        print(f"\nRed Flags:")
        for indicator in template.indicators:
            print(f"  • {indicator}")

        if args.output:
            with open(args.output, 'w') as f:
                f.write(sim.generate_landing_page("TargetCorp", args.phishing_url))
            print(f"\nLanding page saved to: {args.output}")

    elif args.action == 'detect-clone':
        analysis = sim.detect_clone(args.url, args.original)
        print(sim.generate_report(analysis))

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
