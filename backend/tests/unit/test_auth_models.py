"""Tests for auth/models.py module."""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from jd_ingestion.auth.models import (
    User,
    UserSession,
    UserPreference,
    UserPermission,
    hash_password,
    verify_password,
    pwd_context,
)


class TestUser:
    """Test the User model."""

    @pytest.fixture
    def sample_user_data(self):
        """Create sample user data."""
        return {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": "hashed_password",
            "first_name": "Test",
            "last_name": "User",
            "role": "user",
            "department": "IT",
            "security_clearance": "Level 1",
            "preferred_language": "en",
            "is_active": True,
            "last_login": datetime.utcnow() - timedelta(hours=1),
            "created_at": datetime.utcnow() - timedelta(days=30),
            "updated_at": datetime.utcnow() - timedelta(hours=2),
        }

    def test_user_creation(self, sample_user_data):
        """Test creating a User instance."""
        user = User(**sample_user_data)

        assert user.id == 1
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.role == "user"
        assert user.is_active is True

    def test_user_minimal_data(self):
        """Test creating a User with minimal required data."""
        user_data = {
            "id": 2,
            "username": "minimal",
            "email": "minimal@example.com",
            "password_hash": "hash123",
            "created_at": datetime.utcnow(),
        }

        user = User(**user_data)

        assert user.id == 2
        assert user.username == "minimal"
        assert user.role == "user"  # Default value
        assert user.preferred_language == "en"  # Default value
        assert user.is_active is True  # Default value
        assert user.first_name is None
        assert user.last_name is None

    def test_user_validation_errors(self):
        """Test validation errors when creating User."""
        # Missing required fields
        with pytest.raises(ValidationError):
            User(id=1, username="test")

        # Invalid email format
        with pytest.raises(ValidationError):
            User(
                id=1,
                username="test",
                email="invalid-email",
                password_hash="hash",
                created_at=datetime.utcnow(),
            )

        # Invalid data types
        with pytest.raises(ValidationError):
            User(
                id="not_an_int",  # Should be int
                username="test",
                email="test@example.com",
                password_hash="hash",
                created_at=datetime.utcnow(),
            )

    def test_set_password(self, sample_user_data):
        """Test password hashing."""
        user = User(**sample_user_data)
        password = "test_password123"

        hashed = user.set_password(password)

        assert isinstance(hashed, str)
        assert hashed != password  # Should be hashed
        assert len(hashed) > 20  # Bcrypt hashes are typically 60 chars

    def test_verify_password_success(self, sample_user_data):
        """Test successful password verification."""
        password = "test_password123"
        # Create a proper hash for testing
        password_hash = pwd_context.hash(password)
        sample_user_data["password_hash"] = password_hash

        user = User(**sample_user_data)

        assert user.verify_password(password) is True

    def test_verify_password_failure(self, sample_user_data):
        """Test failed password verification."""
        correct_password = "correct_password"
        wrong_password = "wrong_password"
        password_hash = pwd_context.hash(correct_password)
        sample_user_data["password_hash"] = password_hash

        user = User(**sample_user_data)

        assert user.verify_password(wrong_password) is False

    def test_full_name_property(self, sample_user_data):
        """Test the full_name property."""
        user = User(**sample_user_data)

        # With both first and last name
        assert user.full_name == "Test User"

        # Without last name
        sample_user_data["last_name"] = None
        user = User(**sample_user_data)
        assert user.full_name == "testuser"

        # Without first name
        sample_user_data["first_name"] = None
        sample_user_data["last_name"] = "User"
        user = User(**sample_user_data)
        assert user.full_name == "testuser"

        # Without both names
        sample_user_data["first_name"] = None
        sample_user_data["last_name"] = None
        user = User(**sample_user_data)
        assert user.full_name == "testuser"

    def test_is_admin_property(self, sample_user_data):
        """Test the is_admin property."""
        # Regular user
        user = User(**sample_user_data)
        assert user.is_admin is False

        # Admin user
        sample_user_data["role"] = "admin"
        user = User(**sample_user_data)
        assert user.is_admin is True

        # Other roles
        for role in ["editor", "reviewer", "translator"]:
            sample_user_data["role"] = role
            user = User(**sample_user_data)
            assert user.is_admin is False

    def test_can_edit_property(self, sample_user_data):
        """Test the can_edit property."""
        # Roles that can edit
        for role in ["admin", "editor", "reviewer"]:
            sample_user_data["role"] = role
            user = User(**sample_user_data)
            assert user.can_edit is True

        # Roles that cannot edit
        for role in ["user", "translator", "viewer"]:
            sample_user_data["role"] = role
            user = User(**sample_user_data)
            assert user.can_edit is False

    def test_can_translate_property(self, sample_user_data):
        """Test the can_translate property."""
        # Roles that can translate
        for role in ["admin", "translator", "editor"]:
            sample_user_data["role"] = role
            user = User(**sample_user_data)
            assert user.can_translate is True

        # Roles that cannot translate
        for role in ["user", "reviewer", "viewer"]:
            sample_user_data["role"] = role
            user = User(**sample_user_data)
            assert user.can_translate is False


