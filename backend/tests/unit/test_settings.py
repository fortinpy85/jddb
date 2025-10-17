"""
Tests for settings configuration module.
"""

import os
from pathlib import Path
from unittest.mock import patch

from jd_ingestion.config.settings import Settings, settings


class TestSettings:
    """Test Settings class functionality."""

    def test_settings_default_values(self):
        """Test that default values are set correctly."""
        # Clear sensitive env vars to test defaults
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "",
                "DEBUG": "False",
                "SECRET_KEY": "default-secret-key-change-in-production",
                "DATA_DIR": "./data",
            },
            clear=False,
        ):
            test_settings = Settings()

            # Environment Configuration
            assert test_settings.environment == "development"

            # Database Configuration
            assert "postgresql+asyncpg" in test_settings.database_url
            assert test_settings.database_pool_size == 10
            assert test_settings.database_max_overflow == 20
            assert test_settings.database_pool_timeout == 30
            assert test_settings.database_pool_recycle == 3600

            # Redis Configuration
            assert test_settings.redis_url == "redis://localhost:6379/0"
            assert test_settings.redis_max_connections == 100
            assert test_settings.redis_retry_on_timeout is True
            assert test_settings.redis_socket_keepalive is True

            # OpenAI Configuration
            assert test_settings.openai_api_key == ""
            assert test_settings.openai_organization == ""
            assert test_settings.openai_max_retries == 3
            assert test_settings.openai_timeout == 60
            assert test_settings.openai_rate_limit_per_minute == 1000
            assert test_settings.openai_cost_tracking_enabled is True

            # Application Settings
            assert test_settings.debug is False
            assert test_settings.log_level == "INFO"
            assert test_settings.secret_key == "default-secret-key-change-in-production"

            # Security Settings
            assert "localhost" in test_settings.cors_allowed_origins
            assert test_settings.cors_allow_credentials is True
            assert "localhost" in test_settings.allowed_hosts

            # File Processing
            assert test_settings.max_file_size_mb == 50
            assert ".txt" in test_settings.supported_extensions
            assert test_settings.data_dir == "./data"

            # Embedding Settings
            assert test_settings.embedding_model == "text-embedding-ada-002"
            assert test_settings.chunk_size == 512
            assert test_settings.chunk_overlap == 50

        # API Settings
        assert test_settings.api_host == "0.0.0.0"
        assert test_settings.api_port == 8000
        assert test_settings.api_workers == 1

    def test_settings_with_environment_variables(self):
        """Test settings loading from environment variables."""
        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "production",
                "DATABASE_URL": "postgresql+asyncpg://prod:pass@db:5432/prod_db",
                "DEBUG": "true",
                "LOG_LEVEL": "DEBUG",
                "SECRET_KEY": "production-secret-key",
                "MAX_FILE_SIZE_MB": "100",
                "API_PORT": "9000",
                "OPENAI_API_KEY": "sk-test123",
                "REDIS_URL": "redis://redis:6379/1",
            },
        ):
            test_settings = Settings()

            assert test_settings.environment == "production"
            assert "prod_db" in test_settings.database_url
            assert test_settings.debug is True
            assert test_settings.log_level == "DEBUG"
            assert test_settings.secret_key == "production-secret-key"
            assert test_settings.max_file_size_mb == 100
            assert test_settings.api_port == 9000
            assert test_settings.openai_api_key == "sk-test123"
            assert test_settings.redis_url == "redis://redis:6379/1"

    def test_supported_extensions_list_property(self):
        """Test supported_extensions_list property conversion."""
        test_settings = Settings()
        test_settings.supported_extensions = ".txt,.doc,.docx,.pdf"

        extensions = test_settings.supported_extensions_list
        assert extensions == [".txt", ".doc", ".docx", ".pdf"]

    def test_supported_extensions_list_with_spaces(self):
        """Test supported_extensions_list handles spaces correctly."""
        test_settings = Settings()
        test_settings.supported_extensions = ".txt, .doc , .docx, .pdf "

        extensions = test_settings.supported_extensions_list
        assert extensions == [".txt", ".doc", ".docx", ".pdf"]

    def test_data_path_property(self):
        """Test data_path property conversion to Path object."""
        test_settings = Settings()
        test_settings.data_dir = "./custom/data/path"

        data_path = test_settings.data_path
        assert isinstance(data_path, Path)
        # Use as_posix() for cross-platform path comparison
        assert data_path.as_posix() == "custom/data/path"

    def test_environment_properties(self):
        """Test environment detection properties."""
        # Test production environment
        prod_settings = Settings()
        prod_settings.environment = "production"
        assert prod_settings.is_production is True
        assert prod_settings.is_development is False
        assert prod_settings.is_staging is False

        # Test development environment
        dev_settings = Settings()
        dev_settings.environment = "development"
        assert dev_settings.is_production is False
        assert dev_settings.is_development is True
        assert dev_settings.is_staging is False

        # Test staging environment
        staging_settings = Settings()
        staging_settings.environment = "staging"
        assert staging_settings.is_production is False
        assert staging_settings.is_development is False
        assert staging_settings.is_staging is True

    def test_environment_properties_case_insensitive(self):
        """Test environment detection is case insensitive."""
        test_settings = Settings()

        # Test uppercase
        test_settings.environment = "PRODUCTION"
        assert test_settings.is_production is True

        # Test mixed case
        test_settings.environment = "Development"
        assert test_settings.is_development is True

        test_settings.environment = "STAGING"
        assert test_settings.is_staging is True

    def test_celery_broker_url_final_default(self):
        """Test celery_broker_url_final defaults to redis_url."""
        test_settings = Settings()
        test_settings.redis_url = "redis://custom:6379/1"
        test_settings.celery_broker_url = ""  # Empty string

        assert test_settings.celery_broker_url_final == "redis://custom:6379/1"

    def test_celery_broker_url_final_custom(self):
        """Test celery_broker_url_final uses custom value when set."""
        test_settings = Settings()
        test_settings.redis_url = "redis://default:6379/0"
        test_settings.celery_broker_url = "redis://celery:6379/2"

        assert test_settings.celery_broker_url_final == "redis://celery:6379/2"

    def test_celery_result_backend_final_default(self):
        """Test celery_result_backend_final defaults to redis_url."""
        test_settings = Settings()
        test_settings.redis_url = "redis://custom:6379/1"
        test_settings.celery_result_backend = ""  # Empty string

        assert test_settings.celery_result_backend_final == "redis://custom:6379/1"

    def test_celery_result_backend_final_custom(self):
        """Test celery_result_backend_final uses custom value when set."""
        test_settings = Settings()
        test_settings.redis_url = "redis://default:6379/0"
        test_settings.celery_result_backend = "redis://results:6379/3"

        assert test_settings.celery_result_backend_final == "redis://results:6379/3"

    def test_cors_allowed_origins_list_property(self):
        """Test CORS allowed origins list conversion."""
        test_settings = Settings()
        test_settings.cors_allowed_origins = (
            "http://localhost:3000,https://app.example.com,http://127.0.0.1:3001"
        )

        origins = test_settings.cors_allowed_origins_list
        assert origins == [
            "http://localhost:3000",
            "https://app.example.com",
            "http://127.0.0.1:3001",
        ]

    def test_cors_allowed_origins_list_with_spaces(self):
        """Test CORS allowed origins handles spaces correctly."""
        test_settings = Settings()
        test_settings.cors_allowed_origins = (
            " http://localhost:3000 , https://app.example.com, http://127.0.0.1:3001 "
        )

        origins = test_settings.cors_allowed_origins_list
        assert origins == [
            "http://localhost:3000",
            "https://app.example.com",
            "http://127.0.0.1:3001",
        ]

    def test_allowed_hosts_list_property(self):
        """Test allowed hosts list conversion."""
        test_settings = Settings()
        test_settings.allowed_hosts = "localhost,127.0.0.1,api.example.com"

        hosts = test_settings.allowed_hosts_list
        assert hosts == ["localhost", "127.0.0.1", "api.example.com"]

    def test_allowed_hosts_list_with_spaces(self):
        """Test allowed hosts handles spaces correctly."""
        test_settings = Settings()
        test_settings.allowed_hosts = " localhost , 127.0.0.1 , api.example.com "

        hosts = test_settings.allowed_hosts_list
        assert hosts == ["localhost", "127.0.0.1", "api.example.com"]

    def test_celery_accept_content_list_property(self):
        """Test Celery accept content list conversion."""
        test_settings = Settings()
        test_settings.celery_accept_content = "json,pickle,yaml"

        content_types = test_settings.celery_accept_content_list
        assert content_types == ["json", "pickle", "yaml"]

    def test_celery_accept_content_list_with_spaces(self):
        """Test Celery accept content handles spaces correctly."""
        test_settings = Settings()
        test_settings.celery_accept_content = " json , pickle , yaml "

        content_types = test_settings.celery_accept_content_list
        assert content_types == ["json", "pickle", "yaml"]

    def test_celery_configuration_defaults(self):
        """Test Celery configuration default values."""
        test_settings = Settings()

        # Task settings
        assert test_settings.celery_task_always_eager is False
        assert test_settings.celery_task_eager_propagates is True
        assert test_settings.celery_task_soft_time_limit == 300
        assert test_settings.celery_task_time_limit == 600
        assert test_settings.celery_task_max_retries == 3
        assert test_settings.celery_task_default_retry_delay == 60

        # Worker settings
        assert test_settings.celery_worker_concurrency == 4
        assert test_settings.celery_worker_max_tasks_per_child == 1000
        assert test_settings.celery_worker_max_memory_per_child == 200000
        assert test_settings.celery_worker_prefetch_multiplier == 1

        # Reliability settings
        assert test_settings.celery_task_acks_late is True
        assert test_settings.celery_task_reject_on_worker_lost is True
        assert test_settings.celery_broker_connection_retry is True
        assert test_settings.celery_broker_connection_retry_on_startup is True
        assert test_settings.celery_broker_connection_max_retries == 10

        # Optimization settings
        assert test_settings.celery_task_compression == "gzip"
        assert test_settings.celery_result_compression == "gzip"
        assert test_settings.celery_task_serializer == "json"
        assert test_settings.celery_result_serializer == "json"
        assert test_settings.celery_accept_content == "json"

    def test_retry_settings(self):
        """Test retry configuration values."""
        test_settings = Settings()

        assert test_settings.RETRY_MAX_RETRIES == 3
        assert test_settings.RETRY_BASE_DELAY == 0.5

    def test_redis_configuration_defaults(self):
        """Test Redis configuration default values."""
        test_settings = Settings()

        assert test_settings.redis_max_connections == 100
        assert test_settings.redis_retry_on_timeout is True
        assert test_settings.redis_socket_keepalive is True
        assert isinstance(test_settings.redis_socket_keepalive_options, dict)
        assert isinstance(test_settings.redis_connection_pool_kwargs, dict)

    def test_config_class_settings(self):
        """Test Config class settings."""
        test_settings = Settings()

        # Verify config attributes exist and have expected values
        assert hasattr(test_settings.Config, "env_file")
        assert hasattr(test_settings.Config, "case_sensitive")
        assert test_settings.Config.env_file == ".env"
        assert test_settings.Config.case_sensitive is False


