#!/usr/bin/env python3
"""
Security Report Generator

Aggregates results from multiple security scanning tools and generates
a comprehensive security report for the JDDB application.
"""
import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityReportGenerator:
    """Generates comprehensive security reports from multiple scanning tools."""

    def __init__(self):
        self.report_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {},
            "findings": [],
            "tool_results": {},
            "recommendations": [],
            "compliance": {}
        }

    def load_trivy_results(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse Trivy SARIF results."""
        if not file_path.exists():
            logger.warning(f"Trivy results file not found: {file_path}")
            return {}

        try:
            with open(file_path, 'r') as f:
                sarif_data = json.load(f)

            vulnerabilities = []
            if 'runs' in sarif_data:
                for run in sarif_data['runs']:
                    if 'results' in run:
                        for result in run['results']:
                            vulnerabilities.append({
                                "rule_id": result.get('ruleId', 'unknown'),
                                "level": result.get('level', 'note'),
                                "message": result.get('message', {}).get('text', ''),
                                "locations": result.get('locations', [])
                            })

            return {
                "tool": "trivy",
                "vulnerabilities": vulnerabilities,
                "count": len(vulnerabilities)
            }

        except Exception as e:
            logger.error(f"Error parsing Trivy results: {e}")
            return {}

    def load_safety_results(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse Safety check results."""
        if not file_path.exists():
            logger.warning(f"Safety results file not found: {file_path}")
            return {}

        try:
            with open(file_path, 'r') as f:
                safety_data = json.load(f)

            vulnerabilities = []
            for vuln in safety_data:
                vulnerabilities.append({
                    "package": vuln.get('package_name', ''),
                    "version": vuln.get('analyzed_version', ''),
                    "vulnerability_id": vuln.get('vulnerability_id', ''),
                    "advisory": vuln.get('advisory', ''),
                    "severity": vuln.get('severity', 'unknown')
                })

            return {
                "tool": "safety",
                "vulnerabilities": vulnerabilities,
                "count": len(vulnerabilities)
            }

        except Exception as e:
            logger.error(f"Error parsing Safety results: {e}")
            return {}

    def load_bandit_results(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse Bandit results."""
        if not file_path.exists():
            logger.warning(f"Bandit results file not found: {file_path}")
            return {}

        try:
            with open(file_path, 'r') as f:
                bandit_data = json.load(f)

            issues = []
            for result in bandit_data.get('results', []):
                issues.append({
                    "test_id": result.get('test_id', ''),
                    "test_name": result.get('test_name', ''),
                    "severity": result.get('issue_severity', 'low'),
                    "confidence": result.get('issue_confidence', 'low'),
                    "filename": result.get('filename', ''),
                    "line_number": result.get('line_number', 0),
                    "issue_text": result.get('issue_text', '')
                })

            return {
                "tool": "bandit",
                "issues": issues,
                "count": len(issues),
                "metrics": bandit_data.get('metrics', {})
            }

        except Exception as e:
            logger.error(f"Error parsing Bandit results: {e}")
            return {}

    def load_semgrep_results(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse Semgrep results."""
        if not file_path.exists():
            logger.warning(f"Semgrep results file not found: {file_path}")
            return {}

        try:
            with open(file_path, 'r') as f:
                semgrep_data = json.load(f)

            findings = []
            for result in semgrep_data.get('results', []):
                findings.append({
                    "check_id": result.get('check_id', ''),
                    "message": result.get('message', ''),
                    "severity": result.get('extra', {}).get('severity', 'info'),
                    "path": result.get('path', ''),
                    "start_line": result.get('start', {}).get('line', 0),
                    "end_line": result.get('end', {}).get('line', 0)
                })

            return {
                "tool": "semgrep",
                "findings": findings,
                "count": len(findings)
            }

        except Exception as e:
            logger.error(f"Error parsing Semgrep results: {e}")
            return {}

    def load_npm_audit_results(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse npm audit results."""
        if not file_path.exists():
            logger.warning(f"npm audit results file not found: {file_path}")
            return {}

        try:
            with open(file_path, 'r') as f:
                npm_data = json.load(f)

            vulnerabilities = []
            if 'vulnerabilities' in npm_data:
                for package, vuln_data in npm_data['vulnerabilities'].items():
                    vulnerabilities.append({
                        "package": package,
                        "severity": vuln_data.get('severity', 'unknown'),
                        "range": vuln_data.get('range', ''),
                        "via": vuln_data.get('via', [])
                    })

            return {
                "tool": "npm_audit",
                "vulnerabilities": vulnerabilities,
                "count": len(vulnerabilities),
                "metadata": npm_data.get('metadata', {})
            }

        except Exception as e:
            logger.error(f"Error parsing npm audit results: {e}")
            return {}

    def load_eslint_security_results(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse ESLint security results."""
        if not file_path.exists():
            logger.warning(f"ESLint security results file not found: {file_path}")
            return {}

        try:
            with open(file_path, 'r') as f:
                eslint_data = json.load(f)

            issues = []
            for file_result in eslint_data:
                for message in file_result.get('messages', []):
                    if 'security' in message.get('ruleId', '').lower():
                        issues.append({
                            "file": file_result.get('filePath', ''),
                            "rule_id": message.get('ruleId', ''),
                            "severity": message.get('severity', 1),
                            "message": message.get('message', ''),
                            "line": message.get('line', 0),
                            "column": message.get('column', 0)
                        })

            return {
                "tool": "eslint_security",
                "issues": issues,
                "count": len(issues)
            }

        except Exception as e:
            logger.error(f"Error parsing ESLint security results: {e}")
            return {}

    def load_phase2_audit_results(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse Phase 2 specific audit results."""
        if not file_path.exists():
            logger.warning(f"Phase 2 audit results file not found: {file_path}")
            return {}

        try:
            with open(file_path, 'r') as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"Error parsing Phase 2 audit results: {e}")
            return {}

    def calculate_security_score(self) -> float:
        """Calculate overall security score based on findings."""
        total_score = 100.0

        # Deduct points based on severity and tool findings
        for tool_name, tool_data in self.report_data["tool_results"].items():
            if tool_name == "trivy":
                # Deduct points for container vulnerabilities
                critical_count = len([v for v in tool_data.get('vulnerabilities', []) if v.get('level') == 'error'])
                high_count = len([v for v in tool_data.get('vulnerabilities', []) if v.get('level') == 'warning'])
                total_score -= (critical_count * 10) + (high_count * 5)

            elif tool_name == "bandit":
                # Deduct points for code security issues
                high_issues = len([i for i in tool_data.get('issues', []) if i.get('severity') == 'HIGH'])
                medium_issues = len([i for i in tool_data.get('issues', []) if i.get('severity') == 'MEDIUM'])
                total_score -= (high_issues * 8) + (medium_issues * 3)

            elif tool_name == "phase2_audit":
                # Deduct points for Phase 2 specific issues
                high_findings = tool_data.get('high_severity_count', 0)
                medium_findings = tool_data.get('medium_severity_count', 0)
                total_score -= (high_findings * 12) + (medium_findings * 4)

        return max(0.0, min(100.0, total_score))

    def generate_recommendations(self) -> List[str]:
        """Generate security recommendations based on findings."""
        recommendations = []

        # Check tool results for common issues
        for tool_name, tool_data in self.report_data["tool_results"].items():
            if tool_name == "bandit" and tool_data.get('count', 0) > 0:
                recommendations.append("Review and fix Python code security issues identified by Bandit")

            elif tool_name == "safety" and tool_data.get('count', 0) > 0:
                recommendations.append("Update Python dependencies with known vulnerabilities")

            elif tool_name == "npm_audit" and tool_data.get('count', 0) > 0:
                recommendations.append("Update Node.js dependencies with security vulnerabilities")

            elif tool_name == "phase2_audit":
                phase2_recs = tool_data.get('recommendations', [])
                recommendations.extend(phase2_recs)

        # Add general security recommendations
        if not recommendations:
            recommendations.append("No critical security issues found - maintain current security practices")
        else:
            recommendations.insert(0, "Address high-severity findings immediately")

        return list(set(recommendations))  # Remove duplicates

    def assess_compliance(self) -> Dict[str, Any]:
        """Assess compliance with security standards."""
        compliance = {
            "OWASP_Top_10": {
                "compliant": True,
                "issues": []
            },
            "Government_Security": {
                "compliant": True,
                "issues": []
            },
            "ITSG-33": {
                "compliant": True,
                "issues": []
            }
        }

        # Check for common OWASP issues
        for tool_name, tool_data in self.report_data["tool_results"].items():
            if tool_name == "bandit":
                for issue in tool_data.get('issues', []):
                    if any(keyword in issue.get('test_name', '').lower()
                           for keyword in ['sql_injection', 'xss', 'hardcoded_password']):
                        compliance["OWASP_Top_10"]["compliant"] = False
                        compliance["OWASP_Top_10"]["issues"].append(issue.get('test_name', ''))

            elif tool_name == "phase2_audit":
                high_findings = tool_data.get('high_severity_count', 0)
                if high_findings > 0:
                    compliance["Government_Security"]["compliant"] = False
                    compliance["Government_Security"]["issues"].append(f"{high_findings} high-severity findings")

        return compliance

    def generate_report(self, **file_paths) -> Dict[str, Any]:
        """Generate comprehensive security report."""
        logger.info("Generating security report...")

        # Load results from all tools
        if file_paths.get('trivy'):
            self.report_data["tool_results"]["trivy"] = self.load_trivy_results(Path(file_paths['trivy']))

        if file_paths.get('safety'):
            self.report_data["tool_results"]["safety"] = self.load_safety_results(Path(file_paths['safety']))

        if file_paths.get('bandit'):
            self.report_data["tool_results"]["bandit"] = self.load_bandit_results(Path(file_paths['bandit']))

        if file_paths.get('semgrep'):
            self.report_data["tool_results"]["semgrep"] = self.load_semgrep_results(Path(file_paths['semgrep']))

        if file_paths.get('npm_audit'):
            self.report_data["tool_results"]["npm_audit"] = self.load_npm_audit_results(Path(file_paths['npm_audit']))

        if file_paths.get('eslint'):
            self.report_data["tool_results"]["eslint_security"] = self.load_eslint_security_results(Path(file_paths['eslint']))

        if file_paths.get('phase2_audit'):
            self.report_data["tool_results"]["phase2_audit"] = self.load_phase2_audit_results(Path(file_paths['phase2_audit']))

        # Calculate summary metrics
        total_findings = sum(
            tool_data.get('count', len(tool_data.get('vulnerabilities', tool_data.get('issues', tool_data.get('findings', [])))))
            for tool_data in self.report_data["tool_results"].values()
        )

        self.report_data["summary"] = {
            "total_findings": total_findings,
            "security_score": self.calculate_security_score(),
            "tools_used": list(self.report_data["tool_results"].keys()),
            "scan_date": datetime.utcnow().isoformat()
        }

        # Generate recommendations and compliance assessment
        self.report_data["recommendations"] = self.generate_recommendations()
        self.report_data["compliance"] = self.assess_compliance()

        logger.info(f"Security report generated: {total_findings} total findings, security score: {self.report_data['summary']['security_score']:.1f}")

        return self.report_data


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Generate comprehensive security report")
    parser.add_argument("--trivy", type=str, help="Trivy SARIF results file")
    parser.add_argument("--safety", type=str, help="Safety JSON results file")
    parser.add_argument("--bandit", type=str, help="Bandit JSON results file")
    parser.add_argument("--semgrep", type=str, help="Semgrep JSON results file")
    parser.add_argument("--npm-audit", type=str, help="npm audit JSON results file")
    parser.add_argument("--eslint", type=str, help="ESLint security JSON results file")
    parser.add_argument("--phase2-audit", type=str, help="Phase 2 audit JSON results file")
    parser.add_argument("--output", type=str, required=True, help="Output file for security report")

    args = parser.parse_args()

    # Generate report
    generator = SecurityReportGenerator()
    report = generator.generate_report(
        trivy=args.trivy,
        safety=args.safety,
        bandit=args.bandit,
        semgrep=args.semgrep,
        npm_audit=args.npm_audit,
        eslint=args.eslint,
        phase2_audit=args.phase2_audit
    )

    # Save report
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)

    # Print summary
    print(f"\n🔒 Security Report Summary")
    print(f"Total findings: {report['summary']['total_findings']}")
    print(f"Security score: {report['summary']['security_score']:.1f}/100")
    print(f"Tools used: {', '.join(report['summary']['tools_used'])}")

    if report['recommendations']:
        print(f"\n📋 Key Recommendations:")
        for rec in report['recommendations'][:5]:  # Show top 5
            print(f"  • {rec}")

    logger.info(f"Security report saved to {args.output}")


if __name__ == "__main__":
    main()