class TestUserSession:
    """Test the UserSession model."""

    @pytest.fixture
    def sample_session_data(self):
        """Create sample session data."""
        return {
            "id": 1,
            "user_id": 123,
            "session_token": "test_token_12345",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 (Test Browser)",
            "expires_at": datetime.utcnow() + timedelta(hours=24),
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow() - timedelta(minutes=5),
        }

    def test_user_session_creation(self, sample_session_data):
        """Test creating a UserSession instance."""
        session = UserSession(**sample_session_data)

        assert session.id == 1
        assert session.user_id == 123
        assert session.session_token == "test_token_12345"
        assert session.ip_address == "192.168.1.100"
        assert session.user_agent == "Mozilla/5.0 (Test Browser)"

    def test_user_session_minimal_data(self):
        """Test creating a UserSession with minimal required data."""
        session_data = {
            "id": 2,
            "user_id": 456,
            "session_token": "minimal_token",
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "created_at": datetime.utcnow(),
        }

        session = UserSession(**session_data)

        assert session.id == 2
        assert session.user_id == 456
        assert session.ip_address is None
        assert session.user_agent is None
        assert session.last_activity is None

    def test_create_token_class_method(self):
        """Test the create_token class method."""
        user_id = 123
        expires_hours = 48

        token, expires_at = UserSession.create_token(user_id, expires_hours)

        assert isinstance(token, str)
        assert len(token) > 20  # URL-safe tokens are typically longer
        assert isinstance(expires_at, datetime)

        # Check expiration time is approximately correct (within 1 minute tolerance)
        expected_expiry = datetime.utcnow() + timedelta(hours=expires_hours)
        time_diff = abs((expires_at - expected_expiry).total_seconds())
        assert time_diff < 60  # Within 1 minute

    def test_create_token_default_expiry(self):
        """Test create_token with default expiry."""
        token, expires_at = UserSession.create_token(123)

        # Default should be 24 hours
        expected_expiry = datetime.utcnow() + timedelta(hours=24)
        time_diff = abs((expires_at - expected_expiry).total_seconds())
        assert time_diff < 60  # Within 1 minute

    def test_is_expired_property(self, sample_session_data):
        """Test the is_expired property."""
        # Future expiration - not expired
        sample_session_data["expires_at"] = datetime.utcnow() + timedelta(hours=1)
        session = UserSession(**sample_session_data)
        assert session.is_expired is False

        # Past expiration - expired
        sample_session_data["expires_at"] = datetime.utcnow() - timedelta(hours=1)
        session = UserSession(**sample_session_data)
        assert session.is_expired is True

        # Very close to expiration (just expired)
        sample_session_data["expires_at"] = datetime.utcnow() - timedelta(seconds=1)
        session = UserSession(**sample_session_data)
        assert session.is_expired is True

    def test_is_valid_property(self, sample_session_data):
        """Test the is_valid property."""
        # Future expiration - valid
        sample_session_data["expires_at"] = datetime.utcnow() + timedelta(hours=1)
        session = UserSession(**sample_session_data)
        assert session.is_valid is True

        # Past expiration - invalid
        sample_session_data["expires_at"] = datetime.utcnow() - timedelta(hours=1)
        session = UserSession(**sample_session_data)
        assert session.is_valid is False

    def test_token_uniqueness(self):
        """Test that create_token generates unique tokens."""
        tokens = set()
        for _ in range(100):  # Generate 100 tokens
            token, _ = UserSession.create_token(123)
            tokens.add(token)

        # All tokens should be unique
        assert len(tokens) == 100


