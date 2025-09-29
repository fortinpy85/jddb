import pytest
from pathlib import Path
from jd_ingestion.processors.content_processor import (
    ContentProcessor,
    ProcessedContent,
)
from jd_ingestion.core.file_discovery import (
    FileDiscovery,
    FileMetadata,
)  # Import FileDiscovery for relevant tests


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
ContentProcessor.logger = MockLogger()
FileDiscovery.logger = MockLogger()  # Also mock FileDiscovery's logger


@pytest.fixture
def processor(sample_job_description_text):
    """Fixture for ContentProcessor instance with sample content."""
    return ContentProcessor(raw_content=sample_job_description_text, language="en")


@pytest.fixture
def empty_processor():
    """Fixture for ContentProcessor instance with empty content."""
    return ContentProcessor(raw_content="", language="en")


@pytest.fixture
def file_discovery_instance():
    """Fixture for FileDiscovery instance."""
    return FileDiscovery(
        data_directory=Path("/tmp/dummy_data")
    )  # Dummy path for testing


@pytest.mark.unit
def test_extract_sections_basic(processor):
    """Test basic section extraction."""
    sections = processor.extract_sections()
    assert "GENERAL ACCOUNTABILITY" in sections
    assert "SPECIFIC ACCOUNTABILITIES" in sections
    assert "ORGANIZATION STRUCTURE" in sections
    assert len(sections) >= 3  # Ensure at least these core sections are found


@pytest.mark.unit
def test_extract_sections_empty_content(empty_processor):
    """Test section extraction with empty content."""
    sections = empty_processor.extract_sections()
    assert not sections  # No sections should be extracted from empty content


@pytest.mark.unit
def test_extract_sections_no_matches(empty_processor):
    """Test section extraction with no matching sections."""
    empty_processor.raw_content = (
        "This is just random text with no structured sections."
    )
    sections = empty_processor.extract_sections()
    assert not sections  # No sections should be extracted


@pytest.mark.unit
def test_identify_language_english(processor):
    """Test language identification for English content."""
    assert processor.identify_language() == "en"


@pytest.mark.unit
def test_identify_language_french():
    """Test language identification for French content."""
    french_processor = ContentProcessor(raw_content="Contenu français", language="fr")
    assert french_processor.identify_language() == "fr"


@pytest.mark.unit
def test_identify_language_empty(empty_processor):
    """Test language identification with empty content."""
    assert empty_processor.identify_language() == "en"  # Default language


@pytest.mark.unit
def test_parse_structured_fields_reports_to(processor):
    """Test parsing of 'Reports to' field."""
    fields = processor.parse_structured_fields()
    assert fields["reports_to"] == "Director General, Strategic Planning"


@pytest.mark.unit
def test_parse_structured_fields_supervises(processor):
    """Test parsing of 'Supervises' field."""
    fields = processor.parse_structured_fields()
    assert fields["fte_count"] == 12  # From "Supervises: 12 FTE"


@pytest.mark.unit
def test_parse_structured_fields_budget(processor):
    """Test parsing of budget information."""
    fields = processor.parse_structured_fields()
    assert (
        fields["salary_budget"] == 2300000.0
    )  # From "Budget Authority: $2.3M annually"


