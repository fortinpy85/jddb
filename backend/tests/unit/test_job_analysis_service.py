import pytest
import json
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from jd_ingestion.services.job_analysis_service import JobAnalysisService
from jd_ingestion.database.models import (
    JobDescription,
    ContentChunk,
    JobComparison,
    JobSkill,
    JobSection,
    JobMetadata,
)


class TestJobAnalysisService:
    """Test suite for the JobAnalysisService class."""

    @pytest.fixture
    def job_analysis_service(self):
        """Create a job analysis service instance for testing."""
        with patch(
            "jd_ingestion.services.job_analysis_service.settings"
        ) as mock_settings:
            mock_settings.openai_api_key = "test-api-key"
            return JobAnalysisService()

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = AsyncMock(spec=AsyncSession)
        session.add = Mock()
        session.commit = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def sample_job_a(self):
        """Create a sample job description A."""
        job = JobDescription(
            id=1,
            title="Senior Software Developer",
            classification="EX-01",
            language="en",
        )

        job.sections = [
            JobSection(
                section_type="specific_accountabilities",
                section_content="Develop Python applications using Django framework",
            ),
            JobSection(
                section_type="knowledge_skills_abilities",
                section_content="Python programming, Django, REST APIs, database design",
            ),
        ]

        job.metadata_entry = JobMetadata(
            department="Information Technology",
            salary_budget=120000.00,
            fte_count=1.0,
        )

        job.chunks = [
            ContentChunk(
                job_id=1,
                chunk_text="Python development content",
                embedding=[0.1, 0.2, 0.3] * 512,  # Mock 1536-dim embedding
            )
        ]

        return job

    @pytest.fixture
    def sample_job_b(self):
        """Create a sample job description B."""
        job = JobDescription(
            id=2,
            title="Full Stack Developer",
            classification="IT-02",
            language="en",
        )

        job.sections = [
            JobSection(
                section_type="specific_accountabilities",
                section_content="Build web applications using React and Node.js",
            ),
            JobSection(
                section_type="knowledge_skills_abilities",
                section_content="JavaScript, React, Node.js, MongoDB, REST APIs",
            ),
        ]

        job.metadata_entry = JobMetadata(
            department="Information Technology",
            salary_budget=110000.00,
            fte_count=1.0,
        )

        job.chunks = [
            ContentChunk(
                job_id=2,
                chunk_text="JavaScript development content",
                embedding=[0.2, 0.3, 0.4] * 512,  # Mock 1536-dim embedding
            )
        ]

        return job

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client."""
        client = AsyncMock()

        # Mock embeddings response
        embedding_response = Mock()
        embedding_response.data = [Mock()]
        embedding_response.data[0].embedding = [0.1, 0.2, 0.3] * 512  # 1536-dim
        client.embeddings.create.return_value = embedding_response

        # Mock chat completion response
        completion_response = Mock()
        completion_response.choices = [Mock()]
        completion_response.choices[0].message.content = json.dumps(
            {
                "key_differences": [
                    "Different tech stack",
                    "Different seniority",
                    "Different focus",
                ],
                "recommendation": "Transition is feasible with additional training",
            }
        )
        client.chat.completions.create.return_value = completion_response

        return client

    def test_job_analysis_service_initialization(self, job_analysis_service):
        """Test job analysis service initializes correctly."""
        assert job_analysis_service is not None
        assert hasattr(job_analysis_service, "openai_client")

    @pytest.mark.asyncio
    async def test_compare_jobs_basic(
        self,
        job_analysis_service,
        mock_db_session,
        sample_job_a,
        sample_job_b,
        mock_openai_client,
    ):
        """Test basic job comparison functionality."""
        job_analysis_service.openai_client = mock_openai_client

        # Mock database query results
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_job_a, sample_job_b]
        mock_db_session.execute.return_value = mock_result

        # Mock embedding similarity calculation
        with patch.object(
            job_analysis_service, "_calculate_embedding_similarity", return_value=0.75
        ):
            with patch.object(job_analysis_service, "_cache_comparison"):
                result = await job_analysis_service.compare_jobs(
                    mock_db_session, 1, 2, comparison_types=["similarity"]
                )

        assert "job_a" in result
        assert "job_b" in result
        assert "analyses" in result
        assert "similarity" in result["analyses"]
        assert result["job_a"]["id"] == 1
        assert result["job_b"]["id"] == 2

    @pytest.mark.asyncio
    async def test_compare_jobs_not_found(self, job_analysis_service, mock_db_session):
        """Test job comparison when jobs are not found."""
        # Mock empty database result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(ValueError, match="One or both jobs not found"):
            await job_analysis_service.compare_jobs(mock_db_session, 1, 2)

    @pytest.mark.asyncio
    async def test_compare_jobs_all_types(
        self,
        job_analysis_service,
        mock_db_session,
        sample_job_a,
        sample_job_b,
        mock_openai_client,
    ):
        """Test job comparison with all comparison types."""
        job_analysis_service.openai_client = mock_openai_client

        # Mock database query results
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_job_a, sample_job_b]
        mock_db_session.execute.return_value = mock_result

        # Mock all analysis methods
        with patch.object(
            job_analysis_service,
            "_analyze_similarity",
            return_value={"overall_similarity": 0.75},
        ):
            with patch.object(
                job_analysis_service,
                "_analyze_skill_gap",
                return_value={"gap_score": 0.60},
            ):
                with patch.object(
                    job_analysis_service,
                    "_analyze_requirements_match",
                    return_value={"overall_match_score": 0.80},
                ):
                    with patch.object(job_analysis_service, "_cache_comparison"):
                        result = await job_analysis_service.compare_jobs(
                            mock_db_session,
                            1,
                            2,
                            comparison_types=[
                                "similarity",
                                "skill_gap",
                                "requirements",
                            ],
                        )

        assert len(result["analyses"]) == 3
        assert "similarity" in result["analyses"]
        assert "skill_gap" in result["analyses"]
        assert "requirements" in result["analyses"]

    @pytest.mark.asyncio
    async def test_analyze_similarity(
        self,
        job_analysis_service,
        mock_db_session,
        sample_job_a,
        sample_job_b,
        mock_openai_client,
    ):
        """Test similarity analysis between two jobs."""
        job_analysis_service.openai_client = mock_openai_client

        with patch.object(
            job_analysis_service, "_calculate_embedding_similarity", return_value=0.75
        ):
            with patch.object(
                job_analysis_service,
                "_calculate_section_similarities",
                return_value={"technical": 0.80},
            ):
                with patch.object(
                    job_analysis_service,
                    "_generate_similarity_insights",
                    return_value=(["diff1"], "recommendation"),
                ):
                    result = await job_analysis_service._analyze_similarity(
                        mock_db_session, sample_job_a, sample_job_b, True
                    )

        assert "overall_similarity" in result
        assert "section_similarities" in result
        assert "metadata_comparison" in result
        assert "key_differences" in result
        assert "recommendation" in result
        assert "similarity_level" in result
        assert result["overall_similarity"] == 0.75

    @pytest.mark.asyncio
    async def test_analyze_skill_gap(
        self, job_analysis_service, mock_db_session, sample_job_a, sample_job_b
    ):
        """Test skill gap analysis between two jobs."""
        # Mock skill extraction
        skills_a = [
            {
                "name": "Python",
                "category": "technical",
                "level": "required",
                "confidence": 0.9,
            },
            {
                "name": "Django",
                "category": "technical",
                "level": "required",
                "confidence": 0.8,
            },
        ]
        skills_b = [
            {
                "name": "JavaScript",
                "category": "technical",
                "level": "required",
                "confidence": 0.9,
            },
            {
                "name": "React",
                "category": "technical",
                "level": "required",
                "confidence": 0.8,
            },
        ]

        with patch.object(job_analysis_service, "extract_job_skills") as mock_extract:
            mock_extract.side_effect = [skills_a, skills_b]

            # Mock the missing method to return empty list
            with patch.object(
                job_analysis_service,
                "_generate_skill_development_recommendations",
                return_value=[],
            ):
                result = await job_analysis_service._analyze_skill_gap(
                    mock_db_session, sample_job_a, sample_job_b, include_details=False
                )

        assert "skills_job_a" in result
        assert "skills_job_b" in result
        assert "matching_skills" in result
        assert "missing_skills" in result
        assert "development_recommendations" in result
        assert "skill_gap_score" in result

    @pytest.mark.asyncio
    async def test_analyze_requirements_match(
        self, job_analysis_service, mock_db_session, sample_job_a, sample_job_b
    ):
        """Test requirements matching analysis."""
        # Mock all missing methods for requirements analysis
        with patch.object(
            job_analysis_service,
            "_extract_requirements",
            side_effect=[["req1", "req2"], ["req1", "req3"]],
        ):
            with patch.object(
                job_analysis_service,
                "_calculate_requirement_matches",
                return_value={"overall_score": 0.70},
            ):
                with patch.object(
                    job_analysis_service,
                    "_generate_requirement_insights",
                    return_value=["insight1"],
                ):
                    result = await job_analysis_service._analyze_requirements_match(
                        mock_db_session,
                        sample_job_a,
                        sample_job_b,
                        include_details=False,
                    )

        assert "overall_match_score" in result
        assert "education_match" in result
        assert "experience_match" in result
        assert "technical_skills_match" in result
        assert "soft_skills_match" in result
        assert "matching_insights" in result
        assert "match_level" in result

    @pytest.mark.asyncio
    async def test_extract_job_skills_cached(
        self, job_analysis_service, mock_db_session
    ):
        """Test skill extraction with cached results."""
        # Mock cached skills
        cached_skills = [
            JobSkill(
                skill_category="technical",
                skill_name="Python",
                skill_level="required",
                confidence_score=0.9,
                extracted_from_section="technical",
            )
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = cached_skills
        mock_db_session.execute.return_value = mock_result

        result = await job_analysis_service.extract_job_skills(mock_db_session, 1)

        assert len(result) == 1
        assert result[0]["name"] == "Python"
        assert result[0]["category"] == "technical"
        assert result[0]["level"] == "required"

    @pytest.mark.asyncio
    async def test_extract_job_skills_fresh(
        self, job_analysis_service, mock_db_session, sample_job_a, mock_openai_client
    ):
        """Test skill extraction without cached results."""
        job_analysis_service.openai_client = mock_openai_client

        # Mock no cached skills
        mock_cached_result = Mock()
        mock_cached_result.scalars.return_value.all.return_value = []

        # Mock job query result - ensure sections are iterable
        sample_job_a.sections = [sample_job_a.sections[0]]  # Make it a real list
        mock_job_result = Mock()
        mock_job_result.scalar_one_or_none.return_value = sample_job_a

        mock_db_session.execute.side_effect = [mock_cached_result, mock_job_result]

        # Mock OpenAI skill extraction
        skills_response = Mock()
        skills_response.choices = [Mock()]
        skills_response.choices[0].message.content = json.dumps(
            [
                {
                    "name": "Python",
                    "category": "technical",
                    "level": "required",
                    "confidence": 0.9,
                }
            ]
        )
        mock_openai_client.chat.completions.create.return_value = skills_response

        with patch.object(job_analysis_service, "_save_extracted_skills"):
            result = await job_analysis_service.extract_job_skills(
                mock_db_session, 1, refresh=True
            )

        assert len(result) > 0
        mock_openai_client.chat.completions.create.assert_called()

    @pytest.mark.asyncio
    async def test_extract_skills_from_text(
        self, job_analysis_service, mock_openai_client
    ):
        """Test skill extraction from text using GPT."""
        job_analysis_service.openai_client = mock_openai_client

        # Mock OpenAI response
        skills_response = Mock()
        skills_response.choices = [Mock()]
        skills_response.choices[0].message.content = json.dumps(
            [
                {
                    "name": "Python Programming",
                    "category": "technical",
                    "level": "required",
                    "confidence": 0.9,
                },
                {
                    "name": "Team Leadership",
                    "category": "leadership",
                    "level": "preferred",
                    "confidence": 0.8,
                },
            ]
        )
        mock_openai_client.chat.completions.create.return_value = skills_response

        text = "Experience with Python programming and team leadership is required"
        result = await job_analysis_service._extract_skills_from_text(text, "technical")

        assert len(result) == 2
        assert result[0]["name"] == "Python Programming"
        assert result[0]["section"] == "technical"
        assert result[1]["name"] == "Team Leadership"

    @pytest.mark.asyncio
    async def test_extract_skills_from_text_error(
        self, job_analysis_service, mock_openai_client
    ):
        """Test skill extraction error handling."""
        job_analysis_service.openai_client = mock_openai_client

        # Mock OpenAI error
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")

        result = await job_analysis_service._extract_skills_from_text(
            "test text", "technical"
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_save_extracted_skills(self, job_analysis_service, mock_db_session):
        """Test saving extracted skills to database."""
        skills = [
            {
                "name": "Python",
                "category": "technical",
                "level": "required",
                "confidence": 0.9,
                "section": "technical",
            }
        ]

        await job_analysis_service._save_extracted_skills(mock_db_session, 1, skills)

        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_calculate_embedding_similarity(
        self, job_analysis_service, mock_db_session
    ):
        """Test embedding-based similarity calculation."""
        # Mock database result with embeddings
        embedding1 = [0.1, 0.2, 0.3, 0.4]
        embedding2 = [0.2, 0.3, 0.4, 0.5]

        mock_result = Mock()
        mock_result.all.return_value = [(embedding1,), (embedding2,)]
        mock_db_session.execute.return_value = mock_result

        similarity = await job_analysis_service._calculate_embedding_similarity(
            mock_db_session, 1, 2
        )

        assert 0.0 <= similarity <= 1.0
        assert isinstance(similarity, float)

    @pytest.mark.asyncio
    async def test_calculate_embedding_similarity_no_embeddings(
        self, job_analysis_service, mock_db_session
    ):
        """Test embedding similarity when no embeddings exist."""
        mock_result = Mock()
        mock_result.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        similarity = await job_analysis_service._calculate_embedding_similarity(
            mock_db_session, 1, 2
        )

        assert similarity == 0.0

    @pytest.mark.asyncio
    async def test_calculate_section_similarities(
        self, job_analysis_service, sample_job_a, sample_job_b, mock_openai_client
    ):
        """Test section-wise similarity calculation."""
        job_analysis_service.openai_client = mock_openai_client

        with patch.object(
            job_analysis_service,
            "_calculate_embedding_text_similarity",
            return_value=0.75,
        ):
            result = await job_analysis_service._calculate_section_similarities(
                sample_job_a, sample_job_b
            )

        assert isinstance(result, dict)
        # Should have similarities for common sections
        assert "specific_accountabilities" in result
        assert "knowledge_skills_abilities" in result

    def test_calculate_text_similarity(self, job_analysis_service):
        """Test simple text similarity calculation."""
        text_a = "python django web development"
        text_b = "python flask web programming"

        similarity = job_analysis_service._calculate_text_similarity(text_a, text_b)

        assert 0.0 <= similarity <= 1.0
        assert similarity > 0  # Should have some similarity due to "python" and "web"

    @pytest.mark.asyncio
    async def test_calculate_embedding_text_similarity(
        self, job_analysis_service, mock_openai_client
    ):
        """Test embedding-based text similarity."""
        job_analysis_service.openai_client = mock_openai_client

        # Mock different embedding responses
        response_a = Mock()
        response_a.data = [Mock()]
        response_a.data[0].embedding = [0.1, 0.2, 0.3, 0.4]

        response_b = Mock()
        response_b.data = [Mock()]
        response_b.data[0].embedding = [0.2, 0.3, 0.4, 0.5]

        mock_openai_client.embeddings.create.side_effect = [response_a, response_b]

        similarity = await job_analysis_service._calculate_embedding_text_similarity(
            "text a", "text b"
        )

        assert 0.0 <= similarity <= 1.0
        assert mock_openai_client.embeddings.create.call_count == 2

    @pytest.mark.asyncio
    async def test_calculate_embedding_text_similarity_fallback(
        self, job_analysis_service, mock_openai_client
    ):
        """Test embedding similarity fallback to text similarity."""
        job_analysis_service.openai_client = mock_openai_client

        # Mock OpenAI error
        mock_openai_client.embeddings.create.side_effect = Exception("API Error")

        with patch.object(
            job_analysis_service, "_calculate_text_similarity", return_value=0.5
        ) as mock_text_sim:
            similarity = (
                await job_analysis_service._calculate_embedding_text_similarity(
                    "text a", "text b"
                )
            )

        assert similarity == 0.5
        mock_text_sim.assert_called_once()

    def test_compare_metadata(self, job_analysis_service, sample_job_a, sample_job_b):
        """Test metadata comparison."""
        result = job_analysis_service._compare_metadata(
            sample_job_a.metadata_entry, sample_job_b.metadata_entry
        )

        assert "salary_difference_percent" in result
        assert "same_department" in result
        assert result["same_department"] is True  # Both in IT

    def test_compare_metadata_no_metadata(self, job_analysis_service):
        """Test metadata comparison with missing metadata."""
        result = job_analysis_service._compare_metadata(None, None)
        assert result == {}

    def test_compare_skills(self, job_analysis_service):
        """Test skill comparison functionality."""
        skills_a = [
            {"name": "Python", "category": "technical", "level": "required"},
            {"name": "Django", "category": "technical", "level": "preferred"},
        ]
        skills_b = [
            {"name": "Python", "category": "technical", "level": "required"},
            {"name": "React", "category": "technical", "level": "required"},
        ]

        result = job_analysis_service._compare_skills(skills_a, skills_b)

        assert "matching_skills" in result
        assert "missing_skills" in result
        assert "skill_level_gaps" in result
        assert "gap_score" in result
        assert "python" in result["matching_skills"]
        assert "react" in result["missing_skills"]

    @pytest.mark.asyncio
    async def test_generate_similarity_insights(
        self, job_analysis_service, sample_job_a, sample_job_b, mock_openai_client
    ):
        """Test similarity insights generation."""
        job_analysis_service.openai_client = mock_openai_client

        # Mock GPT response
        insights_response = Mock()
        insights_response.choices = [Mock()]
        insights_response.choices[0].message.content = json.dumps(
            {
                "key_differences": [
                    "Technology stack differs",
                    "Experience level varies",
                ],
                "recommendation": "Transition is feasible with training",
            }
        )
        mock_openai_client.chat.completions.create.return_value = insights_response

        (
            differences,
            recommendation,
        ) = await job_analysis_service._generate_similarity_insights(
            sample_job_a, sample_job_b, 0.75
        )

        assert len(differences) == 2
        assert "Technology stack differs" in differences
        assert "training" in recommendation.lower()

    @pytest.mark.asyncio
    async def test_generate_similarity_insights_error(
        self, job_analysis_service, sample_job_a, sample_job_b, mock_openai_client
    ):
        """Test similarity insights generation error handling."""
        job_analysis_service.openai_client = mock_openai_client

        # Mock OpenAI error
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")

        (
            differences,
            recommendation,
        ) = await job_analysis_service._generate_similarity_insights(
            sample_job_a, sample_job_b, 0.75
        )

        assert differences == []
        assert recommendation == ""

    @pytest.mark.asyncio
    async def test_cache_comparison_new(self, job_analysis_service, mock_db_session):
        """Test caching new comparison result."""
        # Mock no existing comparison
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        analysis = {
            "overall_similarity": 0.75,
            "section_similarities": {"technical": 0.8},
        }

        await job_analysis_service._cache_comparison(
            mock_db_session, 1, 2, "similarity", analysis
        )

        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_cache_comparison_update(self, job_analysis_service, mock_db_session):
        """Test updating existing comparison result."""
        # Mock existing comparison
        existing_comparison = JobComparison(id=1, job_a_id=1, job_b_id=2)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = existing_comparison
        mock_db_session.execute.return_value = mock_result

        analysis = {
            "overall_similarity": 0.80,
            "section_similarities": {"technical": 0.85},
        }

        await job_analysis_service._cache_comparison(
            mock_db_session, 1, 2, "similarity", analysis
        )

        # Should update, not add new
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_called()

    def test_get_similarity_level(self, job_analysis_service):
        """Test similarity level categorization."""
        assert job_analysis_service._get_similarity_level(0.9) == "Very High"
        assert job_analysis_service._get_similarity_level(0.7) == "High"
        assert job_analysis_service._get_similarity_level(0.5) == "Medium"
        assert job_analysis_service._get_similarity_level(0.3) == "Low"
        assert job_analysis_service._get_similarity_level(0.1) == "Very Low"

    def test_get_match_level(self, job_analysis_service):
        """Test match level categorization."""
        assert job_analysis_service._get_match_level(0.9) == "Excellent Match"
        assert job_analysis_service._get_match_level(0.75) == "Good Match"
        assert job_analysis_service._get_match_level(0.6) == "Fair Match"
        assert job_analysis_service._get_match_level(0.4) == "Poor Match"
        assert job_analysis_service._get_match_level(0.2) == "No Match"

    @pytest.mark.asyncio
    async def test_extract_job_skills_not_found(
        self, job_analysis_service, mock_db_session
    ):
        """Test skill extraction when job is not found."""
        # Mock no cached skills
        mock_cached_result = Mock()
        mock_cached_result.scalars.return_value.all.return_value = []

        # Mock job not found - create a dummy job with empty sections first
        mock_job_result = Mock()
        mock_job_result.scalar_one_or_none.return_value = None

        mock_db_session.execute.side_effect = [mock_cached_result, mock_job_result]

        with pytest.raises(ValueError, match="Job 999 not found"):
            await job_analysis_service.extract_job_skills(
                mock_db_session, 999, refresh=True
            )

    @pytest.mark.asyncio
    async def test_compare_jobs_unknown_type(
        self, job_analysis_service, mock_db_session, sample_job_a, sample_job_b
    ):
        """Test job comparison with unknown comparison type."""
        # Mock database query results
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_job_a, sample_job_b]
        mock_db_session.execute.return_value = mock_result

        with patch.object(job_analysis_service, "_cache_comparison"):
            result = await job_analysis_service.compare_jobs(
                mock_db_session, 1, 2, comparison_types=["unknown_type"]
            )

        # Should skip unknown type and return empty analyses
        assert len(result["analyses"]) == 0

    def test_compare_skills_empty(self, job_analysis_service):
        """Test skill comparison with empty skill lists."""
        result = job_analysis_service._compare_skills([], [])

        assert result["matching_skills"] == []
        assert result["missing_skills"] == []
        assert result["skill_level_gaps"] == {}
        assert result["gap_score"] == 0.0
