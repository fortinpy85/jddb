#!/usr/bin/env python3
"""
This script is a simple test of the API endpoint /api/ingestion/process-file.
"""
import logging
import requests
from pathlib import Path
from urllib.parse import quote

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def test_process_file() -> None:
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
        return

    encoded_path = quote(str(file_path))
    url = f"{base_url}/ingestion/process-file?file_path={encoded_path}&save_to_db=true"

    logging.info(f"Testing URL: {url}")

    try:
        response = requests.post(url)
        logging.info(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            logging.info("SUCCESS: File processed successfully!")
            if result.get("job_id"):
                logging.info(f"Job saved with ID: {result['job_id']}")
            else:
                logging.warning("No job_id in response")
        else:
            logging.error(f"ERROR: {response.status_code}")
            try:
                error_detail = response.json()
                logging.error(f"Error detail: {error_detail}")
            except requests.exceptions.JSONDecodeError:
                logging.error(f"Raw response: {response.text}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error: {e}")


def main() -> None:
    """
    Runs the test_process_file function.
    """
    test_process_file()


if __name__ == "__main__":
    main()
