#!/usr/bin/env python3
"""
Security Thresholds Checker

Checks security scan results against predefined thresholds and fails
the CI pipeline if security standards are not met.
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityThresholdChecker:
    """Checks security scan results against configured thresholds."""

    def __init__(self):
        self.thresholds = {
            "security_score_minimum": 75.0,
            "max_high_severity": 0,
            "max_medium_severity": 5,
            "max_critical_vulnerabilities": 0,
            "max_total_findings": 20,
            "required_tools": ["trivy", "bandit", "phase2_audit"]
        }
        self.violations = []

    def load_security_summary(self, file_path: Path) -> Dict[str, Any]:
        """Load security summary from JSON file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Security summary file not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in security summary: {e}")
            return {}

    def check_security_score(self, summary: Dict[str, Any]) -> bool:
        """Check if security score meets minimum threshold."""
        security_score = summary.get("summary", {}).get("security_score", 0)
        min_score = self.thresholds["security_score_minimum"]

        if security_score < min_score:
            self.violations.append({
                "type": "security_score",
                "severity": "high",
                "message": f"Security score {security_score:.1f} is below minimum threshold of {min_score}",
                "current_value": security_score,
                "threshold": min_score
            })
            return False

        logger.info(f"✅ Security score {security_score:.1f} meets minimum threshold")
        return True

    def check_high_severity_findings(self, summary: Dict[str, Any]) -> bool:
        """Check high severity findings across all tools."""
        high_severity_count = 0

        # Count high severity findings from all tools
        for tool_name, tool_data in summary.get("tool_results", {}).items():
            if tool_name == "bandit":
                high_severity_count += len([
                    issue for issue in tool_data.get("issues", [])
                    if issue.get("severity", "").upper() == "HIGH"
                ])
            elif tool_name == "phase2_audit":
                high_severity_count += tool_data.get("high_severity_count", 0)
            elif tool_name == "trivy":
                high_severity_count += len([
                    vuln for vuln in tool_data.get("vulnerabilities", [])
                    if vuln.get("level") == "error"
                ])

        max_high = self.thresholds["max_high_severity"]

        if high_severity_count > max_high:
            self.violations.append({
                "type": "high_severity_findings",
                "severity": "high",
                "message": f"Found {high_severity_count} high-severity findings, maximum allowed: {max_high}",
                "current_value": high_severity_count,
                "threshold": max_high
            })
            return False

        logger.info(f"✅ High severity findings ({high_severity_count}) within acceptable threshold")
        return True

    def check_medium_severity_findings(self, summary: Dict[str, Any]) -> bool:
        """Check medium severity findings across all tools."""
        medium_severity_count = 0

        # Count medium severity findings from all tools
        for tool_name, tool_data in summary.get("tool_results", {}).items():
            if tool_name == "bandit":
                medium_severity_count += len([
                    issue for issue in tool_data.get("issues", [])
                    if issue.get("severity", "").upper() == "MEDIUM"
                ])
            elif tool_name == "phase2_audit":
                medium_severity_count += tool_data.get("medium_severity_count", 0)
            elif tool_name == "trivy":
                medium_severity_count += len([
                    vuln for vuln in tool_data.get("vulnerabilities", [])
                    if vuln.get("level") == "warning"
                ])

        max_medium = self.thresholds["max_medium_severity"]

        if medium_severity_count > max_medium:
            self.violations.append({
                "type": "medium_severity_findings",
                "severity": "medium",
                "message": f"Found {medium_severity_count} medium-severity findings, maximum allowed: {max_medium}",
                "current_value": medium_severity_count,
                "threshold": max_medium
            })
            return False

        logger.info(f"✅ Medium severity findings ({medium_severity_count}) within acceptable threshold")
        return True

    def check_critical_vulnerabilities(self, summary: Dict[str, Any]) -> bool:
        """Check for critical vulnerabilities that must be zero."""
        critical_count = 0

        # Count critical vulnerabilities
        for tool_name, tool_data in summary.get("tool_results", {}).items():
            if tool_name == "safety":
                critical_count += len([
                    vuln for vuln in tool_data.get("vulnerabilities", [])
                    if vuln.get("severity", "").lower() == "critical"
                ])
            elif tool_name == "npm_audit":
                critical_count += len([
                    vuln for vuln in tool_data.get("vulnerabilities", [])
                    if vuln.get("severity", "").lower() == "critical"
                ])

        max_critical = self.thresholds["max_critical_vulnerabilities"]

        if critical_count > max_critical:
            self.violations.append({
                "type": "critical_vulnerabilities",
                "severity": "critical",
                "message": f"Found {critical_count} critical vulnerabilities, maximum allowed: {max_critical}",
                "current_value": critical_count,
                "threshold": max_critical
            })
            return False

        logger.info(f"✅ Critical vulnerabilities ({critical_count}) within acceptable threshold")
        return True

    def check_total_findings(self, summary: Dict[str, Any]) -> bool:
        """Check total number of security findings."""
        total_findings = summary.get("summary", {}).get("total_findings", 0)
        max_total = self.thresholds["max_total_findings"]

        if total_findings > max_total:
            self.violations.append({
                "type": "total_findings",
                "severity": "medium",
                "message": f"Total security findings ({total_findings}) exceeds maximum threshold ({max_total})",
                "current_value": total_findings,
                "threshold": max_total
            })
            return False

        logger.info(f"✅ Total findings ({total_findings}) within acceptable threshold")
        return True

    def check_required_tools(self, summary: Dict[str, Any]) -> bool:
        """Check that all required security tools were run."""
        tools_used = summary.get("summary", {}).get("tools_used", [])
        required_tools = self.thresholds["required_tools"]

        missing_tools = set(required_tools) - set(tools_used)

        if missing_tools:
            self.violations.append({
                "type": "missing_tools",
                "severity": "medium",
                "message": f"Required security tools not run: {', '.join(missing_tools)}",
                "current_value": tools_used,
                "threshold": required_tools
            })
            return False

        logger.info(f"✅ All required security tools were executed")
        return True

    def check_compliance_status(self, summary: Dict[str, Any]) -> bool:
        """Check compliance with security standards."""
        compliance = summary.get("compliance", {})
        failed_standards = []

        for standard, status in compliance.items():
            if not status.get("compliant", True):
                failed_standards.append(standard)

        if failed_standards:
            self.violations.append({
                "type": "compliance_failure",
                "severity": "high",
                "message": f"Failed compliance standards: {', '.join(failed_standards)}",
                "current_value": failed_standards,
                "threshold": "All standards must be compliant"
            })
            return False

        logger.info(f"✅ All compliance standards met")
        return True

    def check_thresholds(self, security_summary: Dict[str, Any]) -> bool:
        """Check all security thresholds."""
        logger.info("Checking security thresholds...")

        checks = [
            self.check_security_score(security_summary),
            self.check_high_severity_findings(security_summary),
            self.check_medium_severity_findings(security_summary),
            self.check_critical_vulnerabilities(security_summary),
            self.check_total_findings(security_summary),
            self.check_required_tools(security_summary),
            self.check_compliance_status(security_summary)
        ]

        all_passed = all(checks)

        if not all_passed:
            logger.error(f"❌ Security threshold checks failed: {len(self.violations)} violations")
        else:
            logger.info("✅ All security threshold checks passed")

        return all_passed

    def generate_violation_report(self) -> str:
        """Generate a detailed report of threshold violations."""
        if not self.violations:
            return "✅ All security thresholds met - no violations found."

        report = []
        report.append("❌ Security Threshold Violations Report")
        report.append("=" * 50)

        # Group violations by severity
        critical_violations = [v for v in self.violations if v["severity"] == "critical"]
        high_violations = [v for v in self.violations if v["severity"] == "high"]
        medium_violations = [v for v in self.violations if v["severity"] == "medium"]

        if critical_violations:
            report.append("\n🚨 CRITICAL VIOLATIONS:")
            for violation in critical_violations:
                report.append(f"  • {violation['message']}")

        if high_violations:
            report.append("\n⚠️ HIGH SEVERITY VIOLATIONS:")
            for violation in high_violations:
                report.append(f"  • {violation['message']}")

        if medium_violations:
            report.append("\n⚡ MEDIUM SEVERITY VIOLATIONS:")
            for violation in medium_violations:
                report.append(f"  • {violation['message']}")

        report.append("\n📋 RECOMMENDED ACTIONS:")
        if critical_violations or high_violations:
            report.append("  1. Address all critical and high-severity violations immediately")
            report.append("  2. Do not deploy until these issues are resolved")

        if medium_violations:
            report.append("  3. Plan to address medium-severity violations in next sprint")

        report.append("  4. Review security scanning configuration")
        report.append("  5. Consider tightening security thresholds after remediation")

        return "\n".join(report)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Check security scan results against thresholds")
    parser.add_argument(
        "--security-summary",
        type=Path,
        required=True,
        help="Path to security summary JSON file"
    )
    parser.add_argument(
        "--fail-on-high",
        action="store_true",
        help="Exit with error code if high-severity violations are found"
    )
    parser.add_argument(
        "--fail-on-medium",
        action="store_true",
        help="Exit with error code if medium-severity violations are found"
    )
    parser.add_argument(
        "--custom-thresholds",
        type=Path,
        help="Path to custom thresholds JSON file"
    )

    args = parser.parse_args()

    # Initialize checker
    checker = SecurityThresholdChecker()

    # Load custom thresholds if provided
    if args.custom_thresholds and args.custom_thresholds.exists():
        try:
            with open(args.custom_thresholds, 'r') as f:
                custom_thresholds = json.load(f)
                checker.thresholds.update(custom_thresholds)
                logger.info(f"Loaded custom thresholds from {args.custom_thresholds}")
        except Exception as e:
            logger.warning(f"Failed to load custom thresholds: {e}")

    # Load security summary
    security_summary = checker.load_security_summary(args.security_summary)
    if not security_summary:
        logger.error("Failed to load security summary")
        sys.exit(1)

    # Check thresholds
    passed = checker.check_thresholds(security_summary)

    # Generate and display violation report
    violation_report = checker.generate_violation_report()
    print(violation_report)

    # Determine exit code
    exit_code = 0

    if not passed:
        has_critical = any(v["severity"] == "critical" for v in checker.violations)
        has_high = any(v["severity"] == "high" for v in checker.violations)
        has_medium = any(v["severity"] == "medium" for v in checker.violations)

        if has_critical:
            logger.error("Critical security violations found - failing build")
            exit_code = 1
        elif has_high and args.fail_on_high:
            logger.error("High-severity security violations found - failing build")
            exit_code = 1
        elif has_medium and args.fail_on_medium:
            logger.error("Medium-severity security violations found - failing build")
            exit_code = 1
        else:
            logger.warning("Security violations found but not configured to fail build")

    logger.info(f"Security threshold check completed with exit code: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()