#!/usr/bin/env python3
"""
This script tests the ContentProcessor by reading a sample file,
extracting metadata, and then using the ContentProcessor to extract
sections and structured fields.
"""
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jd_ingestion.processors.file_discovery import FileDiscovery
from jd_ingestion.processors.content_processor import ContentProcessor

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main() -> None:
    """
    Tests the ContentProcessor.
    """
    try:
        raw_data_directory = Path("C:/JDDB/data/raw")
        sample_file_name = "EX-01 Dir, Business Analysis 103249 - JD.txt"
        sample_file_path = raw_data_directory / sample_file_name

        if not sample_file_path.exists():
            logging.error(f"Sample file not found at {sample_file_path}")
            return

        file_discovery = FileDiscovery(str(raw_data_directory))
        metadata = file_discovery.extract_metadata_from_filename(sample_file_name)
        detected_encoding = file_discovery.detect_encoding(str(sample_file_path))

        logging.info(f"Processing file: {sample_file_name}")
        logging.info(f"Initial Metadata: {metadata}")
        logging.info(f"Detected Encoding: {detected_encoding}")

        raw_content = sample_file_path.read_text(encoding=detected_encoding)
        content_processor = ContentProcessor(
            raw_content, language=metadata.get("language", "en")
        )

        sections = content_processor.extract_sections()
        logging.info("\n--- Extracted Sections ---")
        for header, content in sections.items():
            logging.info(f"Header: {header}")
            logging.info(f"Content: {content[:200]}...")
            logging.info("-" * 30)

        structured_fields = content_processor.parse_structured_fields()
        logging.info("\n--- Parsed Structured Fields ---")
        for field, value in structured_fields.items():
            logging.info(f"{field}: {value}")

    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
