"""
AI Enhancement Service for Phase 2 and Phase 3.

Provides AI-powered content enhancement capabilities:
- Text improvement suggestions
- Compliance checking
- Bias detection
- Template generation
- Quality scoring (readability, completeness, clarity)
"""

import uuid
import re
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

try:
    import openai
    from openai import AsyncOpenAI
except ImportError:
    openai = None  # type: ignore
    AsyncOpenAI = None  # type: ignore

try:
    import textstat
except ImportError:
    textstat = None  # type: ignore

from ..config.settings import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AIEnhancementService:
    """Service for AI-powered content enhancement."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client: Optional[Any] = None

        if AsyncOpenAI is not None and hasattr(settings, "openai_api_key"):  # type: ignore[truthy-function]
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
                ai_suggestions = await self._get_ai_suggestions(
                    text, context, suggestion_types
                )
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
        use_gpt4: bool = True,
    ) -> Dict[str, Any]:
        """
        Analyze text for bias and inclusivity issues.

        Args:
            text: Text to analyze
            analysis_types: Types of bias to check for
            use_gpt4: Whether to enhance with GPT-4 context-aware detection

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

        # Enhance with GPT-4 if available, enabled, and requested
        if use_gpt4 and self.client and len(text) > 50:
            try:
                gpt4_issues = await self._analyze_bias_with_gpt4(text, analysis_types)
                # Add GPT-4 detected issues that weren't caught by patterns
                issues.extend(gpt4_issues)
                logger.info(
                    f"GPT-4 enhancement added {len(gpt4_issues)} context-aware issues"
                )
            except Exception as e:
                logger.warning(
                    f"GPT-4 bias analysis failed, using pattern-based only: {e}"
                )

        # Calculate inclusivity score
        inclusivity_score = max(0.0, 1.0 - (len(issues) * 0.15))
        bias_free = len(issues) == 0

        return {
            "bias_free": bias_free,
            "issues": issues,
            "inclusivity_score": inclusivity_score,
        }

    async def _analyze_bias_with_gpt4(
        self,
        text: str,
        analysis_types: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Use GPT-4 to detect subtle bias that pattern matching might miss.

        This enhances pattern-based detection with AI that understands:
        - Context and nuance
        - Implicit bias
        - Cultural sensitivity
        - Tone and implication

        Args:
            text: Text to analyze
            analysis_types: Types of bias to check for

        Returns:
            List of additional bias issues detected by GPT-4
        """
        if not self.client:
            return []

        # Build analysis type description
        types_desc = ", ".join(analysis_types)

        prompt = f"""You are an expert in identifying bias in job descriptions and professional text. Analyze the following text for {types_desc} bias.

Focus on:
1. **Subtle bias** that pattern matching might miss (don't repeat obvious issues)
2. **Context-dependent** bias (words that are problematic in this specific context)
3. **Implicit assumptions** that could exclude qualified candidates
4. **Tone and implications** that may discourage diverse applicants

Text to analyze:
\"\"\"{text}\"\"\"

Provide your analysis as a JSON array of issues. Each issue should have:
- "type": the bias category (gender, age, disability, or cultural)
- "problematic_text": the exact text that is problematic (max 50 characters)
- "description": why this is problematic in this context
- "suggested_alternatives": array of 2-3 better alternatives
- "severity": "critical", "high", "medium", or "low"
- "context_note": brief explanation of why context matters here

ONLY include issues where context is important. Do not repeat obvious pattern-based issues.
If no contextual bias is found, return an empty array.

Return ONLY valid JSON, no other text."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert bias detection system for job descriptions. You identify subtle, context-dependent bias that simple pattern matching cannot detect.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=1500,
            )

            response_text = response.choices[0].message.content.strip()

            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                response_text = (
                    response_text.split("```json")[1].split("```")[0].strip()
                )
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            import json

            gpt4_issues = json.loads(response_text)

            # Convert to our format and add start/end indices
            formatted_issues = []
            for issue in gpt4_issues:
                # Try to find the text in the original to get indices
                problematic = issue.get("problematic_text", "")
                start_idx = text.lower().find(problematic.lower())
                end_idx = start_idx + len(problematic) if start_idx >= 0 else 0

                formatted_issues.append(
                    {
                        "type": issue.get("type", "general"),
                        "description": issue.get("description", "")
                        + f" [GPT-4 Context: {issue.get('context_note', 'N/A')}]",
                        "problematic_text": problematic,
                        "suggested_alternatives": issue.get(
                            "suggested_alternatives", []
                        ),
                        "severity": issue.get("severity", "medium"),
                        "start_index": start_idx if start_idx >= 0 else 0,
                        "end_index": end_idx,
                    }
                )

            logger.info(
                f"GPT-4 detected {len(formatted_issues)} additional context-based bias issues"
            )
            return formatted_issues

        except Exception as e:
            logger.error(f"GPT-4 bias analysis error: {e}")
            return []

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
                suggestions.append(
                    {
                        "id": str(uuid.uuid4()),
                        "type": "grammar",
                        "original_text": match.group(),
                        "suggested_text": " ",
                        "explanation": "Remove extra spaces",
                        "confidence": 0.95,
                        "start_index": match.start(),
                        "end_index": match.end(),
                    }
                )

        return suggestions

    def _check_style(self, text: str) -> List[Dict[str, Any]]:
        """Check for style improvements."""
        suggestions = []

        # Check for passive voice (simplified)
        passive_patterns = [r"\bis\s+\w+ed\b", r"\bwas\s+\w+ed\b", r"\bare\s+\w+ed\b"]
        for pattern in passive_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                suggestions.append(
                    {
                        "id": str(uuid.uuid4()),
                        "type": "style",
                        "original_text": match.group(),
                        "suggested_text": "[Consider active voice]",
                        "explanation": "Consider using active voice for clarity",
                        "confidence": 0.7,
                        "start_index": match.start(),
                        "end_index": match.end(),
                    }
                )

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
                suggestions.append(
                    {
                        "id": str(uuid.uuid4()),
                        "type": "clarity",
                        "original_text": sentence.strip(),
                        "suggested_text": "[Consider breaking into shorter sentences]",
                        "explanation": f"Long sentence ({word_count} words) may reduce clarity",
                        "confidence": 0.8,
                        "start_index": position,
                        "end_index": position + len(sentence),
                    }
                )
            position += len(sentence) + 1

        return suggestions

    async def _get_ai_suggestions(
        self, text: str, context: Optional[str], types: List[str]
    ) -> List[Dict[str, Any]]:
        """Get AI-powered suggestions from OpenAI."""
        if not self.client:
            return []

        prompt = f"""Analyze the following text and provide suggestions for improvement.

        Text to analyze:
        \"\"\"{text}\"\"\"

        Context: {context or "Not provided"}

        Suggestion types: {types}

        Provide a JSON array of suggestions, where each suggestion has:
        - "id": a unique ID
        - "type": the suggestion type (e.g., grammar, style, clarity)
        - "original_text": the text to be replaced
        - "suggested_text": the suggested replacement
        - "explanation": a brief explanation of the suggestion
        - "confidence": a score from 0.0 to 1.0
        - "start_index": the starting index of the original text
        - "end_index": the ending index of the original text
        """

        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in analyzing text and providing improvement suggestions.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_tokens=1000,
            )

            suggestions = json.loads(response.choices[0].message.content)
            return suggestions

        except Exception as e:
            logger.error(f"Error getting AI suggestions: {e}")
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
        issues = []
        required_keywords = [
            "Official Languages",
            "Employment Equity",
            "Access to Information",
        ]

        for keyword in required_keywords:
            if keyword.lower() not in text.lower():
                issues.append(
                    {
                        "type": "compliance",
                        "description": f"Missing required Treasury Board keyword: {keyword}",
                        "severity": "high",
                    }
                )

        return issues

    def _check_accessibility_compliance(self, text: str) -> List[Dict[str, Any]]:
        """Check accessibility standards compliance."""
        issues = []
        required_keywords = ["accommodation", "accessible", "disability"]

        for keyword in required_keywords:
            if keyword.lower() not in text.lower():
                issues.append(
                    {
                        "type": "compliance",
                        "description": f"Missing required accessibility keyword: {keyword}",
                        "severity": "high",
                    }
                )

        return issues

    def _check_bilingual_compliance(self, text: str) -> List[Dict[str, Any]]:
        """Check bilingual requirements compliance."""
        issues = []
        has_english = "the" in text.lower() or "and" in text.lower()
        has_french = "le" in text.lower() or "et" in text.lower()

        if not (has_english and has_french):
            issues.append(
                {
                    "type": "compliance",
                    "description": "The document does not appear to be bilingual.",
                    "severity": "high",
                }
            )

        return issues

    def _check_gender_bias(self, text: str) -> List[Dict[str, Any]]:
        """
        Check for gender bias including pronouns, gendered titles, and coded language.

        Detects:
        - Gender-specific pronouns
        - Gendered job titles
        - Masculine-coded language
        - Feminine-coded language (for balance)
        """
        issues = []

        # Gender-specific pronouns
        gendered_pronouns = {
            "he": {"alternative": "they", "severity": "medium"},
            "she": {"alternative": "they", "severity": "medium"},
            "his": {"alternative": "their", "severity": "medium"},
            "her": {"alternative": "their", "severity": "medium"},
            "him": {"alternative": "them", "severity": "medium"},
            "himself": {"alternative": "themselves", "severity": "medium"},
            "herself": {"alternative": "themselves", "severity": "medium"},
        }

        for term, info in gendered_pronouns.items():
            pattern = r"\b" + term + r"\b"
            for match in re.finditer(pattern, text, re.IGNORECASE):
                issues.append(
                    {
                        "type": "gender",
                        "description": "Gender-specific pronoun detected; use gender-neutral language",
                        "problematic_text": match.group(),
                        "suggested_alternatives": [info["alternative"]],
                        "severity": info["severity"],
                        "start_index": match.start(),
                        "end_index": match.end(),
                    }
                )

        # Gendered job titles
        gendered_job_titles = {
            "chairman": ["chairperson", "chair"],
            "chairwoman": ["chairperson", "chair"],
            "salesman": ["salesperson", "sales representative"],
            "saleswoman": ["salesperson", "sales representative"],
            "businessman": ["businessperson", "business professional"],
            "businesswoman": ["businessperson", "business professional"],
            "policeman": ["police officer"],
            "policewoman": ["police officer"],
            "fireman": ["firefighter"],
            "firewoman": ["firefighter"],
            "mailman": ["mail carrier", "postal worker"],
            "postman": ["mail carrier", "postal worker"],
            "congressman": ["congressional representative", "member of congress"],
            "congresswoman": ["congressional representative", "member of congress"],
            "spokesman": ["spokesperson", "representative"],
            "spokeswoman": ["spokesperson", "representative"],
            "foreman": ["supervisor", "lead"],
            "forewoman": ["supervisor", "lead"],
            "cameraman": ["camera operator"],
            "camerawoman": ["camera operator"],
            "weatherman": ["meteorologist", "weather forecaster"],
            "weatherwoman": ["meteorologist", "weather forecaster"],
            "mankind": ["humanity", "humankind", "people"],
            "manpower": ["workforce", "staff", "personnel"],
            "man-hours": ["person-hours", "work-hours", "labor hours"],
        }

        for term, alternatives in gendered_job_titles.items():
            pattern = r"\b" + re.escape(term) + r"\b"
            for match in re.finditer(pattern, text, re.IGNORECASE):
                issues.append(
                    {
                        "type": "gender",
                        "description": "Gendered job title detected; use gender-neutral alternative",
                        "problematic_text": match.group(),
                        "suggested_alternatives": alternatives,
                        "severity": "high",
                        "start_index": match.start(),
                        "end_index": match.end(),
                    }
                )

        # Masculine-coded language (research shows these discourage women from applying)
        masculine_coded_words = {
            "aggressive": ["assertive", "confident", "proactive"],
            "dominant": ["leading", "influential", "authoritative"],
            "competitive": ["driven", "goal-oriented", "results-focused"],
            "decisive": ["clear decision-maker", "action-oriented"],
            "independent": ["self-directed", "autonomous"],
            "analytical": ["detail-oriented", "systematic"],
            "ambitious": ["motivated", "goal-oriented"],
            "challenging": ["engaging", "stimulating"],
            "confident": ["self-assured", "assured"],
            "enforce": ["implement", "ensure compliance"],
            "superior": ["excellent", "high-quality"],
        }

        # Feminine-coded language (for balance - overuse discourages men)
        feminine_coded_words = {
            "support": ["assist", "enable", "facilitate"],
            "nurture": ["develop", "cultivate", "foster"],
            "collaborate": ["work together", "partner"],
            "empathetic": ["understanding", "perceptive"],
            "interpersonal": ["communication", "relationship"],
            "cooperative": ["team-oriented", "collaborative"],
            "loyal": ["committed", "dedicated"],
            "caring": ["attentive", "considerate"],
            "responsible for others": ["accountable for team", "manages team"],
        }

        # Count masculine vs feminine coded words to detect imbalance
        masculine_count = 0
        feminine_count = 0

        for term, alternatives in masculine_coded_words.items():
            pattern = r"\b" + re.escape(term) + r"\b"
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            masculine_count += len(matches)

            # Only flag if there's significant imbalance (will check later)
            for match in matches:
                issues.append(
                    {
                        "type": "gender_coded_masculine",
                        "description": "Masculine-coded language may discourage female applicants",
                        "problematic_text": match.group(),
                        "suggested_alternatives": alternatives,
                        "severity": "low",  # Low severity for individual words
                        "start_index": match.start(),
                        "end_index": match.end(),
                        "_count_only": True,  # Mark for conditional inclusion
                    }
                )

        for term, alternatives in feminine_coded_words.items():
            pattern = r"\b" + re.escape(term) + r"\b"
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            feminine_count += len(matches)

            for match in matches:
                issues.append(
                    {
                        "type": "gender_coded_feminine",
                        "description": "Feminine-coded language may discourage male applicants",
                        "problematic_text": match.group(),
                        "suggested_alternatives": alternatives,
                        "severity": "low",
                        "start_index": match.start(),
                        "end_index": match.end(),
                        "_count_only": True,  # Mark for conditional inclusion
                    }
                )

        # Only include coded language issues if there's significant imbalance
        # Remove temporary markers and filter based on imbalance
        total_coded = masculine_count + feminine_count
        if total_coded > 0:
            masculine_ratio = masculine_count / total_coded
            # Only flag if ratio is significantly skewed (> 70% one direction)
            if masculine_ratio > 0.7:
                # Keep masculine-coded issues, remove feminine
                issues = [i for i in issues if i.get("type") != "gender_coded_feminine"]
                # Remove the marker from masculine issues
                for issue in issues:
                    if "_count_only" in issue:
                        del issue["_count_only"]
                        issue["severity"] = "medium"  # Upgrade severity when imbalanced
                        issue["description"] = (
                            f"Heavy use of masculine-coded language (ratio: {masculine_ratio:.0%}); may discourage female applicants"
                        )
            elif masculine_ratio < 0.3 and feminine_count > 0:
                # Keep feminine-coded issues, remove masculine
                issues = [
                    i for i in issues if i.get("type") != "gender_coded_masculine"
                ]
                feminine_ratio = feminine_count / total_coded
                for issue in issues:
                    if "_count_only" in issue:
                        del issue["_count_only"]
                        issue["severity"] = "medium"
                        issue["description"] = (
                            f"Heavy use of feminine-coded language (ratio: {feminine_ratio:.0%}); may discourage male applicants"
                        )
            else:
                # Balanced - remove all coded language issues
                issues = [i for i in issues if not i.get("_count_only")]
        else:
            # No coded language found - remove markers
            issues = [i for i in issues if not i.get("_count_only")]

        return issues

    def _check_age_bias(self, text: str) -> List[Dict[str, Any]]:
        """
        Check for age bias in job description text.

        Detects age-discriminatory language that may discourage applicants
        of certain age groups from applying.
        """
        issues = []

        # Age bias pattern library
        age_bias_patterns = {
            # High severity - Direct age discrimination
            "young": {
                "alternatives": ["collaborative", "innovative", "dynamic"],
                "severity": "high",
                "explanation": "Implies age discrimination; suggests preference for younger candidates",
            },
            "youthful": {
                "alternatives": ["energetic", "enthusiastic", "proactive"],
                "severity": "high",
                "explanation": "Excludes experienced professionals; age-discriminatory",
            },
            "energetic": {
                "alternatives": ["motivated", "engaged", "proactive"],
                "severity": "medium",
                "explanation": "May discourage older applicants; implies physical stamina requirement",
            },
            "digital native": {
                "alternatives": [
                    "tech-savvy",
                    "digitally fluent",
                    "technically proficient",
                ],
                "severity": "high",
                "explanation": "Strongly age-biased; excludes experienced professionals who learned technology later",
            },
            "recent graduate": {
                "alternatives": ["entry-level", "early career professional"],
                "severity": "medium",
                "explanation": "Suggests age preference; use career stage instead",
            },
            "new grad": {
                "alternatives": ["entry-level", "early career professional"],
                "severity": "medium",
                "explanation": "Suggests age preference; use career stage instead",
            },
            # Medium severity - Indirect age signals
            "tech-savvy millennial": {
                "alternatives": ["technologically proficient", "digitally skilled"],
                "severity": "high",
                "explanation": "Generational reference is age-discriminatory",
            },
            "high energy": {
                "alternatives": ["self-motivated", "results-driven"],
                "severity": "medium",
                "explanation": "May be perceived as age-biased",
            },
            "vibrant": {
                "alternatives": ["dynamic", "active", "engaged"],
                "severity": "low",
                "explanation": "Could be interpreted as youth-oriented",
            },
            "fast-paced environment": {
                "alternatives": ["dynamic environment", "evolving environment"],
                "severity": "low",
                "explanation": "May discourage experienced professionals",
            },
        }

        # Check for explicit age requirements (illegal in many jurisdictions)
        age_requirement_patterns = [
            r"\b\d+\s*[-–]\s*\d+\s*years?\s*old\b",  # "25-35 years old"
            r"\bunder\s+\d+\b",  # "under 40"
            r"\bover\s+\d+\b",  # "over 25"
            r"\byounger\s+than\b",
            r"\bolder\s+than\b",
        ]

        for pattern in age_requirement_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                issues.append(
                    {
                        "type": "age",
                        "description": "Explicit age requirement detected (likely illegal)",
                        "problematic_text": match.group(),
                        "suggested_alternatives": [
                            "Remove age requirement",
                            "Use experience level instead",
                        ],
                        "severity": "critical",
                        "start_index": match.start(),
                        "end_index": match.end(),
                    }
                )

        # Check for age-biased terms
        for term, info in age_bias_patterns.items():
            # Use word boundary for whole-word matching
            pattern = r"\b" + re.escape(term) + r"\b"
            for match in re.finditer(pattern, text, re.IGNORECASE):
                issues.append(
                    {
                        "type": "age",
                        "description": info["explanation"],
                        "problematic_text": match.group(),
                        "suggested_alternatives": info["alternatives"],
                        "severity": info["severity"],
                        "start_index": match.start(),
                        "end_index": match.end(),
                    }
                )

        # Check for excessive experience requirements (20+ years may exclude younger candidates)
        experience_pattern = r"(\d+)\+?\s*years?\s+(of\s+)?experience"
        for match in re.finditer(experience_pattern, text, re.IGNORECASE):
            years = int(match.group(1))
            if years >= 20:
                issues.append(
                    {
                        "type": "age",
                        "description": f"Excessive experience requirement ({years} years) may discriminate against younger candidates",
                        "problematic_text": match.group(),
                        "suggested_alternatives": [
                            "Consider if this much experience is truly necessary",
                            f"Use '15-{years} years' to show flexibility",
                            "Focus on competencies rather than years",
                        ],
                        "severity": "medium",
                        "start_index": match.start(),
                        "end_index": match.end(),
                    }
                )

        return issues

    def _check_disability_bias(self, text: str) -> List[Dict[str, Any]]:
        """
        Check for disability bias and ability-based language.

        Detects language that may exclude people with disabilities or
        makes unnecessary ability-based assumptions.
        """
        issues = []

        # Disability bias patterns - ability-based requirements
        disability_bias_patterns = {
            # Physical ability requirements
            "must be able to stand": {
                "alternatives": [
                    "position may involve standing",
                    "standing with accommodation available",
                ],
                "severity": "high",
                "explanation": "Excludes candidates with mobility impairments; state requirement with accommodation option",
            },
            "must be able to walk": {
                "alternatives": [
                    "position may require mobility",
                    "mobility with accommodation available",
                ],
                "severity": "high",
                "explanation": "Excludes candidates with mobility disabilities",
            },
            "must be able to lift": {
                "alternatives": [
                    "position may involve lifting",
                    "lifting with accommodation or assistance available",
                ],
                "severity": "medium",
                "explanation": "State physical requirement without making it exclusionary",
            },
            "physically fit": {
                "alternatives": [
                    "able to perform job duties",
                    "capable of fulfilling role responsibilities",
                ],
                "severity": "high",
                "explanation": "Unnecessarily excludes people with disabilities",
            },
            "able-bodied": {
                "alternatives": ["physically capable of", "able to perform"],
                "severity": "high",
                "explanation": "Directly discriminatory term; focus on job requirements",
            },
            # Sensory ability requirements
            "excellent vision": {
                "alternatives": ["attention to detail", "accuracy in work"],
                "severity": "high",
                "explanation": "Excludes candidates with visual impairments; focus on outcome not ability",
            },
            "perfect vision": {
                "alternatives": ["attention to detail", "precision"],
                "severity": "high",
                "explanation": "Discriminatory; most jobs can accommodate visual impairments",
            },
            "must be able to see": {
                "alternatives": ["visual acuity or accommodation", "ability to review"],
                "severity": "high",
                "explanation": "Excludes blind/visually impaired candidates; focus on task outcome",
            },
            "good eyesight": {
                "alternatives": ["attention to visual details", "visual accuracy"],
                "severity": "medium",
                "explanation": "May exclude visually impaired candidates unnecessarily",
            },
            "must be able to hear": {
                "alternatives": [
                    "communication skills",
                    "ability to receive information",
                ],
                "severity": "high",
                "explanation": "Excludes deaf/hard of hearing candidates; many accommodations available",
            },
            "good hearing": {
                "alternatives": [
                    "strong communication skills",
                    "receptive to information",
                ],
                "severity": "medium",
                "explanation": "May exclude candidates with hearing impairments",
            },
            # Mental/cognitive assumptions
            "quick learner": {
                "alternatives": [
                    "adaptable",
                    "learns effectively",
                    "develops new skills",
                ],
                "severity": "low",
                "explanation": "May exclude candidates with learning disabilities; focus on outcome not speed",
            },
            "mentally fit": {
                "alternatives": [
                    "capable of performing job duties",
                    "meets job requirements",
                ],
                "severity": "high",
                "explanation": "Discriminatory against people with mental health conditions",
            },
            # Ableist language
            "normal": {
                "alternatives": ["typical", "standard", "usual"],
                "severity": "medium",
                "explanation": "'Normal' implies disability is abnormal; use neutral terms",
            },
            "suffers from": {
                "alternatives": ["has", "experiences", "lives with"],
                "severity": "medium",
                "explanation": "Person-first language; avoid victim framing",
            },
            "confined to a wheelchair": {
                "alternatives": ["uses a wheelchair", "wheelchair user"],
                "severity": "high",
                "explanation": "Wheelchairs provide mobility, not confinement; use empowering language",
            },
            "wheelchair-bound": {
                "alternatives": ["uses a wheelchair", "wheelchair user"],
                "severity": "high",
                "explanation": "Negative framing; wheelchairs enable mobility",
            },
        }

        # Check for problematic phrases requiring transportation
        transport_patterns = [
            (
                r"\bmust have (a )?driver'?s? licen[cs]e\b",
                "May exclude candidates unable to drive due to disability",
                [
                    "reliable transportation required",
                    "ability to travel to work locations",
                ],
                "medium",
            ),
            (
                r"\bmust (be able to )?drive\b",
                "Excludes candidates who cannot drive",
                ["transportation to sites required", "ability to reach work locations"],
                "medium",
            ),
            (
                r"\bown (a )?car\b",
                "May exclude candidates who cannot drive",
                ["reliable transportation", "means of reaching work sites"],
                "medium",
            ),
        ]

        for pattern, explanation, alternatives, severity in transport_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                issues.append(
                    {
                        "type": "disability",
                        "description": explanation,
                        "problematic_text": match.group(),
                        "suggested_alternatives": alternatives,
                        "severity": severity,
                        "start_index": match.start(),
                        "end_index": match.end(),
                    }
                )

        # Check for disability bias terms
        for term, info in disability_bias_patterns.items():
            pattern = r"\b" + re.escape(term) + r"\b"
            for match in re.finditer(pattern, text, re.IGNORECASE):
                issues.append(
                    {
                        "type": "disability",
                        "description": info["explanation"],
                        "problematic_text": match.group(),
                        "suggested_alternatives": info["alternatives"],
                        "severity": info["severity"],
                        "start_index": match.start(),
                        "end_index": match.end(),
                    }
                )

        # Check for unnecessary physical requirements (often proxy for disability discrimination)
        unnecessary_physical_patterns = [
            (
                r"\b(must|required to) be able to (stand|sit|walk) for (long|extended) periods?\b",
                "Consider if this is essential or can be accommodated",
                [
                    "position may involve periods of standing/sitting",
                    "reasonable accommodation available",
                ],
                "medium",
            ),
            (
                r"\bmust be physically capable\b",
                "Vague and potentially discriminatory",
                [
                    "must be able to perform essential job functions",
                    "with or without accommodation",
                ],
                "medium",
            ),
        ]

        for (
            pattern,
            explanation,
            alternatives,
            severity,
        ) in unnecessary_physical_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                issues.append(
                    {
                        "type": "disability",
                        "description": explanation,
                        "problematic_text": match.group(),
                        "suggested_alternatives": alternatives,
                        "severity": severity,
                        "start_index": match.start(),
                        "end_index": match.end(),
                    }
                )

        return issues

    def _check_cultural_bias(self, text: str) -> List[Dict[str, Any]]:
        """
        Check for cultural and socioeconomic bias.

        Detects language that may exclude candidates from diverse
        cultural backgrounds or socioeconomic circumstances.
        """
        issues = []

        # Cultural bias patterns
        cultural_bias_patterns = {
            # Geographic/cultural requirements
            "north american experience": {
                "alternatives": [
                    "relevant international experience",
                    "experience in comparable markets",
                ],
                "severity": "high",
                "explanation": "Excludes qualified international candidates; focus on skills not geography",
            },
            "western experience": {
                "alternatives": [
                    "relevant market experience",
                    "experience in similar contexts",
                ],
                "severity": "high",
                "explanation": "Geographic bias; unnecessarily excludes international talent",
            },
            "canadian experience": {
                "alternatives": ["relevant experience", "transferable experience"],
                "severity": "medium",
                "explanation": "May exclude new immigrants; focus on skills and qualifications",
            },
            "local experience": {
                "alternatives": ["relevant experience", "applicable experience"],
                "severity": "low",
                "explanation": "May discourage diverse candidates; clarify if truly necessary",
            },
            # Cultural assumptions
            "native english speaker": {
                "alternatives": [
                    "fluent in English",
                    "strong English communication skills",
                ],
                "severity": "high",
                "explanation": "Discriminatory; focus on proficiency not native speaker status",
            },
            "native speaker": {
                "alternatives": ["fluent", "proficient", "strong communication skills"],
                "severity": "high",
                "explanation": "Discriminates against multilingual candidates",
            },
            "perfect english": {
                "alternatives": [
                    "strong English skills",
                    "professional English proficiency",
                ],
                "severity": "medium",
                "explanation": "Unnecessarily high bar; may exclude ESL speakers",
            },
            # Socioeconomic barriers
            "own laptop": {
                "alternatives": [
                    "laptop provided",
                    "access to computer",
                    "equipment provided",
                ],
                "severity": "medium",
                "explanation": "Creates socioeconomic barrier; employer should provide equipment",
            },
            "own computer": {
                "alternatives": ["computer provided", "equipment supplied"],
                "severity": "medium",
                "explanation": "Socioeconomic barrier; provide necessary equipment",
            },
            "home office": {
                "alternatives": [
                    "remote work setup provided",
                    "workspace arrangements available",
                ],
                "severity": "low",
                "explanation": "Assumes candidate has suitable home workspace; offer support",
            },
            "professional wardrobe": {
                "alternatives": [
                    "business appropriate attire",
                    "dress code guidelines provided",
                ],
                "severity": "low",
                "explanation": "May create economic barrier; be specific about requirements",
            },
            # Educational elitism
            "top-tier university": {
                "alternatives": ["relevant degree", "appropriate qualifications"],
                "severity": "high",
                "explanation": "Elitist and exclusionary; focus on competencies not prestige",
            },
            "ivy league": {
                "alternatives": ["strong academic background", "relevant education"],
                "severity": "high",
                "explanation": "Excludes qualified candidates based on school prestige",
            },
            "prestigious university": {
                "alternatives": ["accredited institution", "recognized degree program"],
                "severity": "high",
                "explanation": "Focus on qualifications not institution prestige",
            },
        }

        # Check for cultural bias terms
        for term, info in cultural_bias_patterns.items():
            pattern = r"\b" + re.escape(term) + r"\b"
            for match in re.finditer(pattern, text, re.IGNORECASE):
                issues.append(
                    {
                        "type": "cultural",
                        "description": info["explanation"],
                        "problematic_text": match.group(),
                        "suggested_alternatives": info["alternatives"],
                        "severity": info["severity"],
                        "start_index": match.start(),
                        "end_index": match.end(),
                    }
                )

        # Check for networking/connection requirements (privilege indicator)
        networking_patterns = [
            (
                r"\bstrong network\b",
                "May favor candidates with existing privilege and connections",
                ["ability to build relationships", "collaborative approach"],
                "low",
            ),
            (
                r"\bwell-connected\b",
                "Favors candidates from privileged backgrounds",
                ["strong relationship-building skills", "collaborative"],
                "medium",
            ),
            (
                r"\bestablished connections?\b",
                "May exclude diverse candidates without existing networks",
                ["ability to develop professional relationships"],
                "low",
            ),
        ]

        for pattern, explanation, alternatives, severity in networking_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                issues.append(
                    {
                        "type": "cultural",
                        "description": explanation,
                        "problematic_text": match.group(),
                        "suggested_alternatives": alternatives,
                        "severity": severity,
                        "start_index": match.start(),
                        "end_index": match.end(),
                    }
                )

        # Check for cultural fit language (can be code for bias)
        cultural_fit_patterns = [
            (
                r"\bcultural fit\b",
                "Vague and often used to exclude diverse candidates",
                ["alignment with values", "team collaboration"],
                "medium",
            ),
            (
                r"\bfit our culture\b",
                "May be code for preferring similar backgrounds",
                ["align with our values", "work collaboratively"],
                "medium",
            ),
            (
                r"\bfit in with (the|our) team\b",
                "Could discourage diverse candidates",
                ["collaborate effectively", "work well with team"],
                "low",
            ),
        ]

        for pattern, explanation, alternatives, severity in cultural_fit_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                issues.append(
                    {
                        "type": "cultural",
                        "description": explanation,
                        "problematic_text": match.group(),
                        "suggested_alternatives": alternatives,
                        "severity": severity,
                        "start_index": match.start(),
                        "end_index": match.end(),
                    }
                )

        return issues

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
        """
        Enhance template sections using AI.

        Uses GPT-4 to improve clarity, professionalism, and completeness
        of job description sections.

        Args:
            sections: Dictionary of section names to content
            classification: Job classification (e.g., "EX-01")
            language: Language code ("en" or "fr")

        Returns:
            Enhanced sections dictionary
        """
        try:
            # Prepare prompt for AI enhancement
            sections_text = "\n\n".join(
                [f"## {name}\n{content}" for name, content in sections.items()]
            )

            prompt = f"""You are an expert in writing professional government job descriptions.

Classification: {classification}
Language: {language}

Current job description sections:
{sections_text}

Please enhance these sections by:
1. Improving clarity and readability
2. Ensuring professional tone
3. Adding missing key details where appropriate
4. Maintaining government job description standards
5. Preserving the original meaning and intent

Return the enhanced sections in the same format, with each section clearly marked.
Keep the section names exactly the same."""

            if self.client is None:
                raise ValueError("OpenAI client is not initialized")

            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in writing professional government job descriptions.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # Lower temperature for more consistent, professional output
                max_tokens=2000,
            )

            enhanced_text = response.choices[0].message.content.strip()

            # Parse enhanced sections back into dictionary
            enhanced_sections = {}
            current_section = None
            current_content: list[str] = []

            for line in enhanced_text.split("\n"):
                if line.startswith("## "):
                    # Save previous section
                    if current_section and current_content:
                        enhanced_sections[current_section] = "\n".join(
                            current_content
                        ).strip()
                    # Start new section
                    current_section = line[3:].strip()
                    current_content = []
                elif current_section:
                    current_content.append(line)

            # Save last section
            if current_section and current_content:
                enhanced_sections[current_section] = "\n".join(current_content).strip()

            # Fallback to original sections if parsing failed
            if not enhanced_sections:
                logger.warning("Failed to parse AI-enhanced sections, using originals")
                return sections

            # Only use enhanced sections that were in the original
            result = {}
            for section_name in sections.keys():
                if section_name in enhanced_sections:
                    result[section_name] = enhanced_sections[section_name]
                else:
                    result[section_name] = sections[section_name]

            logger.info(
                f"Successfully enhanced {len(result)} template sections with AI"
            )
            return result

        except Exception as e:
            logger.error(f"Error in AI enhancement: {e}", exc_info=True)
            # Return original sections on any error
            return sections

    # Phase 3: Quality Scoring Methods

    def calculate_readability_scores(self, text: str) -> Dict[str, Any]:
        """
        Calculate comprehensive readability metrics using textstat.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with readability scores and analysis
        """
        if not textstat:
            logger.warning("textstat not available, returning default scores")
            return {
                "flesch_reading_ease": None,
                "flesch_kincaid_grade": None,
                "smog_index": None,
                "automated_readability_index": None,
                "coleman_liau_index": None,
                "reading_level": "Unknown",
                "meets_target": False,
                "recommendations": [
                    "Install textstat library for readability analysis"
                ],
            }

        if not text or len(text.strip()) < 100:
            return {
                "flesch_reading_ease": None,
                "flesch_kincaid_grade": None,
                "smog_index": None,
                "automated_readability_index": None,
                "coleman_liau_index": None,
                "reading_level": "Insufficient text",
                "meets_target": False,
                "recommendations": [
                    "Provide at least 100 characters of text for accurate analysis"
                ],
            }

        try:
            # Calculate multiple readability metrics
            flesch_ease = textstat.flesch_reading_ease(text)
            flesch_grade = textstat.flesch_kincaid_grade(text)
            smog = textstat.smog_index(text)
            ari = textstat.automated_readability_index(text)
            coleman_liau = textstat.coleman_liau_index(text)

            # Determine reading level based on Flesch-Kincaid Grade
            # Target: Grade 8-10 for government documents (accessible to general public)
            if flesch_grade <= 6:
                reading_level = "Elementary"
            elif flesch_grade <= 8:
                reading_level = "Easy"
            elif flesch_grade <= 10:
                reading_level = "Standard"  # Target range
            elif flesch_grade <= 12:
                reading_level = "Moderate"
            elif flesch_grade <= 14:
                reading_level = "Difficult"
            else:
                reading_level = "Very Difficult"

            # Check if meets target (Grade 8-10 for accessibility)
            meets_target = 8.0 <= flesch_grade <= 10.0

            # Generate recommendations
            recommendations = []
            if flesch_grade < 8.0:
                recommendations.append(
                    "Text is below target reading level. Consider adding more complex vocabulary and sentence structures for professional context."
                )
            elif flesch_grade > 10.0:
                recommendations.append(
                    "Text exceeds target reading level. Consider simplifying sentences and using clearer language for better accessibility."
                )
            if flesch_grade > 12.0:
                recommendations.append(
                    "Reading level is too high for general audience. Break down complex sentences and reduce jargon."
                )
            if flesch_ease < 50:
                recommendations.append(
                    "Text is difficult to read (Flesch score < 50). Use shorter sentences and simpler words."
                )
            if not meets_target:
                recommendations.append(
                    "Target reading level for government documents is Grade 8-10 for optimal accessibility."
                )

            return {
                "flesch_reading_ease": round(flesch_ease, 2),
                "flesch_kincaid_grade": round(flesch_grade, 2),
                "smog_index": round(smog, 2),
                "automated_readability_index": round(ari, 2),
                "coleman_liau_index": round(coleman_liau, 2),
                "reading_level": reading_level,
                "target_grade_level": 9.0,  # Middle of 8-10 range
                "meets_target": meets_target,
                "recommendations": recommendations
                if recommendations
                else ["Readability is within target range"],
            }

        except Exception as e:
            logger.error(f"Error calculating readability scores: {e}")
            return {
                "flesch_reading_ease": None,
                "flesch_kincaid_grade": None,
                "smog_index": None,
                "automated_readability_index": None,
                "coleman_liau_index": None,
                "reading_level": "Error",
                "meets_target": False,
                "recommendations": [f"Error analyzing readability: {str(e)}"],
            }

    def calculate_completeness_score(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate completeness score based on required sections and content quality.

        Args:
            job_data: Dictionary containing job description data with sections

        Returns:
            Dictionary with completeness metrics
        """
        # Define required sections for a complete job description
        required_sections = {
            "general_accountability": {
                "name": "General Accountability",
                "min_words": 50,
                "weight": 0.30,
            },
            "organization_structure": {
                "name": "Organization Structure",
                "min_words": 30,
                "weight": 0.15,
            },
            "key_responsibilities": {
                "name": "Key Responsibilities / Specific Accountabilities",
                "min_words": 100,
                "weight": 0.30,
            },
            "qualifications": {
                "name": "Qualifications / Knowledge & Skills",
                "min_words": 50,
                "weight": 0.25,
            },
        }

        # Check sections field (could be list of section objects or dict)
        sections_data = {}
        if isinstance(job_data.get("sections"), list):
            # Convert list of sections to dict
            for section in job_data["sections"]:
                if isinstance(section, dict) and "section_type" in section:
                    sections_data[section["section_type"]] = section.get(
                        "section_content", ""
                    )
        elif isinstance(job_data.get("sections"), dict):
            sections_data = job_data["sections"]

        # Analyze each section
        section_scores = {}
        present_sections = []
        adequate_sections = []
        missing_sections = []
        thin_sections = []

        total_weight = 0.0
        weighted_score = 0.0

        for section_key, section_info in required_sections.items():
            section_content = sections_data.get(section_key, "")

            if section_content and section_content.strip():
                present_sections.append(section_key)
                word_count = len(section_content.split())
                min_words: int = section_info["min_words"]  # type: ignore[assignment]
                weight: float = section_info["weight"]  # type: ignore[assignment]

                # Calculate section score (0-1)
                if word_count >= min_words:
                    section_score = 1.0
                    adequate_sections.append(section_key)
                else:
                    # Partial credit based on word count
                    section_score = min(word_count / min_words, 0.9)
                    thin_sections.append(
                        {
                            "section": section_info["name"],
                            "word_count": word_count,
                            "min_required": min_words,
                        }
                    )

                weighted_score += section_score * weight
                total_weight += weight

                section_scores[section_key] = {
                    "name": section_info["name"],
                    "present": True,
                    "word_count": word_count,
                    "adequate": word_count >= min_words,
                    "score": round(section_score, 2),
                }
            else:
                missing_sections.append(section_info["name"])
                section_scores[section_key] = {
                    "name": section_info["name"],
                    "present": False,
                    "word_count": 0,
                    "adequate": False,
                    "score": 0.0,
                }

        # Calculate overall completeness
        if total_weight > 0:
            # Cast to float explicitly to avoid type errors
            section_weights: list[float] = [
                float(s["weight"])
                if isinstance(s["weight"], (int, float, str))
                else 0.0
                for s in required_sections.values()
            ]
            total_section_weight = sum(section_weights)
            completeness_score = weighted_score / total_section_weight
        else:
            completeness_score = 0.0

        # Generate recommendations
        recommendations: list[str] = []
        if missing_sections:
            # Cast to list of strings to avoid type errors
            missing_section_names: list[str] = [str(name) for name in missing_sections]  # type: ignore[arg-type]
            recommendations.append(
                f"Add missing sections: {', '.join(missing_section_names)}"
            )
        if thin_sections:
            for thin in thin_sections:
                recommendations.append(
                    f"{thin['section']} needs expansion: {thin['word_count']} words (minimum {thin['min_required']})"
                )
        if completeness_score >= 0.9:
            recommendations.append("Job description is comprehensive")
        elif completeness_score >= 0.7:
            recommendations.append(
                "Job description is mostly complete but could be enhanced"
            )
        else:
            recommendations.append(
                "Job description needs significant additions to meet standards"
            )

        return {
            "completeness_score": round(completeness_score, 2),
            "sections_present": len(present_sections),
            "sections_required": len(required_sections),
            "sections_adequate": len(adequate_sections),
            "missing_sections": missing_sections,
            "thin_sections": thin_sections,
            "section_scores": section_scores,
            "recommendations": recommendations,
        }

    def calculate_clarity_score(self, text: str) -> Dict[str, Any]:
        """
        Calculate clarity and structure score.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with clarity metrics
        """
        if not text or len(text.strip()) < 50:
            return {
                "clarity_score": 0.0,
                "avg_sentence_length": 0,
                "long_sentences": 0,
                "paragraph_count": 0,
                "recommendations": ["Insufficient text for clarity analysis"],
            }

        # Split into sentences (basic splitting)
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        sentence_lengths = [len(s.split()) for s in sentences]

        # Calculate metrics
        avg_sentence_length = (
            sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
        )
        long_sentences = sum(1 for length in sentence_lengths if length > 30)

        # Count paragraphs (double line breaks)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        paragraph_count = len(paragraphs)

        # Score clarity (inverse relationship with complexity)
        # Optimal: 15-25 words per sentence
        if 15 <= avg_sentence_length <= 25:
            length_score = 1.0
        elif avg_sentence_length < 15:
            length_score = max(0.7, avg_sentence_length / 15)
        else:
            length_score = max(0.3, 25 / avg_sentence_length)

        # Penalize excessive long sentences
        long_sentence_penalty = min(0.3, (long_sentences / len(sentences)) * 0.5)
        clarity_score = max(0.0, length_score - long_sentence_penalty)

        # Recommendations
        recommendations = []
        if avg_sentence_length > 25:
            recommendations.append(
                f"Average sentence length is {avg_sentence_length:.1f} words. Consider breaking down complex sentences (target: 15-25 words)."
            )
        if long_sentences > len(sentences) * 0.2:
            recommendations.append(
                f"{long_sentences} sentences exceed 30 words. Simplify for better clarity."
            )
        if paragraph_count < 3 and len(text) > 500:
            recommendations.append(
                "Add paragraph breaks to improve readability and visual structure."
            )
        if clarity_score >= 0.8:
            recommendations.append("Text has good clarity and structure")

        return {
            "clarity_score": round(clarity_score, 2),
            "avg_sentence_length": round(avg_sentence_length, 1),
            "optimal_range": "15-25 words",
            "sentence_count": len(sentences),
            "long_sentences": long_sentences,
            "paragraph_count": paragraph_count,
            "recommendations": recommendations
            if recommendations
            else ["Clarity is acceptable"],
        }

    async def calculate_comprehensive_quality_score(
        self, job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive quality score combining all quality dimensions.

        This is the main quality assessment method that combines:
        - Readability (20%)
        - Completeness (25%)
        - Clarity & Structure (15%)
        - Inclusivity/Bias-free (20%)
        - Compliance (20%)

        Args:
            job_data: Complete job description data

        Returns:
            Comprehensive quality assessment with overall score (0-100)
        """
        # Extract full text for analysis
        full_text = ""
        if isinstance(job_data.get("sections"), list):
            full_text = " ".join(
                section.get("section_content", "")
                for section in job_data["sections"]
                if isinstance(section, dict)
            )
        elif isinstance(job_data.get("sections"), dict):
            full_text = " ".join(job_data["sections"].values())
        elif job_data.get("raw_content"):
            full_text = job_data["raw_content"]

        # Calculate individual dimension scores
        readability = self.calculate_readability_scores(full_text)
        completeness = self.calculate_completeness_score(job_data)
        clarity = self.calculate_clarity_score(full_text)
        bias_analysis = await self.analyze_bias(full_text)

        # Convert scores to 0-1 scale for consistency
        readability_score = 1.0 if readability.get("meets_target") else 0.7
        if readability.get("flesch_kincaid_grade"):
            grade = readability["flesch_kincaid_grade"]
            # Closer to target (9.0) is better
            readability_score = max(0.0, 1.0 - abs(grade - 9.0) / 10.0)

        completeness_score = completeness.get("completeness_score", 0.0)
        clarity_score = clarity.get("clarity_score", 0.0)
        inclusivity_score = bias_analysis.get("inclusivity_score", 1.0)

        # Calculate compliance score
        compliance = await self.check_compliance(full_text)
        compliance_score = compliance.get("compliance_score", 0.0)

        # Calculate weighted overall score (0-100 scale)
        overall_score = (
            readability_score * 0.20
            + completeness_score * 0.25
            + clarity_score * 0.15
            + inclusivity_score * 0.20
            + compliance_score * 0.20
        ) * 100

        # Determine quality level
        if overall_score >= 90:
            quality_level = "Excellent"
            quality_color = "green"
        elif overall_score >= 75:
            quality_level = "Good"
            quality_color = "blue"
        elif overall_score >= 60:
            quality_level = "Fair"
            quality_color = "yellow"
        else:
            quality_level = "Needs Improvement"
            quality_color = "red"

        # Aggregate all recommendations
        all_recommendations = []
        all_recommendations.extend(readability.get("recommendations", []))
        all_recommendations.extend(completeness.get("recommendations", []))
        all_recommendations.extend(clarity.get("recommendations", []))
        if bias_analysis.get("issues"):
            all_recommendations.append(
                f"Found {len(bias_analysis['issues'])} inclusivity issues to address"
            )

        # Prioritize top recommendations
        top_recommendations = (
            all_recommendations[:5]
            if all_recommendations
            else ["Job description meets quality standards"]
        )

        return {
            "overall_score": round(overall_score, 1),
            "quality_level": quality_level,
            "quality_color": quality_color,
            "dimension_scores": {
                "readability": {
                    "score": round(readability_score * 100, 1),
                    "weight": "20%",
                    "details": readability,
                },
                "completeness": {
                    "score": round(completeness_score * 100, 1),
                    "weight": "25%",
                    "details": completeness,
                },
                "clarity": {
                    "score": round(clarity_score * 100, 1),
                    "weight": "15%",
                    "details": clarity,
                },
                "inclusivity": {
                    "score": round(inclusivity_score * 100, 1),
                    "weight": "20%",
                    "details": bias_analysis,
                },
                "compliance": {
                    "score": round(compliance_score * 100, 1),
                    "weight": "20%",
                    "details": {
                        "compliant": compliance.get("compliant", False),
                        "issues": compliance.get("issues", []),
                        "frameworks_checked": compliance.get(
                            "frameworks",
                            [
                                "official_languages",
                                "employment_equity",
                                "accessibility",
                            ],
                        ),
                        "issue_count": len(compliance.get("issues", [])),
                    },
                },
            },
            "top_recommendations": top_recommendations,
            "improvement_priority": self._determine_improvement_priority(
                readability_score,
                completeness_score,
                clarity_score,
                inclusivity_score,
                compliance_score,
            ),
        }

    def _determine_improvement_priority(
        self,
        readability: float,
        completeness: float,
        clarity: float,
        inclusivity: float,
        compliance: float,
    ) -> List[str]:
        """Determine which dimensions need improvement most urgently."""
        scores = {
            "Readability": readability,
            "Completeness": completeness,
            "Clarity & Structure": clarity,
            "Inclusivity": inclusivity,
            "Compliance": compliance,
        }

        # Sort by score (lowest first) and return bottom 3
        sorted_dimensions = sorted(scores.items(), key=lambda x: x[1])
        priority_areas = [dim for dim, score in sorted_dimensions if score < 0.7]

        if not priority_areas:
            return ["All dimensions meet acceptable standards"]

        return priority_areas[:3]  # Top 3 priorities

    # Phase 3: Content Generation Methods

    async def complete_section(
        self,
        section_type: str,
        partial_content: str,
        classification: str,
        language: str = "en",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Auto-complete a job description section using GPT-4.

        Args:
            section_type: Type of section (e.g., "general_accountability", "qualifications")
            partial_content: Existing partial content to complete
            classification: Job classification (e.g., "EX-01", "EC-05")
            language: Content language ("en" or "fr")
            context: Additional context about the job

        Returns:
            Dictionary with completed content and metadata
        """
        if not self.client:
            return {
                "completed_content": partial_content,
                "suggestions": [],
                "confidence": 0.0,
                "message": "GPT-4 not available - completion feature disabled",
            }

        try:
            # Build context string
            context_str = f"Classification: {classification}\nLanguage: {language}"
            if context:
                if context.get("department"):
                    context_str += f"\nDepartment: {context['department']}"
                if context.get("reporting_to"):
                    context_str += f"\nReports to: {context['reporting_to']}"

            # Section-specific prompts
            section_prompts = {
                "general_accountability": "the overall purpose and primary responsibility",
                "organization_structure": "reporting relationships and organizational context",
                "key_responsibilities": "specific duties and accountabilities",
                "qualifications": "education, experience, and skill requirements",
                "nature_and_scope": "the scope and impact of the position",
            }

            section_desc = section_prompts.get(
                section_type, "this section of the job description"
            )

            prompt = f"""You are an expert in writing Canadian government job descriptions. Complete the following section intelligently and professionally.

{context_str}

Section Type: {section_type.replace("_", " ").title()}
Purpose: This section describes {section_desc}

Partial Content:
\"\"\"{partial_content}\"\"\"

Instructions:
1. Complete the content naturally from where it left off
2. Maintain the same tone, style, and formality level
3. Keep it concise and professional (government style)
4. Use active voice where possible
5. For French content, use proper government terminology
6. Aim for 2-4 additional sentences unless more context is clearly needed

Return ONLY the completion (the new text to add), not the original partial content."""

            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Canadian government HR writer specializing in job descriptions. You understand Treasury Board standards and bilingual requirements.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )

            completion = response.choices[0].message.content.strip()

            # Combine partial and completion
            completed_content = partial_content.rstrip() + " " + completion

            logger.info(
                f"Completed {section_type} section ({len(completion)} characters added)"
            )

            return {
                "completed_content": completed_content,
                "completion_text": completion,
                "confidence": 0.85,
                "message": "Section completed successfully",
            }

        except Exception as e:
            logger.error(f"Section completion error: {e}")
            return {
                "completed_content": partial_content,
                "suggestions": [],
                "confidence": 0.0,
                "message": f"Completion failed: {str(e)}",
            }

    async def enhance_content(
        self,
        text: str,
        enhancement_types: List[str],
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Enhance text for clarity, active voice, and professionalism.

        Args:
            text: Text to enhance
            enhancement_types: Types of enhancements to apply
                - "clarity": Simplify and clarify complex sentences
                - "active_voice": Convert passive to active voice
                - "conciseness": Remove redundancy and wordiness
                - "formality": Adjust tone for government formality
                - "bias_free": Rewrite to remove biased language
            language: Content language

        Returns:
            Dictionary with enhanced text and change summary
        """
        if not self.client:
            return {
                "enhanced_text": text,
                "changes": [],
                "message": "GPT-4 not available - enhancement feature disabled",
            }

        try:
            # Build enhancement instructions
            instructions = []
            if "clarity" in enhancement_types:
                instructions.append(
                    "- Simplify complex sentences while preserving meaning"
                )
            if "active_voice" in enhancement_types:
                instructions.append(
                    "- Convert passive voice to active voice where appropriate"
                )
            if "conciseness" in enhancement_types:
                instructions.append("- Remove redundancy and wordiness")
            if "formality" in enhancement_types:
                instructions.append("- Ensure appropriate professional/government tone")
            if "bias_free" in enhancement_types:
                instructions.append("- Remove any biased or non-inclusive language")

            instructions_str = "\n".join(instructions)

            prompt = f"""Enhance the following job description text according to these requirements:

{instructions_str}

Original Text:
\"\"\"{text}\"\"\"

Provide:
1. Enhanced version of the text
2. Brief summary of key changes made (bullet points)

Format your response as:
ENHANCED:
[enhanced text here]

CHANGES:
- [change 1]
- [change 2]
..."""

            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an expert editor for government job descriptions in {language}. You enhance clarity while maintaining professionalism and accuracy.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_tokens=1000,
            )

            response_text = response.choices[0].message.content.strip()

            # Parse response
            enhanced_text = text  # fallback
            changes = []

            if "ENHANCED:" in response_text:
                parts = response_text.split("ENHANCED:")
                if len(parts) > 1:
                    enhanced_section = parts[1].split("CHANGES:")[0].strip()
                    enhanced_text = enhanced_section

            if "CHANGES:" in response_text:
                changes_section = response_text.split("CHANGES:")[1].strip()
                changes = [
                    line.strip("- ").strip()
                    for line in changes_section.split("\n")
                    if line.strip().startswith("-")
                ]

            logger.info(f"Enhanced content with {len(changes)} changes")

            return {
                "enhanced_text": enhanced_text,
                "original_text": text,
                "changes": changes,
                "enhancement_types": enhancement_types,
                "message": "Content enhanced successfully",
            }

        except Exception as e:
            logger.error(f"Content enhancement error: {e}")
            return {
                "enhanced_text": text,
                "changes": [],
                "message": f"Enhancement failed: {str(e)}",
            }

    async def save_improved_content(self, job_id: int, improved_content: str) -> None:
        """
        Save the improved content of a job description.

        Args:
            job_id: The ID of the job to update.
            improved_content: The new content of the job description.
        """
        # In a real application, you would update the job description in the database here.
        # For now, we will just log the action.
        logger.info(f"Saving improved content for job {job_id}")

    async def translate_content(self, text: str, target_language: str) -> str:
        """
        Translate text to the specified target language.

        Args:
            text: The text to translate.
            target_language: The language to translate the text to.

        Returns:
            The translated text.
        """
        if not self.client:
            return text

        try:
            prompt = f"""Translate the following text to {target_language}.
Return ONLY the translated text, with no extra commentary or formatting.

Original Text:
\"\"\"
{text}
\"\"\"

Translated Text:
"""
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional translator fluent in English and {target_language}.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=2048,
            )

            translated_text = response.choices[0].message.content.strip()
            logger.info(f"Successfully translated text to {target_language}")
            return translated_text

        except Exception as e:
            logger.error(f"Error during translation: {e}")
            return text

    async def generate_job_posting(self, job_id: int) -> str:
        """
        Generate a job posting from a job description.

        Args:
            job_id: The ID of the job to generate the posting from.

        Returns:
            The generated job posting.
        """
        # In a real application, you would fetch the job description from the database here.
        # For now, we will just use a dummy job description.
        job_description = "This is a dummy job description."

        if not self.client:
            return "Job posting generation is not available."

        try:
            prompt = f"""Generate a compelling job posting from the following job description.
The job posting should be engaging and attract a wide range of qualified candidates.

Job Description:
\"\"\"
{job_description}
\"\"\"

Job Posting:
"""
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in writing compelling job postings.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1024,
            )

            job_posting = response.choices[0].message.content.strip()
            logger.info(f"Successfully generated job posting for job {job_id}")
            return job_posting

        except Exception as e:
            logger.error(f"Error during job posting generation: {e}")
            return "Failed to generate job posting."

    async def run_predictive_analysis(self, job_id: int) -> Dict[str, Any]:
        """
        Run predictive analysis on a job description.

        Args:
            job_id: The ID of the job to analyze.

        Returns:
            A dictionary with the predictive analysis results.
        """
        # In a real application, you would fetch the job description from the database here.
        # For now, we will just use a dummy job description.
        job_description = "This is a dummy job description."

        if not self.client:
            return {"error": "Predictive analysis is not available."}

        try:
            prompt = f"""Analyze the following job description and provide a predictive analysis.
The analysis should include predictions for time-to-fill, applicant volume, and content effectiveness.

Job Description:
\"\"\"
{job_description}
\"\"\"

Predictive Analysis:
"""
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in HR analytics and predictive modeling.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1024,
            )

            analysis = response.choices[0].message.content.strip()
            logger.info(f"Successfully ran predictive analysis for job {job_id}")
            return {"analysis": analysis}

        except Exception as e:
            logger.error(f"Error during predictive analysis: {e}")
            return {"error": "Failed to run predictive analysis."}

    async def generate_inline_suggestions(
        self,
        text: str,
        cursor_position: int,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate smart inline suggestions based on cursor position and context.

        Args:
            text: Full text content
            cursor_position: Current cursor position in text
            context: Additional context (section type, etc.)

        Returns:
            Dictionary with suggestions and context
        """
        if not self.client:
            return {
                "suggestions": [],
                "message": "GPT-4 not available",
            }

        try:
            # Get text around cursor
            start = max(0, cursor_position - 200)
            end = min(len(text), cursor_position + 50)
            surrounding_text = text[start:end]

            # Mark cursor position
            cursor_marker = "[CURSOR]"
            marked_text = (
                surrounding_text[: cursor_position - start]
                + cursor_marker
                + surrounding_text[cursor_position - start :]
            )

            prompt = f"""Given the following job description text with cursor position marked, suggest 2-3 intelligent completions or improvements.

Text with cursor position:
\"\"\"{marked_text}\"\"\"

Provide suggestions as a JSON array:
[
  {{"text": "suggestion 1", "reason": "why this helps"}},
  {{"text": "suggestion 2", "reason": "why this helps"}}
]

Consider:
- Natural sentence completion
- Common patterns in job descriptions
- Professional language
- Government writing standards

Return ONLY valid JSON."""

            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI writing assistant for job descriptions. Provide helpful, contextual suggestions.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.6,
                max_tokens=300,
            )

            response_text = response.choices[0].message.content.strip()

            # Extract JSON
            if "```json" in response_text:
                response_text = (
                    response_text.split("```json")[1].split("```")[0].strip()
                )
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            import json

            suggestions = json.loads(response_text)

            return {
                "suggestions": suggestions,
                "cursor_position": cursor_position,
                "message": "Suggestions generated successfully",
            }

        except Exception as e:
            logger.error(f"Inline suggestions error: {e}")
            return {
                "suggestions": [],
                "message": f"Suggestions failed: {str(e)}",
            }
