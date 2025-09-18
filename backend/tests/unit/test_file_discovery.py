import pytest
from pathlib import Path
from datetime import datetime
from jd_ingestion.processors.file_discovery import FileDiscovery, FileMetadata


# Mock the logger to prevent actual logging during tests
class MockLogger:
    def __init__(self):
        self.debug_messages = []
        self.info_messages = []
        self.warning_messages = []
        self.error_messages = []

    def debug(self, msg, **kwargs):
        self.debug_messages.append((msg, kwargs))

    def info(self, msg, **kwargs):
        self.info_messages.append((msg, kwargs))

    def warning(self, msg, **kwargs):
        self.warning_messages.append((msg, kwargs))

    def error(self, msg, **kwargs):
        self.error_messages.append((msg, kwargs))


# Replace the actual logger with the mock logger for testing
FileDiscovery.logger = MockLogger()


@pytest.fixture
def file_discovery_instance():
    # Use a dummy path for data_directory as it's not used in _extract_metadata_from_filename
    return FileDiscovery(data_directory=Path("/tmp/dummy_data"))


def test_extract_metadata_from_filename_pattern1(file_discovery_instance):
    # Pattern: "EX-01 Dir, Business Analysis 103249 - JD.txt"
    filename = "EX-01 Dir, Business Analysis 103249 - JD.txt"
    metadata = FileMetadata(file_path=Path(filename))
    file_discovery_instance._extract_metadata_from_filename(filename, metadata)

    assert metadata.classification == "EX-01"
    assert metadata.job_number == "103249"
    assert metadata.language == "en"
    assert metadata.title == "Dir Business Analysis"
    assert not metadata.validation_errors


def test_extract_metadata_from_filename_pattern2(file_discovery_instance):
    # Pattern: "JD_EX-01_123456_Director.txt"
    filename = "JD_EX-01_123456_Director.txt"
    metadata = FileMetadata(file_path=Path(filename))
    file_discovery_instance._extract_metadata_from_filename(filename, metadata)

    assert metadata.classification == "EX-01"
    assert metadata.job_number == "123456"
    assert metadata.language == "en"
    assert metadata.title == "Director"
    assert not metadata.validation_errors


def test_extract_metadata_from_filename_pattern2_no_title(file_discovery_instance):
    # Pattern: "JD_EX-01_123456.txt"
    filename = "JD_EX-01_123456.txt"
    metadata = FileMetadata(file_path=Path(filename))
    file_discovery_instance._extract_metadata_from_filename(filename, metadata)

    assert metadata.classification == "EX-01"
    assert metadata.job_number == "123456"
    assert metadata.language == "en"
    assert metadata.title is None
    assert not metadata.validation_errors


def test_extract_metadata_from_filename_pattern3(file_discovery_instance):
    # Pattern: "Director Business Analysis EX-01 103249.txt"
    filename = "Director Business Analysis EX-01 103249.txt"
    metadata = FileMetadata(file_path=Path(filename))
    file_discovery_instance._extract_metadata_from_filename(filename, metadata)

    assert metadata.classification == "EX-01"
    assert metadata.job_number == "103249"
    assert metadata.language == "en"  # Default language
    assert metadata.title == "Director Business Analysis"
    assert not metadata.validation_errors


def test_extract_metadata_from_filename_pattern3_with_lang_code(
    file_discovery_instance,
):
    # Pattern: "Director Business Analysis EX-01 103249-DE.txt"
    filename = "Director Business Analysis EX-01 103249-DE.txt"
    metadata = FileMetadata(file_path=Path(filename))
    file_discovery_instance._extract_metadata_from_filename(filename, metadata)

    assert metadata.classification == "EX-01"
    assert metadata.job_number == "103249"
    assert metadata.language == "fr"
    assert metadata.title == "Director Business Analysis"
    assert not metadata.validation_errors


def test_extract_metadata_from_filename_unrecognized_pattern(file_discovery_instance):
    filename = "Some_Random_File.txt"
    metadata = FileMetadata(file_path=Path(filename))
    file_discovery_instance._extract_metadata_from_filename(filename, metadata)

    assert metadata.classification is None
    assert metadata.job_number is None
    assert metadata.language == "en"  # Default language
    assert metadata.title is None
    assert any(
        "Filename doesn't match expected patterns but extracted basic info" in error
        for error in metadata.validation_errors
    )


def test_extract_metadata_from_filename_partial_match(file_discovery_instance):
    filename = "EX-01 Some File.txt"  # Only classification matches
    metadata = FileMetadata(file_path=Path(filename))
    file_discovery_instance._extract_metadata_from_filename(filename, metadata)

    assert metadata.classification == "EX-01"
    assert metadata.job_number is None
    assert metadata.language == "en"
    assert metadata.title is None
    assert any(
        "Filename doesn't match expected patterns but extracted basic info" in error
        for error in metadata.validation_errors
    )


def test_extract_metadata_from_filename_title_cleanup(file_discovery_instance):
    filename = "EX-01 Dir_of_IT, 100000 - JD.txt"
    metadata = FileMetadata(file_path=Path(filename))
    file_discovery_instance._extract_metadata_from_filename(filename, metadata)
    assert metadata.title == "Dir of IT"

    filename = "EX-01  Dir   of   HR  100001 - JD.txt"
    metadata = FileMetadata(file_path=Path(filename))
    file_discovery_instance._extract_metadata_from_filename(filename, metadata)
    assert metadata.title == "Dir of HR"


def test_extract_metadata_from_filename_case_insensitivity(file_discovery_instance):
    filename = "ex-01 director operations 123456 - jd.txt"
    metadata = FileMetadata(file_path=Path(filename))
    file_discovery_instance._extract_metadata_from_filename(filename, metadata)
    assert metadata.classification == "EX-01"
    assert metadata.job_number == "123456"
    assert metadata.language == "en"
    assert metadata.title == "director operations"

    filename = "DE_ex-02_789012_directeur.txt"
    metadata = FileMetadata(file_path=Path(filename))
    file_discovery_instance._extract_metadata_from_filename(filename, metadata)
    assert metadata.language == "fr"
    assert metadata.title == "directeur"
