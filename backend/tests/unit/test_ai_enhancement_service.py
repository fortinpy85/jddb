import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from jd_ingestion.services.ai_enhancement_service import AIEnhancementService


# Mock settings for testing
@pytest.fixture(autouse=True)
def mock_settings_for_ai_service():
    with patch(
        "jd_ingestion.services.ai_enhancement_service.settings"
    ) as mock_settings:
        mock_settings.openai_api_key = "test_api_key"
        mock_settings.openai_organization = "test_org"
        mock_settings.openai_max_retries = 3
        mock_settings.openai_timeout = 60
        mock_settings.openai_request_timeout = 60
        mock_settings.openai_rate_limit_per_minute = 1000
        mock_settings.openai_cost_tracking_enabled = True
        yield mock_settings


@pytest.fixture
def ai_enhancement_service(mock_settings_for_ai_service):
    db_session = AsyncMock(spec=AsyncSession)
    service = AIEnhancementService(db_session)
    # Ensure client is mocked if OpenAI is not installed or API key is missing
    if not service.client:
        service.client = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_init_openai_client_success(mock_settings_for_ai_service):
    with patch(
        "jd_ingestion.services.ai_enhancement_service.AsyncOpenAI"
    ) as MockAsyncOpenAI:
        mock_settings_for_ai_service.openai_api_key = "valid_key"
        service = AIEnhancementService(AsyncMock(spec=AsyncSession))
        MockAsyncOpenAI.assert_called_once_with(api_key="valid_key")
        assert service.client is not None


@pytest.mark.asyncio
async def test_init_openai_client_no_api_key(mock_settings_for_ai_service):
    with patch(
        "jd_ingestion.services.ai_enhancement_service.AsyncOpenAI"
    ) as MockAsyncOpenAI:
        mock_settings_for_ai_service.openai_api_key = ""
        service = AIEnhancementService(AsyncMock(spec=AsyncSession))
        MockAsyncOpenAI.assert_not_called()
        assert service.client is None


@pytest.mark.asyncio
async def test_init_openai_client_import_error():
    with patch("jd_ingestion.services.ai_enhancement_service.AsyncOpenAI", new=None):
        service = AIEnhancementService(AsyncMock(spec=AsyncSession))
        assert service.client is None


def test_check_grammar_double_spaces(ai_enhancement_service):
    text = "This  text   has  double  spaces."
    suggestions = ai_enhancement_service._check_grammar(text)
    assert len(suggestions) == 4
    assert suggestions[0]["original_text"] == "  "
    assert suggestions[0]["suggested_text"] == " "
    assert suggestions[0]["start_index"] == 4
    assert suggestions[0]["end_index"] == 6


def test_check_grammar_no_issues(ai_enhancement_service):
    text = "This text has no grammar issues."
    suggestions = ai_enhancement_service._check_grammar(text)
    assert len(suggestions) == 0


def test_check_style_passive_voice(ai_enhancement_service):
    text = "The report was finished. The task is completed."
    suggestions = ai_enhancement_service._check_style(text)
    assert len(suggestions) == 2
    assert any(s["original_text"] == "was finished" for s in suggestions)
    assert any(s["original_text"] == "is completed" for s in suggestions)


def test_check_clarity_long_sentences(ai_enhancement_service):
    text = "This is a very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very long sentence. Another incredibly long sentence that easily exceeds thirty words and should also be flagged as a clarity issue."
    suggestions = ai_enhancement_service._check_clarity(text)
    assert len(suggestions) == 1
    assert "Long sentence" in suggestions[0]["explanation"]


def test_check_gender_bias_pronouns(ai_enhancement_service):
    text = "He is a chairman. She is a saleswoman."
    issues = ai_enhancement_service._check_gender_bias(text)
    assert any("Gender-specific pronoun" in i["description"] for i in issues)
    assert any("Gendered job title" in i["description"] for i in issues)