class TestSettingsInstance:
    """Test the global settings instance."""

    def test_settings_instance_exists(self):
        """Test that the global settings instance is properly created."""
        from jd_ingestion.config.settings import settings

        assert settings is not None
        assert isinstance(settings, Settings)

    def test_settings_instance_properties(self):
        """Test that the global settings instance has all expected properties."""
        # Test that all properties are accessible
        assert hasattr(settings, "environment")
        assert hasattr(settings, "database_url")
        assert hasattr(settings, "redis_url")
        assert hasattr(settings, "openai_api_key")
        assert hasattr(settings, "debug")

        # Test computed properties
        assert hasattr(settings, "is_production")
        assert hasattr(settings, "is_development")
        assert hasattr(settings, "is_staging")
        assert hasattr(settings, "data_path")
        assert hasattr(settings, "supported_extensions_list")
        assert hasattr(settings, "cors_allowed_origins_list")
        assert hasattr(settings, "allowed_hosts_list")
        assert hasattr(settings, "celery_broker_url_final")
        assert hasattr(settings, "celery_result_backend_final")
        assert hasattr(settings, "celery_accept_content_list")

    def test_settings_instance_type_consistency(self):
        """Test that property types are consistent."""
        # String properties
        assert isinstance(settings.environment, str)
        assert isinstance(settings.database_url, str)
        assert isinstance(settings.redis_url, str)
        assert isinstance(settings.log_level, str)

        # Integer properties
        assert isinstance(settings.database_pool_size, int)
        assert isinstance(settings.api_port, int)
        assert isinstance(settings.max_file_size_mb, int)
        assert isinstance(settings.chunk_size, int)

        # Boolean properties
        assert isinstance(settings.debug, bool)
        assert isinstance(settings.is_production, bool)
        assert isinstance(settings.cors_allow_credentials, bool)

        # Path property
        assert isinstance(settings.data_path, Path)

        # List properties
        assert isinstance(settings.supported_extensions_list, list)
        assert isinstance(settings.cors_allowed_origins_list, list)
        assert isinstance(settings.allowed_hosts_list, list)