class TestUserPreference:
    """Test the UserPreference model."""

    @pytest.fixture
    def sample_preference_data(self):
        """Create sample preference data."""
        return {
            "id": 1,
            "user_id": 123,
            "preference_key": "theme",
            "preference_value": "dark",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

    def test_user_preference_creation(self, sample_preference_data):
        """Test creating a UserPreference instance."""
        preference = UserPreference(**sample_preference_data)

        assert preference.id == 1
        assert preference.user_id == 123
        assert preference.preference_key == "theme"
        assert preference.preference_value == "dark"

    def test_user_preference_minimal_data(self):
        """Test creating a UserPreference with minimal data."""
        preference_data = {
            "id": 2,
            "user_id": 456,
            "preference_key": "language",
            "preference_value": "fr",
            "created_at": datetime.utcnow(),
        }

        preference = UserPreference(**preference_data)

        assert preference.id == 2
        assert preference.updated_at is None

    def test_user_preference_various_value_types(self):
        """Test UserPreference with various value types."""
        base_data = {
            "id": 1,
            "user_id": 123,
            "preference_key": "test",
            "created_at": datetime.utcnow(),
        }

        # String value
        base_data.update({"preference_key": "theme", "preference_value": "dark"})
        preference = UserPreference(**base_data)
        assert preference.preference_value == "dark"

        # Boolean value
        base_data.update({"preference_key": "notifications", "preference_value": True})
        preference = UserPreference(**base_data)
        assert preference.preference_value is True

        # Integer value
        base_data.update({"preference_key": "page_size", "preference_value": 50})
        preference = UserPreference(**base_data)
        assert preference.preference_value == 50

        # Dictionary value
        base_data.update(
            {"preference_key": "settings", "preference_value": {"key": "value"}}
        )
        preference = UserPreference(**base_data)
        assert preference.preference_value == {"key": "value"}

        # List value
        base_data.update({"preference_key": "favorites", "preference_value": [1, 2, 3]})
        preference = UserPreference(**base_data)
        assert preference.preference_value == [1, 2, 3]


class TestUserPermission:
    """Test the UserPermission model."""

    @pytest.fixture
    def sample_permission_data(self):
        """Create sample permission data."""
        return {
            "id": 1,
            "user_id": 123,
            "resource_type": "document",
            "resource_id": 456,
            "permission_type": "read",
            "granted_by": 789,
            "granted_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=30),
        }

    def test_user_permission_creation(self, sample_permission_data):
        """Test creating a UserPermission instance."""
        permission = UserPermission(**sample_permission_data)

        assert permission.id == 1
        assert permission.user_id == 123
        assert permission.resource_type == "document"
        assert permission.resource_id == 456
        assert permission.permission_type == "read"
        assert permission.granted_by == 789

    def test_user_permission_minimal_data(self):
        """Test creating a UserPermission with minimal data."""
        permission_data = {
            "id": 2,
            "user_id": 456,
            "resource_type": "system",
            "permission_type": "admin",
            "granted_at": datetime.utcnow(),
        }

        permission = UserPermission(**permission_data)

        assert permission.id == 2
        assert permission.resource_id is None
        assert permission.granted_by is None
        assert permission.expires_at is None

    def test_is_expired_property_with_expiry(self, sample_permission_data):
        """Test the is_expired property with expiration date."""
        # Future expiration - not expired
        sample_permission_data["expires_at"] = datetime.utcnow() + timedelta(hours=1)
        permission = UserPermission(**sample_permission_data)
        assert permission.is_expired is False

        # Past expiration - expired
        sample_permission_data["expires_at"] = datetime.utcnow() - timedelta(hours=1)
        permission = UserPermission(**sample_permission_data)
        assert permission.is_expired is True

    def test_is_expired_property_no_expiry(self, sample_permission_data):
        """Test the is_expired property without expiration date."""
        sample_permission_data["expires_at"] = None
        permission = UserPermission(**sample_permission_data)
        assert permission.is_expired is False  # Never expires if no expiry date

    def test_is_valid_property(self, sample_permission_data):
        """Test the is_valid property."""
        # Future expiration - valid
        sample_permission_data["expires_at"] = datetime.utcnow() + timedelta(hours=1)
        permission = UserPermission(**sample_permission_data)
        assert permission.is_valid is True

        # Past expiration - invalid
        sample_permission_data["expires_at"] = datetime.utcnow() - timedelta(hours=1)
        permission = UserPermission(**sample_permission_data)
        assert permission.is_valid is False

        # No expiration - always valid
        sample_permission_data["expires_at"] = None
        permission = UserPermission(**sample_permission_data)
        assert permission.is_valid is True


class TestPasswordUtilities:
    """Test password utility functions."""

    def test_hash_password(self):
        """Test the hash_password function."""
        password = "test_password123"
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert hashed != password
        assert len(hashed) > 20  # Bcrypt hashes are typically 60 chars
        assert hashed.startswith("$2b$")  # Bcrypt identifier

    def test_verify_password_success(self):
        """Test successful password verification."""
        password = "test_password123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_failure(self):
        """Test failed password verification."""
        correct_password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(correct_password)

        assert verify_password(wrong_password, hashed) is False

    def test_hash_password_consistency(self):
        """Test that the same password produces different hashes (salt)."""
        password = "same_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different due to salt
        assert hash1 != hash2

        # But both should verify the original password
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_verify_password_empty_strings(self):
        """Test password verification with empty strings."""
        # Empty password
        assert verify_password("", hash_password("")) is True
        assert verify_password("", hash_password("not_empty")) is False
        assert verify_password("not_empty", hash_password("")) is False

    def test_verify_password_special_characters(self):
        """Test password verification with special characters."""
        special_passwords = [
            "password!@#$%^&*()",
            "пароль",  # Non-ASCII characters
            "🔐🔑",  # Emoji
            "pass word with spaces",
            "UPPERCASE_PASSWORD",
            "123456789",
            "a" * 100,  # Very long password
        ]

        for password in special_passwords:
            hashed = hash_password(password)
            assert verify_password(password, hashed) is True
            assert verify_password(password + "x", hashed) is False


class TestModelConfig:
    """Test model configuration."""

    def test_user_from_attributes_config(self):
        """Test that User model has from_attributes=True."""
        assert User.model_config.get("from_attributes") is True

    def test_user_session_from_attributes_config(self):
        """Test that UserSession model has from_attributes=True."""
        assert UserSession.model_config.get("from_attributes") is True

    def test_user_preference_from_attributes_config(self):
        """Test that UserPreference model has from_attributes=True."""
        assert UserPreference.model_config.get("from_attributes") is True

    def test_user_permission_from_attributes_config(self):
        """Test that UserPermission model has from_attributes=True."""
        assert UserPermission.model_config.get("from_attributes") is True


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_user_very_long_strings(self):
        """Test User model with very long strings."""
        long_string = "x" * 1000
        user_data = {
            "id": 1,
            "username": long_string,
            "email": f"{long_string}@example.com",
            "password_hash": hash_password("password"),
            "first_name": long_string,
            "last_name": long_string,
            "department": long_string,
            "created_at": datetime.utcnow(),
        }

        # Should create without validation error (Pydantic doesn't enforce string length limits by default)
        user = User(**user_data)
        assert len(user.username) == 1000
        assert len(user.full_name) == 2001  # first_name + " " + last_name

    def test_session_token_edge_cases(self):
        """Test session token generation edge cases."""
        # Very short expiry
        token, expires_at = UserSession.create_token(123, 0)
        assert isinstance(token, str)
        assert expires_at <= datetime.utcnow()

        # Very long expiry
        token, expires_at = UserSession.create_token(123, 8760)  # 1 year
        expected_expiry = datetime.utcnow() + timedelta(hours=8760)
        time_diff = abs((expires_at - expected_expiry).total_seconds())
        assert time_diff < 60

    def test_permission_expiry_edge_cases(self):
        """Test permission expiry edge cases."""
        base_data = {
            "id": 1,
            "user_id": 123,
            "resource_type": "test",
            "permission_type": "read",
            "granted_at": datetime.utcnow(),
        }

        # Permission expiring in 1 second
        base_data["expires_at"] = datetime.utcnow() + timedelta(seconds=1)
        permission = UserPermission(**base_data)
        assert permission.is_valid is True

        # Wait a moment and check again (in real scenario)
        # For testing, we'll simulate by setting past expiry
        base_data["expires_at"] = datetime.utcnow() - timedelta(milliseconds=1)
        permission = UserPermission(**base_data)
        assert permission.is_valid is False

    def test_password_context_configuration(self):
        """Test that password context is properly configured."""
        # Test that the context uses bcrypt
        assert "bcrypt" in pwd_context.schemes()

        # Test that deprecated schemes are handled
        password = "test123"
        hashed = pwd_context.hash(password)
        assert pwd_context.verify(password, hashed) is True