def test_check_gender_bias_coded_language_masculine_skew(ai_enhancement_service):
    text = "We need an aggressive and dominant leader. He will enforce new rules."
    issues = ai_enhancement_service._check_gender_bias(text)
    assert any(
        "Heavy use of masculine-coded language" in i["description"] for i in issues
    )
    assert any(i["problematic_text"] == "aggressive" for i in issues)


def test_check_gender_bias_coded_language_feminine_skew(ai_enhancement_service):
    text = (
        "We need a nurturing and supportive team member. She will build relationships."
    )
    issues = ai_enhancement_service._check_gender_bias(text)
    assert any(
        "Heavy use of feminine-coded language" in i["description"] for i in issues
    )
    assert any(i["problematic_text"] == "nurturing" for i in issues)


def test_check_gender_bias_coded_language_balanced(ai_enhancement_service):
    text = "We need an aggressive yet supportive leader."
    issues = ai_enhancement_service._check_gender_bias(text)
    assert not any("coded language" in i["description"] for i in issues)


def test_check_age_bias_explicit_age_requirement(ai_enhancement_service):
    text = "Candidates must be under 30 years old."
    issues = ai_enhancement_service._check_age_bias(text)
    assert len(issues) == 1
    assert "Explicit age requirement" in issues[0]["description"]


def test_check_age_bias_biased_terms(ai_enhancement_service):
    text = "We are looking for a youthful and energetic team member."
    issues = ai_enhancement_service._check_age_bias(text)
    assert len(issues) >= 2
    assert any("youthful" in i["problematic_text"].lower() for i in issues)
    assert any("energetic" in i["problematic_text"].lower() for i in issues)


def test_check_age_bias_excessive_experience(ai_enhancement_service):
    text = "Requires 25 years of experience."
    issues = ai_enhancement_service._check_age_bias(text)
    assert len(issues) == 1
    assert "Excessive experience requirement" in issues[0]["description"]


def test_check_disability_bias_physical_requirements(ai_enhancement_service):
    text = "Must be able to stand for long periods."
    issues = ai_enhancement_service._check_disability_bias(text)
    assert (
        len(issues) == 2
    )  # Matches both unnecessary_physical_patterns and disability_bias_patterns
    assert any(
        "Excludes candidates with mobility impairments" in i["description"]
        for i in issues
    )
    assert any(
        "Consider if this is essential or can be accommodated" in i["description"]
        for i in issues
    )


def test_check_disability_bias_ableist_language(ai_enhancement_service):
    text = "Candidates must be able-bodied."
    issues = ai_enhancement_service._check_disability_bias(text)
    assert len(issues) == 1
    assert "Directly discriminatory term" in issues[0]["description"]


def test_check_disability_bias_transport_patterns(ai_enhancement_service):
    text = "Must have a driver's license."
    issues = ai_enhancement_service._check_disability_bias(text)
    assert len(issues) == 1
    assert (
        "May exclude candidates unable to drive due to disability"
        in issues[0]["description"]
    )


def test_check_cultural_bias_geographic(ai_enhancement_service):
    text = "Requires North American experience."
    issues = ai_enhancement_service._check_cultural_bias(text)
    assert len(issues) == 1
    assert "Excludes qualified international candidates" in issues[0]["description"]


def test_check_cultural_bias_language_proficiency(ai_enhancement_service):
    text = "Must be a native English speaker."
    issues = ai_enhancement_service._check_cultural_bias(text)
    assert len(issues) == 1
    assert (
        "Discriminatory; focus on proficiency not native speaker status"
        in issues[0]["description"]
    )


def test_check_cultural_bias_socioeconomic(ai_enhancement_service):
    text = "Candidates must own a laptop."
    issues = ai_enhancement_service._check_cultural_bias(text)
    assert len(issues) == 1
    assert "Creates socioeconomic barrier" in issues[0]["description"]


def test_check_cultural_bias_cultural_fit(ai_enhancement_service):
    text = "We are looking for a cultural fit."
    issues = ai_enhancement_service._check_cultural_bias(text)
    assert len(issues) == 1
    assert (
        "Vague and often used to exclude diverse candidates" in issues[0]["description"]
    )
