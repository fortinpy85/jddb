#!/usr/bin/env python3
"""
This script tests the FileDiscovery processor by scanning a directory for files,
extracting metadata from the filenames, detecting the encoding, and validating
the file format.
"""
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jd_ingestion.processors.file_discovery import FileDiscovery

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main() -> None:
    """
    Tests the FileDiscovery processor.
    """
    try:
        raw_data_directory = Path("C:/JDDB/data/raw")

        if not raw_data_directory.exists():
            logging.error(f"Raw data directory not found at {raw_data_directory}")
            return

        file_discovery = FileDiscovery(str(raw_data_directory))
        found_files = file_discovery.scan_directory()

        if not found_files:
            logging.info(f"No .txt files found in {raw_data_directory}.")
            return

        logging.info(f"Found {len(found_files)} files in {raw_data_directory}:")
        for file_info in found_files:
            file_path = file_info["file_path"]
            file_name = file_info["file_name"]

            logging.info(f"\nProcessing file: {file_name}")

            metadata = file_discovery.extract_metadata_from_filename(file_name)
            logging.info(f"  Extracted Metadata: {metadata}")

            encoding = file_discovery.detect_encoding(file_path)
            logging.info(f"  Detected Encoding: {encoding}")

            is_valid = file_discovery.validate_file_format(file_path)
            logging.info(f"  Is Valid Format (non-empty): {is_valid}")

    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
