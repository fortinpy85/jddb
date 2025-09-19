"""
Compliance testing configuration and fixtures.

Provides common fixtures and configuration for government compliance testing.
"""

import pytest
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta


@pytest.fixture
def government_security_config():
    """Configuration for government security requirements."""
    return {
        "encryption": {
            "algorithm": "AES-256-GCM",
            "key_size": 256,
            "tls_version": "1.3"
        },
        "authentication": {
            "mfa_required": True,
            "password_min_length": 12,
            "session_timeout": 30,  # minutes
            "max_failed_attempts": 5
        },
        "audit": {
            "retention_years": 7,
            "real_time_monitoring": True,
            "integrity_checking": True
        },
        "privacy": {
            "pii_detection": True,
            "data_masking": True,
            "consent_management": True,
            "data_retention_policies": True
        }
    }


@pytest.fixture
def mock_audit_logger():
    """Mock audit logger for compliance testing."""
    logger = Mock()
    logger.log_event = Mock(return_value=True)
    logger.log_security_event = Mock(return_value=True)
    logger.log_privacy_event = Mock(return_value=True)
    return logger


@pytest.fixture
def mock_auth_service():
    """Mock authentication service for compliance testing."""
    auth_service = Mock()
    auth_service.authenticate = Mock(return_value={"success": True, "user_id": "test_user"})
    auth_service.verify_mfa = Mock(return_value=True)
    auth_service.check_session = Mock(return_value=True)
    auth_service.logout = Mock(return_value=True)
    return auth_service


@pytest.fixture
def sample_job_description():
    """Sample job description for compliance testing."""
    return {
        "id": "job_123",
        "title": "Director, Strategic Planning",
        "classification": "PROTECTED_B",
        "content": """
        GENERAL ACCOUNTABILITY:
        The Director is responsible for strategic planning initiatives
        and reports to the Deputy Minister.

        SPECIFIC ACCOUNTABILITIES:
        - Lead strategic planning processes
        - Manage team of 5 analysts
        - Budget authority of $2.5M annually

        QUALIFICATIONS:
        - Master's degree in relevant field
        - 10+ years of government experience
        - Valid security clearance required
        """,
        "metadata": {
            "department": "Strategic Policy",
            "security_clearance": "PROTECTED_B",
            "created_by": "hr_user",
            "created_at": datetime.now(),
            "last_modified": datetime.now()
        }
    }


@pytest.fixture
def compliance_test_data():
    """Test data for compliance scenarios."""
    return {
        "users": [
            {
                "id": "user_1",
                "username": "john.doe",
                "clearance": "PROTECTED_B",
                "department": "HR",
                "mfa_enabled": True
            },
            {
                "id": "user_2",
                "username": "jane.smith",
                "clearance": "SECRET",
                "department": "Security",
                "mfa_enabled": True
            }
        ],
        "documents": [
            {
                "id": "doc_1",
                "classification": "PROTECTED_A",
                "content": "Lower classification content"
            },
            {
                "id": "doc_2",
                "classification": "SECRET",
                "content": "Higher classification content"
            }
        ],
        "audit_events": [
            {
                "timestamp": datetime.now(),
                "user_id": "user_1",
                "action": "document_access",
                "resource": "doc_1",
                "result": "success"
            },
            {
                "timestamp": datetime.now() - timedelta(hours=1),
                "user_id": "user_2",
                "action": "failed_login",
                "resource": "authentication",
                "result": "failure"
            }
        ]
    }


@pytest.fixture
def privacy_test_scenarios():
    """Test scenarios for privacy compliance."""
    return {
        "pii_examples": {
            "emails": ["john.doe@gc.ca", "user@department.gov.ca"],
            "phones": ["(613) 555-1234", "613-555-5678"],
            "names": ["John Doe", "Marie Tremblay"],
            "addresses": ["123 Main St, Ottawa, ON"]
        },
        "consent_scenarios": [
            {
                "user_id": "user_1",
                "consent_type": "data_processing",
                "consent_given": True,
                "consent_date": datetime.now(),
                "can_withdraw": True
            }
        ],
        "retention_policies": {
            "audit_logs": 7 * 365,  # 7 years in days
            "user_data": 5 * 365,   # 5 years in days
            "temp_files": 90        # 90 days
        }
    }


@pytest.fixture
def security_test_scenarios():
    """Test scenarios for security compliance."""
    return {
        "clearance_hierarchy": {
            "UNCLASSIFIED": 0,
            "PROTECTED_A": 1,
            "PROTECTED_B": 2,
            "PROTECTED_C": 3,
            "CONFIDENTIAL": 4,
            "SECRET": 5,
            "TOP_SECRET": 6
        },
        "attack_scenarios": [
            {
                "type": "brute_force",
                "description": "Multiple failed login attempts",
                "indicators": ["repeated_failed_logins", "source_ip_patterns"]
            },
            {
                "type": "privilege_escalation",
                "description": "Attempt to access higher classified documents",
                "indicators": ["access_denied", "clearance_insufficient"]
            }
        ],
        "encryption_requirements": {
            "algorithms": ["AES-256-GCM", "ChaCha20-Poly1305"],
            "key_sizes": [256, 384],
            "tls_versions": ["1.2", "1.3"]
        }
    }


def pytest_configure(config):
    """Configure pytest for compliance testing."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "compliance: mark test as compliance test"
    )
    config.addinivalue_line(
        "markers", "privacy: mark test as privacy compliance test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security compliance test"
    )
    config.addinivalue_line(
        "markers", "itsg33: mark test as ITSG-33 compliance test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection for compliance testing."""
    # Add compliance marker to all tests in compliance directory
    for item in items:
        if "compliance" in str(item.fspath):
            item.add_marker(pytest.mark.compliance)


@pytest.fixture
def compliance_report_generator():
    """Generate compliance reports for test results."""
    def generate_report(test_results: Dict[str, Any]) -> str:
        """Generate a compliance test report."""
        report = []
        report.append("GOVERNMENT OF CANADA - COMPLIANCE TEST REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")

        for category, results in test_results.items():
            report.append(f"{category.upper()} COMPLIANCE:")
            report.append("-" * 30)

            for test_name, result in results.items():
                status = "✅ PASS" if result["passed"] else "❌ FAIL"
                report.append(f"  {status} {test_name}")

                if not result["passed"] and "error" in result:
                    report.append(f"      Error: {result['error']}")

            report.append("")

        return "\n".join(report)

    return generate_report