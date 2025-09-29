#!/usr/bin/env python3
"""
This script starts a Celery worker for the job description ingestion system.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add the src directory to Python path
backend_dir = Path(__file__).parent.parent
src_dir = backend_dir / "src"
sys.path.insert(0, str(src_dir))

# Import Celery app
from jd_ingestion.tasks.celery_app import celery_app  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main() -> None:
    """
    Starts the Celery worker with the given arguments.
    """
    parser = argparse.ArgumentParser(description="Start a Celery worker.")
    parser.add_argument("--loglevel", default="info", help="Logging level")
    parser.add_argument(
        "--queues",
        default="processing,embeddings",
        help="Comma-separated list of queues to consume from",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=2,
        help="Number of concurrent worker processes",
    )
    args = parser.parse_args()

    worker_args = [
        "worker",
        f"--loglevel={args.loglevel}",
        f"--queues={args.queues}",
        f"--concurrency={args.concurrency}",
    ]

    try:
        logging.info(f"Starting Celery worker with args: {worker_args}")
        celery_app.worker_main(worker_args)
    except Exception as e:
        logging.critical(f"Failed to start Celery worker: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
