"""
AI Enhancement Service for Phase 2.

Provides AI-powered content enhancement capabilities:
- Text improvement suggestions
- Compliance checking
- Bias detection
- Template generation
"""

import uuid
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

try:
    import openai
    from openai import AsyncOpenAI
except ImportError:
    openai = None  # type: ignore
    AsyncOpenAI = None  # type: ignore

from ..config.settings import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AIEnhancementService:
    """Service for AI-powered content enhancement."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client: Optional[Any] = None

        if AsyncOpenAI and hasattr(settings, "openai_api_key"):
            try:
                self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")

    async def generate_suggestions(
        self,
        text: str,
        context: Optional[str] = None,
        suggestion_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate AI-powered text improvement suggestions.

        Args:
            text: Text to analyze
            context: Additional context for suggestions
            suggestion_types: Types of suggestions to generate

        Returns:
            Dictionary with suggestions and overall score
        """
        if suggestion_types is None:
            suggestion_types = ["grammar", "style", "clarity"]

        suggestions = []

        # Check for common grammar issues (basic implementation)
        if "grammar" in suggestion_types:
            grammar_suggestions = self._check_grammar(text)
            suggestions.extend(grammar_suggestions)

        # Check for style improvements
        if "style" in suggestion_types:
            style_suggestions = self._check_style(text)
            suggestions.extend(style_suggestions)

        # Check for clarity issues
        if "clarity" in suggestion_types:
            clarity_suggestions = self._check_clarity(text)
            suggestions.extend(clarity_suggestions)

        # If OpenAI is available, enhance suggestions with AI
        if self.client:
            try:
                ai_suggestions = await self._get_ai_suggestions(text, context, suggestion_types)
                suggestions.extend(ai_suggestions)
            except Exception as e:
                logger.error(f"Error getting AI suggestions: {e}")

        # Calculate overall quality score
        overall_score = self._calculate_quality_score(text, suggestions)

        return {
            "suggestions": suggestions,
            "overall_score": overall_score,
        }

    async def check_compliance(
        self,
        text: str,
        frameworks: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Check text compliance against government standards.

        Args:
            text: Text to check
            frameworks: List of compliance frameworks to check

        Returns:
            Dictionary with compliance status and issues
        """
        if frameworks is None:
            frameworks = ["treasury_board", "accessibility", "bilingual"]

        issues = []

        # Check Treasury Board compliance
        if "treasury_board" in frameworks:
            tb_issues = self._check_treasury_board_compliance(text)
            issues.extend(tb_issues)

        # Check accessibility compliance
        if "accessibility" in frameworks:
            accessibility_issues = self._check_accessibility_compliance(text)
            issues.extend(accessibility_issues)

        # Check bilingual requirements
        if "bilingual" in frameworks:
            bilingual_issues = self._check_bilingual_compliance(text)
            issues.extend(bilingual_issues)

        # Calculate compliance score
        compliance_score = max(0.0, 1.0 - (len(issues) * 0.1))
        compliant = len(issues) == 0

        return {
            "compliant": compliant,
            "issues": issues,
            "compliance_score": compliance_score,
        }

    async def analyze_bias(
        self,
        text: str,
        analysis_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze text for bias and inclusivity issues.

        Args:
            text: Text to analyze
            analysis_types: Types of bias to check for

        Returns:
            Dictionary with bias analysis results
        """
        if analysis_types is None:
            analysis_types = ["gender", "age", "disability", "cultural"]

        issues = []

        # Check for gender bias
        if "gender" in analysis_types:
            gender_issues = self._check_gender_bias(text)
            issues.extend(gender_issues)

        # Check for age bias
        if "age" in analysis_types:
            age_issues = self._check_age_bias(text)
            issues.extend(age_issues)

        # Check for disability bias
        if "disability" in analysis_types:
            disability_issues = self._check_disability_bias(text)
            issues.extend(disability_issues)

        # Check for cultural bias
        if "cultural" in analysis_types:
            cultural_issues = self._check_cultural_bias(text)
            issues.extend(cultural_issues)

        # Calculate inclusivity score
        inclusivity_score = max(0.0, 1.0 - (len(issues) * 0.15))
        bias_free = len(issues) == 0

        return {
            "bias_free": bias_free,
            "issues": issues,
            "inclusivity_score": inclusivity_score,
        }

    async def generate_template(
        self,
        classification: str,
        language: str = "en",
        custom_requirements: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate AI-powered job description template.

        Args:
            classification: Job classification code
            language: Template language
            custom_requirements: Custom requirements for template

        Returns:
            Dictionary with template content
        """
        template_id = str(uuid.uuid4())

        # Define standard sections based on classification
        sections = self._get_standard_sections(classification, language)

        # Apply custom requirements if provided
        if custom_requirements:
            sections = self._apply_custom_requirements(sections, custom_requirements)

        # Generate AI-enhanced content if available
        if self.client:
            try:
                sections = await self._enhance_template_with_ai(
                    sections, classification, language
                )
            except Exception as e:
                logger.error(f"Error enhancing template with AI: {e}")

        metadata = {
            "created_at": datetime.utcnow().isoformat(),
            "classification": classification,
            "language": language,
            "version": "1.0",
        }

        return {
            "template_id": template_id,
            "classification": classification,
            "language": language,
            "sections": sections,
            "metadata": metadata,
        }

    # Private helper methods

    def _check_grammar(self, text: str) -> List[Dict[str, Any]]:
        """Check for basic grammar issues."""
        suggestions = []

        # Check for double spaces
        if "  " in text:
            for match in re.finditer(r"  +", text):
                suggestions.append({
                    "id": str(uuid.uuid4()),
                    "type": "grammar",
                    "original_text": match.group(),
                    "suggested_text": " ",
                    "explanation": "Remove extra spaces",
                    "confidence": 0.95,
                    "start_index": match.start(),
                    "end_index": match.end(),
                })

        return suggestions

    def _check_style(self, text: str) -> List[Dict[str, Any]]:
        """Check for style improvements."""
        suggestions = []

        # Check for passive voice (simplified)
        passive_patterns = [r"\bis\s+\w+ed\b", r"\bwas\s+\w+ed\b", r"\bare\s+\w+ed\b"]
        for pattern in passive_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                suggestions.append({
                    "id": str(uuid.uuid4()),
                    "type": "style",
                    "original_text": match.group(),
                    "suggested_text": "[Consider active voice]",
                    "explanation": "Consider using active voice for clarity",
                    "confidence": 0.7,
                    "start_index": match.start(),
                    "end_index": match.end(),
                })

        return suggestions

    def _check_clarity(self, text: str) -> List[Dict[str, Any]]:
        """Check for clarity issues."""
        suggestions = []

        # Check for overly long sentences
        sentences = text.split(".")
        position = 0
        for sentence in sentences:
            word_count = len(sentence.split())
            if word_count > 30:
                suggestions.append({
                    "id": str(uuid.uuid4()),
                    "type": "clarity",
                    "original_text": sentence.strip(),
                    "suggested_text": "[Consider breaking into shorter sentences]",
                    "explanation": f"Long sentence ({word_count} words) may reduce clarity",
                    "confidence": 0.8,
                    "start_index": position,
                    "end_index": position + len(sentence),
                })
            position += len(sentence) + 1

        return suggestions

    async def _get_ai_suggestions(
        self, text: str, context: Optional[str], types: List[str]
    ) -> List[Dict[str, Any]]:
        """Get AI-powered suggestions from OpenAI."""
        # Placeholder for OpenAI integration
        # Would make API call to GPT for advanced suggestions
        return []

    def _calculate_quality_score(self, text: str, suggestions: List[Dict]) -> float:
        """Calculate overall quality score based on text and suggestions."""
        if not text:
            return 0.0

        # Simple scoring: reduce score based on number of issues
        base_score = 1.0
        penalty_per_issue = 0.05
        score = max(0.0, base_score - (len(suggestions) * penalty_per_issue))

        return round(score, 2)

    def _check_treasury_board_compliance(self, text: str) -> List[Dict[str, Any]]:
        """Check Treasury Board directive compliance."""
        return []  # Simplified implementation

    def _check_accessibility_compliance(self, text: str) -> List[Dict[str, Any]]:
        """Check accessibility standards compliance."""
        return []  # Simplified implementation

    def _check_bilingual_compliance(self, text: str) -> List[Dict[str, Any]]:
        """Check bilingual requirements compliance."""
        return []  # Simplified implementation

    def _check_gender_bias(self, text: str) -> List[Dict[str, Any]]:
        """Check for gender bias."""
        issues = []

        # Check for gender-specific pronouns in job descriptions
        gendered_terms = {
            "he": "they",
            "she": "they",
            "his": "their",
            "her": "their",
            "him": "them",
            "himself": "themselves",
            "herself": "themselves",
        }

        for term, alternative in gendered_terms.items():
            pattern = r"\b" + term + r"\b"
            for match in re.finditer(pattern, text, re.IGNORECASE):
                issues.append({
                    "type": "gender",
                    "description": "Gender-specific pronoun detected",
                    "problematic_text": match.group(),
                    "suggested_alternatives": [alternative],
                    "severity": "medium",
                    "start_index": match.start(),
                    "end_index": match.end(),
                })

        return issues

    def _check_age_bias(self, text: str) -> List[Dict[str, Any]]:
        """Check for age bias."""
        return []  # Simplified implementation

    def _check_disability_bias(self, text: str) -> List[Dict[str, Any]]:
        """Check for disability bias."""
        return []  # Simplified implementation

    def _check_cultural_bias(self, text: str) -> List[Dict[str, Any]]:
        """Check for cultural bias."""
        return []  # Simplified implementation

    def _get_standard_sections(
        self, classification: str, language: str
    ) -> Dict[str, str]:
        """Get standard template sections for classification."""
        # Simplified template structure
        if language == "fr":
            return {
                "general_accountability": "À définir",
                "organization_structure": "À définir",
                "key_responsibilities": "À définir",
                "qualifications": "À définir",
            }
        else:
            return {
                "general_accountability": "To be defined",
                "organization_structure": "To be defined",
                "key_responsibilities": "To be defined",
                "qualifications": "To be defined",
            }

    def _apply_custom_requirements(
        self, sections: Dict[str, str], requirements: Dict[str, Any]
    ) -> Dict[str, str]:
        """Apply custom requirements to template sections."""
        # Update sections based on custom requirements
        return sections

    async def _enhance_template_with_ai(
        self, sections: Dict[str, str], classification: str, language: str
    ) -> Dict[str, str]:
        """Enhance template sections using AI."""
        # Placeholder for AI enhancement
        return sections