@pytest.mark.unit
def test_parse_structured_fields_no_matches(empty_processor):
    """Test structured field parsing with no matches."""
    empty_processor.raw_content = "Random text without structured fields."
    fields = empty_processor.parse_structured_fields()
    # Check that all fields are None or default empty values
    assert all(
        value is None or value == "" or value == 0
        for key, value in fields.items()
        if key not in ["position_title", "department", "location", "effective_date"]
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_content_success(processor):
    """Test successful content processing."""
    processed_content = processor.process_content(
        processor.raw_content, processor.language
    )
    assert isinstance(processed_content, ProcessedContent)
    assert processed_content.cleaned_content != ""
    assert "GENERAL ACCOUNTABILITY" in processed_content.sections
    assert (
        processed_content.structured_fields.reports_to
        == "Director General, Strategic Planning"
    )
    assert not processed_content.processing_errors


@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_content_empty(empty_processor):
    """Test processing empty content."""
    processed_content = empty_processor.process_content(
        empty_processor.raw_content, empty_processor.language
    )
    assert isinstance(processed_content, ProcessedContent)
    assert processed_content.cleaned_content == ""
    assert not processed_content.sections
    assert not processed_content.processing_errors


@pytest.mark.unit
def test_chunk_content_basic(processor):
    """Test chunk creation from content."""
    chunks = processor.chunk_content(
        "This is a test sentence. This is another sentence. And a third one.",
        chunk_size=20,
        overlap=5,
    )
    assert len(chunks) > 1
    assert isinstance(chunks[0], str)


@pytest.mark.unit
def test_chunk_content_custom_size(processor):
    """Test chunk creation with custom size."""
    chunks = processor.chunk_content(
        "This is a test sentence. This is another sentence. And a third one.",
        chunk_size=30,  # Use character-based size
        overlap=5,
    )
    assert len(chunks) > 1
    assert len(chunks[0]) <= 30  # Check character length, not word count


@pytest.mark.unit
def test_chunk_content_with_overlap(processor):
    """Test chunk creation with overlap."""
    content = "This is a test sentence. This is another sentence."
    chunks = processor.chunk_content(content, chunk_size=25, overlap=10)
    assert len(chunks) > 1
    # Check for overlap in content - with character-based overlap,
    # later chunks should contain some characters from the previous chunk
    assert len(chunks) >= 2


@pytest.mark.unit
@pytest.mark.benchmark
def test_process_large_file_performance(processor, sample_job_description_text):
    """Test processing of large content for performance."""
    large_content = sample_job_description_text * 100  # Create a large content string
    result = processor.process_content(large_content, "en")
    assert result is not None
    assert hasattr(result, "cleaned_content")
    assert result.cleaned_content is not None
    assert len(result.cleaned_content) > 0


# Tests for FileDiscovery methods that were previously in ContentProcessor tests
@pytest.mark.unit
def test_file_discovery_extract_metadata_from_filename_pattern1(
    file_discovery_instance,
):
    # Pattern: "EX-01 Dir, Business Analysis 103249 - JD.txt"
    filename = "EX-01 Dir, Business Analysis 103249 - JD.txt"
    metadata = FileMetadata(file_path=Path(filename))
    file_discovery_instance._extract_metadata_from_filename(filename, metadata)

    assert metadata.classification == "EX-01"
    assert metadata.job_number == "103249"
    assert metadata.language == "en"
    assert metadata.title == "Dir Business Analysis"
    assert not metadata.validation_errors


@pytest.mark.unit
def test_file_discovery_extract_metadata_from_filename_pattern2(
    file_discovery_instance,
):
    # Pattern: "JD_EX-01_123456_Director.txt"
    filename = "JD_EX-01_123456_Director.txt"
    metadata = FileMetadata(file_path=Path(filename))
    file_discovery_instance._extract_metadata_from_filename(filename, metadata)

    assert metadata.classification == "EX-01"
    assert metadata.job_number == "123456"
    assert metadata.language == "en"
    assert metadata.title == "Director"
    assert not metadata.validation_errors


@pytest.mark.unit
def test_file_discovery_extract_metadata_from_filename_pattern2_no_title(
    file_discovery_instance,
):
    # Pattern: "JD_EX-01_123456.txt"
    filename = "JD_EX-01_123456.txt"
    metadata = FileMetadata(file_path=Path(filename))
    file_discovery_instance._extract_metadata_from_filename(filename, metadata)

    assert metadata.classification == "EX-01"
    assert metadata.job_number == "123456"
    assert metadata.language == "en"
    assert metadata.title is None
    assert not metadata.validation_errors


@pytest.mark.unit
def test_file_discovery_extract_metadata_from_filename_pattern3(
    file_discovery_instance,
):
    # Pattern: "Director Business Analysis EX-01 103249.txt"
    filename = "Director Business Analysis EX-01 103249.txt"
    metadata = FileMetadata(file_path=Path(filename))
    file_discovery_instance._extract_metadata_from_filename(filename, metadata)

    assert metadata.classification == "EX-01"
    assert metadata.job_number == "103249"
    assert metadata.language == "en"  # Default language
    assert metadata.title == "Director Business Analysis"
    assert not metadata.validation_errors


@pytest.mark.unit
def test_file_discovery_extract_metadata_from_filename_pattern3_with_lang_code(
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


@pytest.mark.unit
def test_file_discovery_extract_metadata_from_filename_unrecognized_pattern(
    file_discovery_instance,
):
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


@pytest.mark.unit
def test_file_discovery_extract_metadata_from_filename_partial_match(
    file_discovery_instance,
):
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


@pytest.mark.unit
def test_file_discovery_extract_metadata_from_filename_title_cleanup(
    file_discovery_instance,
):
    filename = "EX-01 Dir_of_IT, 100000 - JD.txt"
    metadata = FileMetadata(file_path=Path(filename))
    file_discovery_instance._extract_metadata_from_filename(filename, metadata)
    assert metadata.title == "Dir of IT"

    filename = "EX-01  Dir   of   HR  100001 - JD.txt"
    metadata = FileMetadata(file_path=Path(filename))
    file_discovery_instance._extract_metadata_from_filename(filename, metadata)
    assert metadata.title == "Dir of HR"


@pytest.mark.unit
def test_file_discovery_extract_metadata_from_filename_case_insensitivity(
    file_discovery_instance,
):
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
