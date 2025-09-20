#!/usr/bin/env python3
"""
Phase 2 Security Audit Script

Performs specific security checks for Phase 2 collaborative editing features
including WebSocket security, user authentication, and data protection.
"""
import argparse
import json
import logging
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Phase2SecurityAuditor:
    """Security auditor for Phase 2 collaborative editing features."""

    def __init__(self):
        self.findings = []
        self.source_paths = [
            "src/jd_ingestion/api/endpoints/",
            "src/jd_ingestion/services/",
            "src/jd_ingestion/database/models.py",
        ]

    def audit_websocket_security(self) -> List[Dict[str, Any]]:
        """Audit WebSocket implementation for security issues."""
        logger.info("Auditing WebSocket security...")
        findings = []

        # Check for WebSocket authentication
        websocket_files = list(Path("src").glob("**/websocket*.py"))

        for file_path in websocket_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                # Check for authentication in WebSocket connections
                if "websocket" in content.lower() and "auth" not in content.lower():
                    findings.append({
                        "severity": "high",
                        "type": "websocket_authentication",
                        "file": str(file_path),
                        "message": "WebSocket endpoint may lack authentication",
                        "line": self._find_line_number(content, "websocket"),
                        "recommendation": "Implement WebSocket authentication middleware"
                    })

                # Check for input validation in WebSocket handlers
                if "json.loads" in content and "validate" not in content:
                    findings.append({
                        "severity": "medium",
                        "type": "input_validation",
                        "file": str(file_path),
                        "message": "WebSocket message handling may lack input validation",
                        "line": self._find_line_number(content, "json.loads"),
                        "recommendation": "Add Pydantic validation for WebSocket messages"
                    })

                # Check for rate limiting
                if "websocket" in content.lower() and "rate" not in content.lower():
                    findings.append({
                        "severity": "medium",
                        "type": "rate_limiting",
                        "file": str(file_path),
                        "message": "WebSocket endpoint may lack rate limiting",
                        "line": 1,
                        "recommendation": "Implement WebSocket rate limiting"
                    })

            except Exception as e:
                logger.warning(f"Error reading {file_path}: {e}")

        return findings

    def audit_translation_memory_security(self) -> List[Dict[str, Any]]:
        """Audit translation memory implementation for security issues."""
        logger.info("Auditing translation memory security...")
        findings = []

        # Check translation memory service
        tm_files = list(Path("src").glob("**/translation_memory*.py"))

        for file_path in tm_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                # Check for SQL injection protection
                if "query" in content and "text(" in content:
                    findings.append({
                        "severity": "high",
                        "type": "sql_injection",
                        "file": str(file_path),
                        "message": "Potential SQL injection risk in translation memory queries",
                        "line": self._find_line_number(content, "text("),
                        "recommendation": "Use parameterized queries and SQLAlchemy ORM"
                    })

                # Check for access control in translation memory
                if "translation" in content and "permission" not in content:
                    findings.append({
                        "severity": "medium",
                        "type": "access_control",
                        "file": str(file_path),
                        "message": "Translation memory may lack access control",
                        "line": 1,
                        "recommendation": "Implement user-based access control for translation projects"
                    })

                # Check for sensitive data in translation memory
                if "password" in content.lower() or "secret" in content.lower():
                    findings.append({
                        "severity": "high",
                        "type": "sensitive_data",
                        "file": str(file_path),
                        "message": "Potential sensitive data in translation memory",
                        "line": self._find_line_number(content, "password"),
                        "recommendation": "Ensure no sensitive data is stored in translation memory"
                    })

            except Exception as e:
                logger.warning(f"Error reading {file_path}: {e}")

        return findings

    def audit_user_authentication(self) -> List[Dict[str, Any]]:
        """Audit user authentication and authorization."""
        logger.info("Auditing user authentication...")
        findings = []

        # Check authentication endpoints
        auth_files = list(Path("src").glob("**/auth*.py")) + list(Path("src").glob("**/user*.py"))

        for file_path in auth_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                # Check for weak password hashing
                if "password" in content and ("md5" in content or "sha1" in content):
                    findings.append({
                        "severity": "high",
                        "type": "weak_crypto",
                        "file": str(file_path),
                        "message": "Weak password hashing algorithm detected",
                        "line": self._find_line_number(content, "md5"),
                        "recommendation": "Use bcrypt, scrypt, or Argon2 for password hashing"
                    })

                # Check for session management
                if "session" in content and "secure" not in content.lower():
                    findings.append({
                        "severity": "medium",
                        "type": "session_security",
                        "file": str(file_path),
                        "message": "Session configuration may lack security flags",
                        "line": self._find_line_number(content, "session"),
                        "recommendation": "Set secure, httpOnly, and sameSite flags for sessions"
                    })

                # Check for JWT security
                if "jwt" in content.lower() and "secret" in content:
                    findings.append({
                        "severity": "medium",
                        "type": "jwt_security",
                        "file": str(file_path),
                        "message": "JWT implementation may have security issues",
                        "line": self._find_line_number(content, "jwt"),
                        "recommendation": "Use strong JWT secrets and proper expiration"
                    })

            except Exception as e:
                logger.warning(f"Error reading {file_path}: {e}")

        return findings

    def audit_data_protection(self) -> List[Dict[str, Any]]:
        """Audit data protection and privacy compliance."""
        logger.info("Auditing data protection...")
        findings = []

        # Check database models for PII
        model_files = list(Path("src").glob("**/models.py"))

        for file_path in model_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                # Check for PII fields without encryption
                pii_patterns = [
                    r'email\s*=.*Column',
                    r'phone\s*=.*Column',
                    r'ssn\s*=.*Column',
                    r'address\s*=.*Column'
                ]

                for pattern in pii_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        findings.append({
                            "severity": "medium",
                            "type": "pii_protection",
                            "file": str(file_path),
                            "message": f"PII field may lack encryption: {match.group()}",
                            "line": line_num,
                            "recommendation": "Consider encrypting PII fields at rest"
                        })

                # Check for audit logging
                if "Column" in content and "audit" not in content.lower():
                    findings.append({
                        "severity": "low",
                        "type": "audit_logging",
                        "file": str(file_path),
                        "message": "Database models may lack audit logging",
                        "line": 1,
                        "recommendation": "Implement audit logging for data changes"
                    })

            except Exception as e:
                logger.warning(f"Error reading {file_path}: {e}")

        return findings

    def audit_api_security(self) -> List[Dict[str, Any]]:
        """Audit API security practices."""
        logger.info("Auditing API security...")
        findings = []

        # Check API endpoints
        api_files = list(Path("src").glob("**/endpoints/*.py"))

        for file_path in api_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                # Check for CORS configuration
                if "router" in content and "cors" not in content.lower():
                    findings.append({
                        "severity": "medium",
                        "type": "cors_configuration",
                        "file": str(file_path),
                        "message": "API endpoint may lack CORS configuration",
                        "line": 1,
                        "recommendation": "Configure CORS properly for production"
                    })

                # Check for input validation
                if "@router.post" in content and "BaseModel" not in content:
                    findings.append({
                        "severity": "medium",
                        "type": "input_validation",
                        "file": str(file_path),
                        "message": "POST endpoint may lack input validation",
                        "line": self._find_line_number(content, "@router.post"),
                        "recommendation": "Use Pydantic models for input validation"
                    })

                # Check for error handling
                if "except" in content and "logger" not in content:
                    findings.append({
                        "severity": "low",
                        "type": "error_handling",
                        "file": str(file_path),
                        "message": "Exception handling may leak sensitive information",
                        "line": self._find_line_number(content, "except"),
                        "recommendation": "Log errors securely without exposing sensitive data"
                    })

            except Exception as e:
                logger.warning(f"Error reading {file_path}: {e}")

        return findings

    def audit_environment_configuration(self) -> List[Dict[str, Any]]:
        """Audit environment and configuration security."""
        logger.info("Auditing environment configuration...")
        findings = []

        # Check for hardcoded secrets
        config_files = list(Path("src").glob("**/config/*.py")) + list(Path("src").glob("**/settings.py"))

        for file_path in config_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                # Check for hardcoded secrets
                secret_patterns = [
                    r'password\s*=\s*["\'][^"\']+["\']',
                    r'secret\s*=\s*["\'][^"\']+["\']',
                    r'key\s*=\s*["\'][^"\']+["\']',
                    r'token\s*=\s*["\'][^"\']+["\']'
                ]

                for pattern in secret_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        if "os.environ" not in match.group() and "getenv" not in match.group():
                            line_num = content[:match.start()].count('\n') + 1
                            findings.append({
                                "severity": "high",
                                "type": "hardcoded_secrets",
                                "file": str(file_path),
                                "message": f"Potential hardcoded secret: {match.group()[:50]}...",
                                "line": line_num,
                                "recommendation": "Use environment variables for secrets"
                            })

                # Check for debug mode in production
                if "debug.*=.*true" in content.lower():
                    findings.append({
                        "severity": "medium",
                        "type": "debug_mode",
                        "file": str(file_path),
                        "message": "Debug mode may be enabled",
                        "line": self._find_line_number(content, "debug"),
                        "recommendation": "Ensure debug mode is disabled in production"
                    })

            except Exception as e:
                logger.warning(f"Error reading {file_path}: {e}")

        return findings

    def _find_line_number(self, content: str, search_term: str) -> int:
        """Find line number of first occurrence of search term."""
        try:
            index = content.lower().find(search_term.lower())
            if index != -1:
                return content[:index].count('\n') + 1
        except:
            pass
        return 1

    def run_audit(self) -> Dict[str, Any]:
        """Run complete Phase 2 security audit."""
        logger.info("Starting Phase 2 security audit...")

        # Collect all findings
        all_findings = []
        all_findings.extend(self.audit_websocket_security())
        all_findings.extend(self.audit_translation_memory_security())
        all_findings.extend(self.audit_user_authentication())
        all_findings.extend(self.audit_data_protection())
        all_findings.extend(self.audit_api_security())
        all_findings.extend(self.audit_environment_configuration())

        # Categorize findings by severity
        high_severity = [f for f in all_findings if f["severity"] == "high"]
        medium_severity = [f for f in all_findings if f["severity"] == "medium"]
        low_severity = [f for f in all_findings if f["severity"] == "low"]

        # Generate summary
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_findings": len(all_findings),
            "high_severity_count": len(high_severity),
            "medium_severity_count": len(medium_severity),
            "low_severity_count": len(low_severity),
            "findings": all_findings,
            "summary_by_type": self._summarize_by_type(all_findings),
            "recommendations": self._generate_recommendations(all_findings)
        }

        logger.info(f"Security audit completed: {len(all_findings)} findings ({len(high_severity)} high, {len(medium_severity)} medium, {len(low_severity)} low)")

        return summary

    def _summarize_by_type(self, findings: List[Dict[str, Any]]) -> Dict[str, int]:
        """Summarize findings by type."""
        type_counts = {}
        for finding in findings:
            finding_type = finding["type"]
            type_counts[finding_type] = type_counts.get(finding_type, 0) + 1
        return type_counts

    def _generate_recommendations(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate prioritized security recommendations."""
        recommendations = []

        high_severity = [f for f in findings if f["severity"] == "high"]

        if high_severity:
            recommendations.append("🚨 CRITICAL: Address all high-severity findings immediately")

        # Count common issues
        common_issues = {}
        for finding in findings:
            issue_type = finding["type"]
            common_issues[issue_type] = common_issues.get(issue_type, 0) + 1

        # Generate specific recommendations
        if common_issues.get("input_validation", 0) > 0:
            recommendations.append("Implement comprehensive input validation using Pydantic models")

        if common_issues.get("access_control", 0) > 0:
            recommendations.append("Review and strengthen access control mechanisms")

        if common_issues.get("websocket_authentication", 0) > 0:
            recommendations.append("Implement proper WebSocket authentication and authorization")

        if common_issues.get("hardcoded_secrets", 0) > 0:
            recommendations.append("Move all secrets to environment variables")

        return recommendations


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Phase 2 Security Audit")
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output file for security audit results (JSON)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run security audit
    auditor = Phase2SecurityAuditor()
    results = auditor.run_audit()

    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Security audit results saved to {args.output}")

    # Print summary
    print(f"\n🔒 Phase 2 Security Audit Summary")
    print(f"Total findings: {results['total_findings']}")
    print(f"High severity: {results['high_severity_count']}")
    print(f"Medium severity: {results['medium_severity_count']}")
    print(f"Low severity: {results['low_severity_count']}")

    if results['recommendations']:
        print(f"\n📋 Key Recommendations:")
        for rec in results['recommendations']:
            print(f"  • {rec}")


if __name__ == "__main__":
    main()