class TestSettingsValidation:
    """Test settings validation and edge cases."""

    def test_empty_comma_separated_values(self):
        """Test handling of empty comma-separated values."""
        test_settings = Settings()

        # Test empty supported extensions
        test_settings.supported_extensions = ""
        extensions = test_settings.supported_extensions_list
        assert extensions == [""]

        # Test empty CORS origins
        test_settings.cors_allowed_origins = ""
        origins = test_settings.cors_allowed_origins_list
        assert origins == [""]

    def test_single_value_comma_separated(self):
        """Test handling of single values in comma-separated fields."""
        test_settings = Settings()

        # Test single supported extension
        test_settings.supported_extensions = ".txt"
        extensions = test_settings.supported_extensions_list
        assert extensions == [".txt"]

        # Test single CORS origin
        test_settings.cors_allowed_origins = "http://localhost:3000"
        origins = test_settings.cors_allowed_origins_list
        assert origins == ["http://localhost:3000"]

    def test_path_creation_different_formats(self):
        """Test Path creation with different path formats."""
        test_settings = Settings()

        # Test relative path - use as_posix() for cross-platform compatibility
        test_settings.data_dir = "./data"
        assert isinstance(test_settings.data_path, Path)
        assert test_settings.data_path.as_posix() == "data"

        # Test absolute path
        test_settings.data_dir = "/var/app/data"
        assert isinstance(test_settings.data_path, Path)
        # On Windows, this becomes C:/var/app/data, so just check it's a Path
        assert test_settings.data_path.parts[-1] == "data"

        # Test Windows path - only check on Windows
        import sys

        if sys.platform == "win32":
            test_settings.data_dir = "C:\\app\\data"
            assert isinstance(test_settings.data_path, Path)
            assert test_settings.data_path.as_posix() == "C:/app/data"

    def test_boolean_environment_variables(self):
        """Test boolean conversion from environment variables."""
        with patch.dict(
            os.environ,
            {
                "DEBUG": "true",
                "CORS_ALLOW_CREDENTIALS": "false",
                "OPENAI_COST_TRACKING_ENABLED": "1",
                "REDIS_RETRY_ON_TIMEOUT": "0",
            },
        ):
            test_settings = Settings()

            assert test_settings.debug is True
            assert test_settings.cors_allow_credentials is False
            assert test_settings.openai_cost_tracking_enabled is True
            assert test_settings.redis_retry_on_timeout is False
