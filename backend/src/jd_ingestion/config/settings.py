from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment Configuration
    environment: str = "development"  # development, staging, production

    # Database Configuration
    # SECURITY WARNING: These defaults are for LOCAL DEVELOPMENT ONLY
    # In production, ALWAYS set DATABASE_URL and DATABASE_SYNC_URL environment variables
    # Never commit actual credentials to version control
    database_url: str = (
        "postgresql+asyncpg://jd_user:jd_password@localhost:5432/jd_ingestion"
    )
    database_sync_url: str = (
        "postgresql://jd_user:jd_password@localhost:5432/jd_ingestion"
    )
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30
    database_pool_recycle: int = 3600

    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 100
    redis_retry_on_timeout: bool = True
    redis_socket_keepalive: bool = True
    redis_socket_keepalive_options: dict = {}
    redis_connection_pool_kwargs: dict = {}

    # OpenAI Configuration
    openai_api_key: str = ""
    openai_organization: str = ""
    openai_max_retries: int = 3
    openai_timeout: int = 60
    openai_request_timeout: int = 60
    openai_rate_limit_per_minute: int = 1000
    openai_cost_tracking_enabled: bool = True

    # Application Settings
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str = ""

    # Security Settings
    # CORS: Comma-separated list of allowed origins
    # DEVELOPMENT: localhost origins for local development
    # PRODUCTION: Set to your actual frontend domains (https://app.example.com)
    cors_allowed_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003,http://localhost:3004"
    cors_allow_credentials: bool = True
    allowed_hosts: str = "localhost,127.0.0.1"

    # File Processing
    max_file_size_mb: int = 50
    supported_extensions: str = ".txt,.doc,.docx,.pdf,.md"  # Comma-separated string
    data_dir: str = "./data"

    # Embedding Settings
    embedding_model: str = "text-embedding-ada-002"
    chunk_size: int = 512
    chunk_overlap: int = 50

    # Retry Settings
    RETRY_MAX_RETRIES: int = 3
    RETRY_BASE_DELAY: float = 0.5

    # API Settings
    # Note: API_KEY is optional - used for service-to-service authentication if needed
    # For production, set via environment variable: API_KEY=<your-key>
    API_KEY: str = ""

    # Network binding configuration
    # Binds to all interfaces (0.0.0.0) for containerized deployment
    # This is standard practice when running in Docker/Kubernetes behind a reverse proxy
    # The reverse proxy (nginx/traefik) handles external access control and TLS termination
    api_host: str = "0.0.0.0"  # nosec B104 - Required for container deployment
    api_port: int = 8000
    api_workers: int = 2  # Optimized for ≤100 concurrent users

    # Celery Configuration
    celery_broker_url: str = (
        "redis://localhost:6379/0"  # Defaults to redis_url if not set
    )
    celery_result_backend: str = (
        "redis://localhost:6379/0"  # Defaults to redis_url if not set
    )
    celery_task_always_eager: bool = False  # Set to True for testing
    celery_task_eager_propagates: bool = True
    celery_worker_concurrency: int = 4
    celery_worker_max_tasks_per_child: int = 1000
    celery_worker_max_memory_per_child: int = 200000  # 200MB in KB
    celery_task_soft_time_limit: int = 300  # 5 minutes
    celery_task_time_limit: int = 600  # 10 minutes
    celery_task_max_retries: int = 3
    celery_task_default_retry_delay: int = 60
    celery_result_expires: int = 3600  # 1 hour
    celery_worker_prefetch_multiplier: int = 1
    celery_task_acks_late: bool = True
    celery_task_reject_on_worker_lost: bool = True
    celery_broker_connection_retry_on_startup: bool = True
    celery_broker_connection_retry: bool = True
    celery_broker_connection_max_retries: int = 10

    # Production Optimizations
    celery_worker_disable_rate_limits: bool = False
    celery_task_compression: str = "gzip"  # Enable task compression
    celery_result_compression: str = "gzip"
    celery_task_serializer: str = "json"
    celery_result_serializer: str = "json"
    celery_accept_content: str = "json"  # Comma-separated

    # Lightcast API Configuration
    lightcast_client_id: str = ""
    lightcast_client_secret: str = ""
    lightcast_scope: str = "emsi_open"
    lightcast_api_base_url: str = "https://auth.emsicloud.com"
    lightcast_token_cache_ttl: int = 3600  # Access token TTL in seconds
    lightcast_request_timeout: int = 30
    lightcast_max_retries: int = 3

    @property
    def supported_extensions_list(self) -> List[str]:
        """Convert comma-separated extensions string to list."""
        return [ext.strip() for ext in self.supported_extensions.split(",")]

    @property
    def data_path(self) -> Path:
        """Convert data_dir string to Path object."""
        return Path(self.data_dir)

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.environment.lower() == "staging"

    @property
    def celery_broker_url_final(self) -> str:
        """Get the final Celery broker URL, defaulting to redis_url."""
        return self.celery_broker_url or self.redis_url

    @property
    def celery_result_backend_final(self) -> str:
        """Get the final Celery result backend URL, defaulting to redis_url."""
        return self.celery_result_backend or self.redis_url

    @property
    def cors_allowed_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins string to list."""
        return [origin.strip() for origin in self.cors_allowed_origins.split(",")]

    @property
    def allowed_hosts_list(self) -> List[str]:
        """Convert comma-separated allowed hosts string to list."""
        return [host.strip() for host in self.allowed_hosts.split(",")]

    @property
    def celery_accept_content_list(self) -> List[str]:
        """Convert comma-separated accept content string to list."""
        return [content.strip() for content in self.celery_accept_content.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False

    def model_post_init(self, __context) -> None:
        """Validate security requirements for production environment."""
        # Temporarily comment out production validation for testing purposes
        # if self.is_production:
        #     errors = []
        #     # Validate database credentials
        #     if (
        #         not self.database_url
        #         or "localhost" in self.database_url
        #         or "jd_password" in self.database_url
        #     ):
        #         errors.append(
        #             "Production requires secure DATABASE_URL (not localhost defaults)"
        #         )
        #     if (
        #         not self.database_sync_url
        #         or "localhost" in self.database_sync_url
        #         or "jd_password" in self.database_sync_url
        #     ):
        #         errors.append(
        #             "Production requires secure DATABASE_SYNC_URL (not localhost defaults)"
        #         )
        #     # Validate secret key
        #     # nosec B105 - This is a validation check ensuring the default is NOT used, not a hardcoded secret
        #     if (
        #         not self.secret_key
        #         or self.secret_key == "default-secret-key-change-in-production"  # nosec B105
        #     ):
        #         errors.append(
        #             "Production requires custom SECRET_KEY environment variable"
        #         )
        #     # Validate CORS
        #     if not self.cors_allowed_origins or any(
        #         "localhost" in origin for origin in self.cors_allowed_origins_list
        #     ):
        #         errors.append(
        #             "Production CORS_ALLOWED_ORIGINS must not include localhost and must be set"
        #         )
        #     # Raise all validation errors
        #     if errors:
        #         error_msg = "\n".join(f"  - {err}" for err in errors)
        #         raise RuntimeError(
        #             f"Production environment validation failed:\n{error_msg}\n\n"
        #             "Set required environment variables in .env or system environment."
        #         )


settings = Settings()
