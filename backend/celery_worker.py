#!/usr/bin/env python3
"""
Celery worker entry point for the job description ingestion system.
This script properly configures the Python path and starts the Celery worker.
"""

import sys
import os


def main():
    """
    Starts the Celery worker.
    """
    try:
        # Add the src directory to the Python path
        backend_dir = os.path.abspath(os.path.dirname(__file__))
        src_dir = os.path.join(backend_dir, "src")
        sys.path.insert(0, src_dir)

        # Now import and start the Celery app
        from jd_ingestion.tasks.celery_app import celery_app

        # Start the Celery worker
        celery_app.start()
    except ImportError as e:
        print(f"Error: {e}")
        print(
            "Please ensure that the required modules are installed and the Python path is correct."
        )
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
