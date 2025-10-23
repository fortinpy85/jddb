import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from jd_ingestion.services.quality_service import QualityService
from jd_ingestion.database.models import (
    JobDescription,
    DataQualityMetrics,
    JobSection,
    JobMetadata,
    ContentChunk,
)


class TestQualityService:
    """Test suite for the QualityService class."""

    @pytest.fixture
    def quality_service(self):
        """Create a quality service instance for testing."""
        return QualityService()

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = AsyncMock(spec=AsyncSession)
        session.add = Mock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.flush = AsyncMock()
        session.execute = AsyncMock()
        session.scalar = AsyncMock()
        return session

    @pytest.fixture
    def complete_job_description(self):
        """Create a complete job description for testing."""
        job = JobDescription(
            id=123,
            title="Senior Software Developer",
            job_number="EX-01-12345",
            classification="EX-01",
            language="en",
            raw_content="This is a comprehensive job description with sufficient content "
            * 10,
        )

        # Add sections
        job.sections = [
            JobSection(
                section_type="general_accountability",
                section_content="General accountability content",
            ),
            JobSection(
                section_type="organization_structure",
                section_content="Organization structure content",
            ),
            JobSection(
                section_type="nature_and_scope",
                section_content="Nature and scope content",
            ),
            JobSection(
                section_type="specific_accountabilities",
                section_content="Specific accountabilities content",
            ),
            JobSection(section_type="dimensions", section_content="Dimensions content"),
            JobSection(
                section_type="knowledge_skills_abilities",
                section_content="Knowledge skills abilities content",
            ),
        ]

        # Add metadata (use job_metadata to match service)
        job.job_metadata = JobMetadata(
            reports_to="Director of Engineering",
            department="Information Technology",
            location="Ottawa, ON",
            fte_count=1.0,
            salary_budget=120000.00,
            effective_date=datetime.utcnow(),
        )

        # Add chunks
        job.chunks = [
            ContentChunk(
                chunk_text="Content chunk 1",
                chunk_index=0,
                embedding=[0.1, 0.2, 0.3],  # Mock embedding
            ),
            ContentChunk(
                chunk_text="Content chunk 2",
                chunk_index=1,
                embedding=[0.4, 0.5, 0.6],  # Mock embedding
            ),
        ]

        return job

    @pytest.fixture
    def incomplete_job_description(self):
        """Create an incomplete job description for testing."""
        job = JobDescription(
            id=456,
            title="Incomplete Job",
            job_number=None,
            classification=None,
            language="en",
            raw_content="Short content",
        )

        # Minimal sections
        job.sections = [
            JobSection(
                section_type="general_accountability",
                section_content="Basic content",
            ),
        ]

        # No metadata or chunks
        job.job_metadata = None
        job.chunks = []

        return job

    def test_quality_service_initialization(self, quality_service):
        """Test quality service initializes correctly."""
        assert quality_service is not None
        assert quality_service.calculation_version == "1.0"
        assert len(quality_service.EXPECTED_SECTIONS) == 6
        assert len(quality_service.REQUIRED_STRUCTURED_FIELDS) == 4

    @pytest.mark.asyncio
    async def test_calculate_quality_metrics_for_job_success(
        self, quality_service, mock_db_session, complete_job_description
    ):
        """Test successful quality metrics calculation for a job."""
        # Mock database response
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = complete_job_description
        mock_db_session.execute.return_value = mock_result

        # Mock existing metrics check
        mock_existing_result = Mock()
        mock_existing_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.side_effect = [mock_result, mock_existing_result]

        metrics = await quality_service.calculate_quality_metrics_for_job(
            mock_db_session, 123
        )

        # Verify metrics structure
        assert isinstance(metrics, dict)
        assert "content_completeness_score" in metrics
        assert "sections_completeness_score" in metrics
        assert "metadata_completeness_score" in metrics
        assert "has_structured_fields" in metrics
        assert "has_all_sections" in metrics
        assert "has_embeddings" in metrics
        assert "validation_results" in metrics
        assert "quality_flags" in metrics

        # Verify database interactions
        mock_db_session.execute.call_count >= 1
        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_quality_metrics_job_not_found(
        self, quality_service, mock_db_session
    ):
        """Test error handling when job is not found."""
        # Mock database response with no job
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Job with ID 999 not found"):
            await quality_service.calculate_quality_metrics_for_job(
                mock_db_session, 999
            )

    @pytest.mark.asyncio
    async def test_batch_calculate_quality_metrics_all_jobs(
        self, quality_service, mock_db_session
    ):
        """Test batch calculation for all jobs."""
        # Mock job IDs query
        mock_result = Mock()
        mock_result.fetchall.return_value = [(1,), (2,), (3,)]
        mock_db_session.execute.return_value = mock_result

        # Mock successful calculations
        with patch.object(
            quality_service, "calculate_quality_metrics_for_job"
        ) as mock_calc:
            mock_calc.return_value = {"test": "metrics"}

            results = await quality_service.batch_calculate_quality_metrics(
                mock_db_session
            )

            assert results["total_jobs"] == 3
            assert results["successful"] == 3
            assert results["failed"] == 0
            assert len(results["errors"]) == 0
            assert mock_calc.call_count == 3

        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_calculate_quality_metrics_specific_jobs(
        self, quality_service, mock_db_session
    ):
        """Test batch calculation for specific job IDs."""
        job_ids = [100, 200, 300]

        with patch.object(
            quality_service, "calculate_quality_metrics_for_job"
        ) as mock_calc:
            mock_calc.return_value = {"test": "metrics"}

            results = await quality_service.batch_calculate_quality_metrics(
                mock_db_session, job_ids
            )

            assert results["total_jobs"] == 3
            assert results["successful"] == 3
            assert results["failed"] == 0

    @pytest.mark.asyncio
    async def test_batch_calculate_with_failures(
        self, quality_service, mock_db_session
    ):
        """Test batch calculation handling individual job failures."""
        job_ids = [1, 2, 3]

        with patch.object(
            quality_service, "calculate_quality_metrics_for_job"
        ) as mock_calc:
            # Second job fails
            mock_calc.side_effect = [
                {"success": "metrics"},
                ValueError("Processing failed"),
                {"success": "metrics"},
            ]

            results = await quality_service.batch_calculate_quality_metrics(
                mock_db_session, job_ids
            )

            assert results["total_jobs"] == 3
            assert results["successful"] == 2
            assert results["failed"] == 1
            assert len(results["errors"]) == 1
            assert results["errors"][0]["job_id"] == 2

        # Should still commit successful ones
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_calculate_rollback_on_exception(
        self, quality_service, mock_db_session
    ):
        """Test batch calculation rollback on database exception."""
        mock_db_session.execute.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await quality_service.batch_calculate_quality_metrics(mock_db_session)

        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_quality_report_single_job(
        self, quality_service, mock_db_session
    ):
        """Test getting quality report for single job."""
        with patch.object(
            quality_service, "_get_single_job_quality_report"
        ) as mock_single:
            mock_single.return_value = {"job_id": 123, "overall_score": 0.85}

            result = await quality_service.get_quality_report(mock_db_session, 123)
            assert result["job_id"] == 123
            mock_single.assert_called_once_with(mock_db_session, 123)

    @pytest.mark.asyncio
    async def test_get_quality_report_system_wide(
        self, quality_service, mock_db_session
    ):
        """Test getting system-wide quality report."""
        with patch.object(quality_service, "_get_system_quality_report") as mock_system:
            mock_system.return_value = {"total_jobs_analyzed": 100}

            result = await quality_service.get_quality_report(mock_db_session)
            assert "total_jobs_analyzed" in result
            mock_system.assert_called_once_with(mock_db_session)

    def test_calculate_content_completeness_complete(
        self, quality_service, complete_job_description
    ):
        """Test content completeness calculation for complete job."""
        score = quality_service._calculate_content_completeness(
            complete_job_description
        )
        assert isinstance(score, Decimal)
        assert score == Decimal("1.000")  # All 4 components present

    def test_calculate_content_completeness_incomplete(
        self, quality_service, incomplete_job_description
    ):
        """Test content completeness calculation for incomplete job."""
        score = quality_service._calculate_content_completeness(
            incomplete_job_description
        )
        assert isinstance(score, Decimal)
        assert score == Decimal("0.250")  # Only 1 of 4 components present

    def test_calculate_sections_completeness_complete(
        self, quality_service, complete_job_description
    ):
        """Test sections completeness calculation for complete job."""
        score = quality_service._calculate_sections_completeness(
            complete_job_description
        )
        assert isinstance(score, Decimal)
        assert score == Decimal("1.000")  # All expected sections present

    def test_calculate_sections_completeness_partial(
        self, quality_service, incomplete_job_description
    ):
        """Test sections completeness calculation for partial job."""
        score = quality_service._calculate_sections_completeness(
            incomplete_job_description
        )
        assert isinstance(score, Decimal)
        assert float(score) < 1.0  # Only partial sections present

    def test_calculate_sections_completeness_no_sections(self, quality_service):
        """Test sections completeness when no sections exist."""
        job = JobDescription(sections=[])
        score = quality_service._calculate_sections_completeness(job)
        assert score == Decimal("0.000")

    def test_calculate_metadata_completeness_complete(
        self, quality_service, complete_job_description
    ):
        """Test metadata completeness calculation for complete metadata."""
        score = quality_service._calculate_job_metadata_completeness(
            complete_job_description
        )
        assert isinstance(score, Decimal)
        assert score == Decimal("1.000")  # All 6 metadata fields present

    def test_calculate_metadata_completeness_no_metadata(self, quality_service):
        """Test metadata completeness when no metadata exists."""
        job = JobDescription(job_metadata=None)
        score = quality_service._calculate_job_metadata_completeness(job)
        assert score == Decimal("0.000")

    def test_assess_structured_fields_complete(
        self, quality_service, complete_job_description
    ):
        """Test structured fields assessment for complete job."""
        result = quality_service._assess_structured_fields(complete_job_description)
        assert result == "complete"

    def test_assess_structured_fields_partial(self, quality_service):
        """Test structured fields assessment for partial job."""
        job = JobDescription(
            title="Test Job",
            job_number="123",
            classification=None,
            job_metadata=None,
        )
        result = quality_service._assess_structured_fields(job)
        assert result == "partial"

    def test_assess_structured_fields_missing(self, quality_service):
        """Test structured fields assessment for job with missing fields."""
        job = JobDescription(
            title=None, job_number=None, classification=None, job_metadata=None
        )
        result = quality_service._assess_structured_fields(job)
        assert result == "missing"

    def test_assess_sections_coverage_complete(
        self, quality_service, complete_job_description
    ):
        """Test sections coverage assessment for complete job."""
        result = quality_service._assess_sections_coverage(complete_job_description)
        assert result == "complete"

    def test_assess_sections_coverage_partial(
        self, quality_service, incomplete_job_description
    ):
        """Test sections coverage assessment for partial job."""
        result = quality_service._assess_sections_coverage(incomplete_job_description)
        assert result == "missing"  # Only 1 of 6 sections

    def test_assess_sections_coverage_no_sections(self, quality_service):
        """Test sections coverage when no sections exist."""
        job = JobDescription(sections=[])
        result = quality_service._assess_sections_coverage(job)
        assert result == "missing"

    def test_assess_embeddings_coverage_complete(
        self, quality_service, complete_job_description
    ):
        """Test embeddings coverage assessment for complete job."""
        result = quality_service._assess_embeddings_coverage(complete_job_description)
        assert result == "complete"

    def test_assess_embeddings_coverage_partial(self, quality_service):
        """Test embeddings coverage assessment for partial embeddings."""
        job = JobDescription()
        job.chunks = [
            ContentChunk(embedding=[0.1, 0.2, 0.3]),  # Has embedding
            ContentChunk(embedding=None),  # No embedding
        ]
        result = quality_service._assess_embeddings_coverage(job)
        assert result == "partial"

    def test_assess_embeddings_coverage_missing(self, quality_service):
        """Test embeddings coverage when no chunks exist."""
        job = JobDescription(chunks=[])
        result = quality_service._assess_embeddings_coverage(job)
        assert result == "missing"

    def test_assess_processing_quality_success(
        self, quality_service, complete_job_description
    ):
        """Test processing quality assessment for successful processing."""
        result = quality_service._assess_processing_quality(complete_job_description)

        assert "processing_errors_count" in result
        assert "validation_errors_count" in result
        assert "content_extraction_success" in result
        assert result["content_extraction_success"] == "success"

    def test_assess_processing_quality_failed(self, quality_service):
        """Test processing quality assessment for failed processing."""
        job = JobDescription(sections=[])
        result = quality_service._assess_processing_quality(job)
        assert result["content_extraction_success"] == "failed"

    def test_assess_processing_quality_partial(self, quality_service):
        """Test processing quality assessment for partial processing."""
        job = JobDescription()
        job.sections = [JobSection(section_type="test", section_content="content")]
        result = quality_service._assess_processing_quality(job)
        assert result["content_extraction_success"] == "partial"

    def test_analyze_content_characteristics(
        self, quality_service, complete_job_description
    ):
        """Test content characteristics analysis."""
        result = quality_service._analyze_content_characteristics(
            complete_job_description
        )

        assert "raw_content_length" in result
        assert "processed_content_length" in result
        assert "sections_extracted_count" in result
        assert "chunks_generated_count" in result

        assert result["raw_content_length"] > 0
        assert result["processed_content_length"] > 0
        assert result["sections_extracted_count"] == 6
        assert result["chunks_generated_count"] == 2

    def test_assess_language_quality_english(self, quality_service):
        """Test language quality assessment for English content."""
        job = JobDescription(
            language="en",
            raw_content="The software developer will be responsible for and with the team",
        )
        result = quality_service._assess_language_quality(job)

        assert "language_detection_confidence" in result
        assert "encoding_issues_detected" in result
        assert result["encoding_issues_detected"] == "none"
        assert float(result["language_detection_confidence"]) > 0.8

    def test_assess_language_quality_french(self, quality_service):
        """Test language quality assessment for French content."""
        job = JobDescription(
            language="fr", raw_content="Le développeur sera responsable de et pour les"
        )
        result = quality_service._assess_language_quality(job)
        assert float(result["language_detection_confidence"]) > 0.8

    def test_assess_language_quality_encoding_issues(self, quality_service):
        """Test language quality assessment with encoding issues."""
        job = JobDescription(
            language="en", raw_content="The developer� will work with Ã©ngineering"
        )
        result = quality_service._assess_language_quality(job)
        assert result["encoding_issues_detected"] == "major"

    def test_validate_content_complete_job(
        self, quality_service, complete_job_description
    ):
        """Test content validation for complete job."""
        result = quality_service._validate_content(complete_job_description)

        assert "errors" in result
        assert "warnings" in result
        assert "error_count" in result
        assert "warning_count" in result

        assert result["error_count"] == 0  # Complete job should have no errors
        assert isinstance(result["errors"], list)
        assert isinstance(result["warnings"], list)

    def test_validate_content_incomplete_job(
        self, quality_service, incomplete_job_description
    ):
        """Test content validation for incomplete job."""
        result = quality_service._validate_content(incomplete_job_description)

        assert result["error_count"] > 0
        assert "Missing job number" in result["errors"]
        assert "Missing classification" in result["errors"]

    def test_generate_quality_flags_high_quality(
        self, quality_service, complete_job_description
    ):
        """Test quality flags generation for high quality job."""
        validation_results = {"error_count": 0, "warning_count": 0}
        flags = quality_service._generate_quality_flags(
            complete_job_description, validation_results
        )

        assert flags["high_quality"] is True
        assert flags["needs_review"] is False
        assert flags["processing_issues"] is False
        assert flags["content_issues"] is False
        assert isinstance(flags["recommendations"], list)

    def test_generate_quality_flags_needs_review(self, quality_service):
        """Test quality flags generation for job needing review."""
        job = JobDescription(sections=[], chunks=[])
        validation_results = {"error_count": 2, "warning_count": 3}
        flags = quality_service._generate_quality_flags(job, validation_results)

        assert flags["high_quality"] is False
        assert flags["needs_review"] is True
        assert flags["processing_issues"] is True
        assert flags["content_issues"] is True
        assert len(flags["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_save_quality_metrics_new_record(
        self, quality_service, mock_db_session
    ):
        """Test saving new quality metrics record."""
        # Mock no existing metrics
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        metrics = {"content_completeness_score": Decimal("0.85")}

        await quality_service._save_quality_metrics(mock_db_session, 123, metrics)

        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_quality_metrics_update_existing(
        self, quality_service, mock_db_session
    ):
        """Test updating existing quality metrics record."""
        # Mock existing metrics
        existing_metrics = DataQualityMetrics(job_id=123)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = existing_metrics
        mock_db_session.execute.return_value = mock_result

        metrics = {"content_completeness_score": Decimal("0.90")}

        await quality_service._save_quality_metrics(mock_db_session, 123, metrics)

        # Should update existing, not add new
        mock_db_session.add.assert_not_called()
        mock_db_session.flush.assert_called_once()
        assert hasattr(existing_metrics, "last_calculated")

    @pytest.mark.asyncio
    async def test_get_single_job_quality_report(
        self, quality_service, mock_db_session
    ):
        """Test getting single job quality report."""
        # Mock quality metrics
        mock_metrics = DataQualityMetrics(
            job_id=123,
            content_completeness_score=Decimal("0.85"),
            sections_completeness_score=Decimal("0.90"),
            metadata_completeness_score=Decimal("0.75"),
            has_structured_fields="complete",
            has_all_sections="complete",
            has_embeddings="complete",
            content_extraction_success="success",
            processing_errors_count=0,
            validation_errors_count=0,
            raw_content_length=1500,
            processed_content_length=1200,
            sections_extracted_count=6,
            chunks_generated_count=5,
            language_detection_confidence=Decimal("0.95"),
            encoding_issues_detected="none",
            validation_results={"errors": [], "warnings": []},
            quality_flags={"high_quality": True},
            last_calculated=datetime.utcnow(),
        )

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_metrics
        mock_db_session.execute.return_value = mock_result

        report = await quality_service._get_single_job_quality_report(
            mock_db_session, 123
        )

        assert report["job_id"] == 123
        assert "overall_score" in report
        assert "completeness" in report
        assert "quality_indicators" in report
        assert "processing_quality" in report
        assert "content_characteristics" in report
        assert "language_quality" in report

    @pytest.mark.asyncio
    async def test_get_single_job_quality_report_not_found(
        self, quality_service, mock_db_session
    ):
        """Test getting quality report for job with no metrics."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(ValueError, match="No quality metrics found for job 999"):
            await quality_service._get_single_job_quality_report(mock_db_session, 999)

    @pytest.mark.asyncio
    async def test_get_system_quality_report(self, quality_service, mock_db_session):
        """Test getting system-wide quality report."""
        # Mock aggregated statistics
        mock_stats = Mock()
        mock_stats.total_jobs = 100
        mock_stats.avg_content_completeness = Decimal("0.85")
        mock_stats.avg_sections_completeness = Decimal("0.78")
        mock_stats.avg_metadata_completeness = Decimal("0.65")
        mock_stats.total_processing_errors = 5
        mock_stats.total_validation_errors = 12

        # Mock distribution data
        mock_distribution = [
            Mock(
                count=50,
                has_structured_fields="complete",
                has_all_sections="complete",
                has_embeddings="complete",
            ),
            Mock(
                count=30,
                has_structured_fields="partial",
                has_all_sections="partial",
                has_embeddings="partial",
            ),
            Mock(
                count=20,
                has_structured_fields="missing",
                has_all_sections="missing",
                has_embeddings="missing",
            ),
        ]

        mock_db_session.execute.side_effect = [
            Mock(first=Mock(return_value=mock_stats)),
            Mock(fetchall=Mock(return_value=mock_distribution)),
        ]

        report = await quality_service._get_system_quality_report(mock_db_session)

        assert "overview" in report
        assert "quality_distribution" in report
        assert "generated_at" in report
        assert report["overview"]["total_jobs_analyzed"] == 100
        assert len(report["quality_distribution"]) == 3

    @pytest.mark.asyncio
    async def test_calculate_metrics_complete_workflow(
        self, quality_service, complete_job_description
    ):
        """Test complete metrics calculation workflow."""
        metrics = await quality_service._calculate_metrics(complete_job_description)

        # Verify all expected metrics are present
        expected_keys = [
            "content_completeness_score",
            "sections_completeness_score",
            "metadata_completeness_score",
            "has_structured_fields",
            "has_all_sections",
            "has_embeddings",
            "processing_errors_count",
            "validation_errors_count",
            "content_extraction_success",
            "raw_content_length",
            "processed_content_length",
            "sections_extracted_count",
            "chunks_generated_count",
            "language_detection_confidence",
            "encoding_issues_detected",
            "validation_results",
            "quality_flags",
            "calculation_version",
        ]

        for key in expected_keys:
            assert key in metrics

        # Verify data types and values
        assert isinstance(metrics["content_completeness_score"], Decimal)
        assert isinstance(metrics["validation_results"], dict)
        assert isinstance(metrics["quality_flags"], dict)
        assert metrics["calculation_version"] == "1.0"

    # Additional edge case tests for improved coverage

    def test_calculate_content_completeness_edge_cases(self, quality_service):
        """Test content completeness with various edge cases."""
        # Job with exactly 100 chars (boundary)
        job = JobDescription(raw_content="x" * 100, sections=[], chunks=[])
        score = quality_service._calculate_content_completeness(job)
        assert score == Decimal("0.000")  # sections and chunks missing

        # Job with 99 chars (just below threshold)
        job = JobDescription(raw_content="x" * 99, sections=[], chunks=[])
        score = quality_service._calculate_content_completeness(job)
        assert score == Decimal("0.000")

        # Job with 101 chars (just above threshold)
        job = JobDescription(raw_content="x" * 101)
        job.sections = []
        job.chunks = []
        score = quality_service._calculate_content_completeness(job)
        assert score == Decimal("0.250")  # Only raw content present

    def test_calculate_metadata_completeness_partial(self, quality_service):
        """Test metadata completeness with partial metadata."""
        # Only 3 of 6 fields present
        job = JobDescription()
        job.job_metadata = JobMetadata(
            reports_to="Manager",
            department="IT",
            location="Ottawa",
            fte_count=None,
            salary_budget=None,
            effective_date=None,
        )
        score = quality_service._calculate_job_metadata_completeness(job)
        assert score == Decimal("0.500")  # 3/6 fields

        # Only 1 field present
        job.job_metadata = JobMetadata(
            reports_to="Manager",
            department=None,
            location=None,
            fte_count=None,
            salary_budget=None,
            effective_date=None,
        )
        score = quality_service._calculate_job_metadata_completeness(job)
        assert float(score) < 0.2  # 1/6 fields

    def test_calculate_metadata_completeness_empty_strings(self, quality_service):
        """Test metadata completeness with empty strings."""
        job = JobDescription()
        job.job_metadata = JobMetadata(
            reports_to="",  # Empty string should not count
            department="  ",  # Whitespace only should not count
            location="Ottawa",
            fte_count=0,  # Zero should count
            salary_budget=0.0,  # Zero should count
            effective_date=datetime.utcnow(),
        )
        score = quality_service._calculate_job_metadata_completeness(job)
        assert score == Decimal("0.667")  # 4/6 fields (location, fte, salary, date)

    def test_assess_sections_coverage_boundary_80_percent(self, quality_service):
        """Test sections coverage at 80% boundary (complete threshold)."""
        job = JobDescription()
        # Provide exactly 5 of 6 expected sections (83.3%)
        job.sections = [
            JobSection(
                section_type="general_accountability", section_content="content"
            ),
            JobSection(
                section_type="organization_structure", section_content="content"
            ),
            JobSection(section_type="nature_and_scope", section_content="content"),
            JobSection(
                section_type="specific_accountabilities", section_content="content"
            ),
            JobSection(section_type="dimensions", section_content="content"),
        ]
        result = quality_service._assess_sections_coverage(job)
        assert result == "complete"  # 5/6 = 0.833 >= 0.8

    def test_assess_sections_coverage_boundary_40_percent(self, quality_service):
        """Test sections coverage at 40% boundary (partial threshold)."""
        job = JobDescription()
        # Provide exactly 2 of 6 expected sections (33.3%)
        job.sections = [
            JobSection(
                section_type="general_accountability", section_content="content"
            ),
            JobSection(
                section_type="organization_structure", section_content="content"
            ),
        ]
        result = quality_service._assess_sections_coverage(job)
        assert result == "missing"  # 2/6 = 0.333 < 0.4

        # Provide 3 of 6 (50%)
        job.sections.append(
            JobSection(section_type="nature_and_scope", section_content="content")
        )
        result = quality_service._assess_sections_coverage(job)
        assert result == "partial"  # 3/6 = 0.5 >= 0.4

    def test_assess_embeddings_coverage_boundary_cases(self, quality_service):
        """Test embeddings coverage at boundary conditions."""
        job = JobDescription()

        # Exactly 50% coverage (boundary for partial)
        job.chunks = [
            ContentChunk(embedding=[0.1, 0.2]),
            ContentChunk(embedding=None),
        ]
        result = quality_service._assess_embeddings_coverage(job)
        assert result == "partial"

        # Just below 50%
        job.chunks = [
            ContentChunk(embedding=[0.1, 0.2]),
            ContentChunk(embedding=None),
            ContentChunk(embedding=None),
        ]
        result = quality_service._assess_embeddings_coverage(job)
        assert result == "missing"  # 1/3 = 0.333 < 0.5

    def test_assess_embeddings_coverage_all_none(self, quality_service):
        """Test embeddings coverage when chunks exist but all embeddings are None."""
        job = JobDescription()
        job.chunks = [
            ContentChunk(embedding=None),
            ContentChunk(embedding=None),
            ContentChunk(embedding=None),
        ]
        result = quality_service._assess_embeddings_coverage(job)
        assert result == "missing"  # 0/3 = 0

    def test_assess_processing_quality_exactly_3_sections(self, quality_service):
        """Test processing quality with exactly 3 sections (boundary)."""
        job = JobDescription()
        job.sections = [
            JobSection(section_type="section1", section_content="content"),
            JobSection(section_type="section2", section_content="content"),
            JobSection(section_type="section3", section_content="content"),
        ]
        result = quality_service._assess_processing_quality(job)
        assert result["content_extraction_success"] == "success"  # >= 3 sections

    def test_assess_processing_quality_two_sections(self, quality_service):
        """Test processing quality with 2 sections."""
        job = JobDescription()
        job.sections = [
            JobSection(section_type="section1", section_content="content"),
            JobSection(section_type="section2", section_content="content"),
        ]
        result = quality_service._assess_processing_quality(job)
        assert result["content_extraction_success"] == "partial"  # < 3 sections

    def test_analyze_content_characteristics_empty_sections(self, quality_service):
        """Test content characteristics with empty section content."""
        job = JobDescription(raw_content="test content")
        job.sections = [
            JobSection(section_type="test", section_content=None),
            JobSection(section_type="test2", section_content=""),
            JobSection(section_type="test3", section_content="valid"),
        ]
        job.chunks = []

        result = quality_service._analyze_content_characteristics(job)
        assert result["raw_content_length"] == 12
        assert result["processed_content_length"] == 5  # Only "valid"
        assert result["sections_extracted_count"] == 3
        assert result["chunks_generated_count"] == 0

    def test_assess_language_quality_no_language(self, quality_service):
        """Test language quality when language is not set."""
        job = JobDescription(language=None, raw_content="test content")
        result = quality_service._assess_language_quality(job)
        assert result["language_detection_confidence"] == Decimal("0.800")
        assert result["encoding_issues_detected"] == "none"

    def test_assess_language_quality_short_content(self, quality_service):
        """Test language quality with insufficient content for analysis."""
        job = JobDescription(language="en", raw_content="test")
        result = quality_service._assess_language_quality(job)
        # Should still return confidence even with short content
        assert "language_detection_confidence" in result
        assert result["encoding_issues_detected"] == "none"

    def test_assess_language_quality_language_mismatch_french(self, quality_service):
        """Test language quality with French labeled as English."""
        job = JobDescription(
            language="en",
            raw_content="Le développeur sera responsable de la création des applications pour les clients et les utilisateurs dans le système",
        )
        result = quality_service._assess_language_quality(job)
        assert (
            float(result["language_detection_confidence"]) < 0.5
        )  # Should detect mismatch

    def test_assess_language_quality_language_mismatch_english(self, quality_service):
        """Test language quality with English labeled as French."""
        job = JobDescription(
            language="fr",
            raw_content="The developer will be responsible for creating applications for the clients and users in the system",
        )
        result = quality_service._assess_language_quality(job)
        assert (
            float(result["language_detection_confidence"]) < 0.5
        )  # Should detect mismatch

    def test_assess_language_quality_minor_encoding_issues(self, quality_service):
        """Test language quality with minor encoding issues."""
        job = JobDescription(
            language="fr", raw_content="Le dÃ©veloppeur avec expÃ©rience en Ã©quipe"
        )
        result = quality_service._assess_language_quality(job)
        assert result["encoding_issues_detected"] == "minor"

    def test_validate_content_long_content_warning(self, quality_service):
        """Test content validation with unusually long content."""
        job = JobDescription(
            title="Test",
            job_number="123",
            classification="EX-01",
            raw_content="x" * 100001,  # Over 100KB
        )
        job.sections = [JobSection(section_type="test", section_content="content")]
        job.chunks = [ContentChunk(chunk_text="test", chunk_index=0)]

        result = quality_service._validate_content(job)
        assert "Raw content unusually long" in result["warnings"]

    def test_validate_content_multiple_errors(self, quality_service):
        """Test content validation accumulating multiple errors."""
        job = JobDescription(
            title=None,
            job_number=None,
            classification=None,
            raw_content="short",  # Too short
        )
        job.sections = []
        job.chunks = []

        result = quality_service._validate_content(job)
        assert result["error_count"] >= 5
        assert "Missing job number" in result["errors"]
        assert "Missing job title" in result["errors"]
        assert "Missing classification" in result["errors"]
        assert "Raw content too short or missing" in result["errors"]
        assert "No sections extracted" in result["errors"]
        assert "No content chunks generated" in result["errors"]

    def test_validate_content_chunks_without_embeddings(self, quality_service):
        """Test validation warning for chunks without embeddings."""
        job = JobDescription(
            title="Test",
            job_number="123",
            classification="EX-01",
            raw_content="x" * 200,
        )
        job.sections = [JobSection(section_type="test", section_content="content")]
        job.chunks = [
            ContentChunk(chunk_text="test1", chunk_index=0, embedding=[0.1, 0.2]),
            ContentChunk(chunk_text="test2", chunk_index=1, embedding=None),
            ContentChunk(chunk_text="test3", chunk_index=2, embedding=None),
        ]

        result = quality_service._validate_content(job)
        assert "2 chunks missing embeddings" in result["warnings"]

    def test_generate_quality_flags_all_issues(self, quality_service):
        """Test quality flags with all possible issues."""
        job = JobDescription()
        job.sections = []
        job.chunks = []

        validation_results = {
            "error_count": 5,
            "warning_count": 10,
            "errors": ["error1", "error2"],
            "warnings": ["warn1", "warn2", "warn3"],
        }

        flags = quality_service._generate_quality_flags(job, validation_results)
        assert flags["high_quality"] is False
        assert flags["needs_review"] is True
        assert flags["processing_issues"] is True
        assert flags["content_issues"] is True
        assert "Review processing errors" in flags["recommendations"]
        assert "Consider reprocessing file" in flags["recommendations"]
        assert "Review section extraction" in flags["recommendations"]
        assert "Generate content chunks" in flags["recommendations"]
        assert "Review content quality warnings" in flags["recommendations"]

    def test_generate_quality_flags_missing_embeddings_only(self, quality_service):
        """Test quality flags for job with missing embeddings."""
        job = JobDescription()
        job.sections = [
            JobSection(section_type="test1", section_content="content"),
            JobSection(section_type="test2", section_content="content"),
            JobSection(section_type="test3", section_content="content"),
        ]
        job.chunks = [
            ContentChunk(chunk_text="test", chunk_index=0, embedding=None),
        ]

        validation_results = {"error_count": 0, "warning_count": 1}
        flags = quality_service._generate_quality_flags(job, validation_results)
        assert "Generate missing embeddings" in flags["recommendations"]

    def test_generate_quality_flags_two_warnings_no_review(self, quality_service):
        """Test quality flags with exactly 2 warnings (below review threshold)."""
        job = JobDescription()
        job.sections = [JobSection(section_type="test", section_content="content")]
        job.chunks = [ContentChunk(chunk_text="test", chunk_index=0)]

        validation_results = {"error_count": 0, "warning_count": 2}
        flags = quality_service._generate_quality_flags(job, validation_results)
        assert flags["needs_review"] is False  # <= 2 warnings

    def test_generate_quality_flags_three_warnings_needs_review(self, quality_service):
        """Test quality flags with exactly 3 warnings (at review threshold)."""
        job = JobDescription()
        job.sections = [JobSection(section_type="test", section_content="content")]
        job.chunks = [ContentChunk(chunk_text="test", chunk_index=0)]

        validation_results = {"error_count": 0, "warning_count": 3}
        flags = quality_service._generate_quality_flags(job, validation_results)
        assert flags["needs_review"] is True  # > 2 warnings
        assert "Review content quality warnings" in flags["recommendations"]

    @pytest.mark.asyncio
    async def test_get_system_quality_report_empty_database(
        self, quality_service, mock_db_session
    ):
        """Test system quality report with no data."""
        # Mock empty stats
        mock_stats = Mock()
        mock_stats.total_jobs = 0
        mock_stats.avg_content_completeness = None
        mock_stats.avg_sections_completeness = None
        mock_stats.avg_metadata_completeness = None
        mock_stats.total_processing_errors = None
        mock_stats.total_validation_errors = None

        mock_db_session.execute.side_effect = [
            Mock(first=Mock(return_value=mock_stats)),
            Mock(fetchall=Mock(return_value=[])),
        ]

        report = await quality_service._get_system_quality_report(mock_db_session)

        assert report["overview"]["total_jobs_analyzed"] == 0
        assert report["overview"]["average_content_completeness"] == 0.0
        assert report["overview"]["total_processing_errors"] == 0
        assert len(report["quality_distribution"]) == 0

    @pytest.mark.asyncio
    async def test_batch_calculate_all_failures(self, quality_service, mock_db_session):
        """Test batch calculation when all jobs fail."""
        job_ids = [1, 2, 3]

        with patch.object(
            quality_service, "calculate_quality_metrics_for_job"
        ) as mock_calc:
            mock_calc.side_effect = ValueError("Processing failed")

            results = await quality_service.batch_calculate_quality_metrics(
                mock_db_session, job_ids
            )

            assert results["total_jobs"] == 3
            assert results["successful"] == 0
            assert results["failed"] == 3
            assert len(results["errors"]) == 3

    @pytest.mark.asyncio
    async def test_calculate_quality_metrics_for_job_database_error(
        self, quality_service, mock_db_session
    ):
        """Test error handling during database operations."""
        mock_db_session.execute.side_effect = Exception("Database connection lost")

        with pytest.raises(Exception, match="Database connection lost"):
            await quality_service.calculate_quality_metrics_for_job(
                mock_db_session, 123
            )

    @pytest.mark.asyncio
    async def test_get_quality_report_error_handling(
        self, quality_service, mock_db_session
    ):
        """Test error handling in get_quality_report."""
        mock_db_session.execute.side_effect = Exception("Query failed")

        with pytest.raises(Exception, match="Query failed"):
            await quality_service.get_quality_report(mock_db_session, 123)

    def test_assess_structured_fields_with_whitespace(self, quality_service):
        """Test structured fields assessment with whitespace-only values."""
        job = JobDescription(
            title="  ",  # Whitespace only
            job_number="   ",
            classification="EX-01",  # Valid
        )
        job.job_metadata = JobMetadata(department="IT")  # Valid

        result = quality_service._assess_structured_fields(job)
        assert result == "partial"  # Only 2 of 4 fields valid

    def test_calculate_sections_completeness_case_insensitive(self, quality_service):
        """Test sections completeness is case-insensitive."""
        job = JobDescription()
        job.sections = [
            JobSection(
                section_type="GENERAL_ACCOUNTABILITY", section_content="content"
            ),
            JobSection(
                section_type="Organization_Structure", section_content="content"
            ),
            JobSection(section_type="nature_and_scope", section_content="content"),
            JobSection(
                section_type="SPECIFIC_ACCOUNTABILITIES", section_content="content"
            ),
            JobSection(section_type="Dimensions", section_content="content"),
            JobSection(
                section_type="Knowledge_Skills_Abilities", section_content="content"
            ),
        ]

        score = quality_service._calculate_sections_completeness(job)
        assert score == Decimal(
            "1.000"
        )  # All sections should match despite case differences

    @pytest.mark.asyncio
    async def test_calculate_metrics_integration(
        self, quality_service, complete_job_description
    ):
        """Test _calculate_metrics with various completeness levels."""
        metrics = await quality_service._calculate_metrics(complete_job_description)

        # Verify overall quality for complete job
        assert float(metrics["content_completeness_score"]) == 1.0
        assert float(metrics["sections_completeness_score"]) == 1.0
        assert float(metrics["metadata_completeness_score"]) == 1.0
        assert metrics["has_structured_fields"] == "complete"
        assert metrics["has_all_sections"] == "complete"
        assert metrics["has_embeddings"] == "complete"
        assert metrics["content_extraction_success"] == "success"
