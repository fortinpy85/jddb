#!/usr/bin/env python3
"""
This script tests the API endpoints for file processing and job retrieval.
"""
import logging
import requests
from pathlib import Path
from urllib.parse import quote
from typing import Optional

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def test_process_file() -> Optional[int]:
    """
    Sends a POST request to the /api/ingestion/process-file endpoint
    with a file path and checks the response.
    """
    base_url = "http://localhost:8000/api"
    file_path = (
        Path(__file__).parent.parent
        / "data"
        / "raw"
        / "EX-01 Dir, Business Analysis 103249 - JD.txt"
    )

    if not file_path.exists():
        logging.error(f"Test file not found at {file_path}")
        return None

    encoded_path = quote(str(file_path))
    url = f"{base_url}/ingestion/process-file?file_path={encoded_path}&save_to_db=true"

    logging.info(f"Testing URL: {url}")

    try:
        response = requests.post(url)
        logging.info(f"Status Code: {response.status_code}")
        logging.info(f"Response: {response.json()}")

        if response.status_code == 200:
            result = response.json()
            if result.get("job_id"):
                logging.info(f"SUCCESS: Job saved with ID: {result['job_id']}")
                return result["job_id"]
            else:
                logging.warning("No job_id in response")
        else:
            logging.error(f"ERROR: {response.status_code}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error: {e}")

    return None


def check_job_in_db(job_id: Optional[int]) -> bool:
    """
    Checks if the job was actually saved to the database.
    """
    if not job_id:
        return False

    base_url = "http://localhost:8000/api"
    url = f"{base_url}/jobs/{job_id}"

    try:
        response = requests.get(url)
        logging.info(f"Job check status: {response.status_code}")
        if response.status_code == 200:
            job_data = response.json()
            logging.info(f"Job found: {job_data['title']}")
            return True
        else:
            logging.info("Job not found in database")
            return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Error checking job: {e}")
        return False


def main() -> None:
    """
    Runs the test_process_file and check_job_in_db functions.
    """
    logging.info("Testing file processing with database persistence...")
    job_id = test_process_file()

    if job_id:
        logging.info(f"\nChecking if job {job_id} exists in database...")
        success = check_job_in_db(job_id)
        if success:
            logging.info("✅ SUCCESS: File uploaded and saved to database!")
        else:
            logging.error("❌ FAILED: File processed but not found in database")
    else:
        logging.error("❌ FAILED: File processing failed")


if __name__ == "__main__":
    main()
