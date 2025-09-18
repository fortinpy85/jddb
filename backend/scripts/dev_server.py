#!/usr/bin/env python3
"""
This script runs the development server with auto-reload and debugging features.
"""
import logging
import sys
from pathlib import Path
import uvicorn

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jd_ingestion.config import settings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main() -> None:
    """
    Runs the development server with optimal settings.
    """
    try:
        logging.info("Starting Job Description Ingestion Engine API Server...")
        logging.info(
            f"Server will be available at: http://{settings.api_host}:{settings.api_port}"
        )
        logging.info(
            f"API Documentation: http://{settings.api_host}:{settings.api_port}/api/docs"
        )
        logging.info(f"Debug mode: {settings.debug}")
        logging.info("=" * 60)

        uvicorn.run(
            "jd_ingestion.api.main:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=True,
            reload_dirs=["src"],
            log_level=settings.log_level.lower(),
            access_log=True,
            use_colors=True,
            loop="asyncio",
            lifespan="on",
        )
    except Exception as e:
        logging.error(f"Failed to start the server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
