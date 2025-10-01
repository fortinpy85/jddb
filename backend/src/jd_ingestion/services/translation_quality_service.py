"""
Translation Quality Service

Provides translation quality assessment and validation with:
- Quality scoring algorithms (0-100)
- Consistency checking across sections
- Terminology validation
- Translation completeness analysis
- Review and approval workflow support
"""

import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class TranslationQualityService:
    """Service for assessing and validating translation quality."""

    # Common terminology that should be consistent
    GOVERNMENT_TERMINOLOGY = {
        "en": {
            "Deputy Minister": "sous-ministre",
            "Director": "directeur",
            "strategic planning": "planification stratégique",
            "policy development": "élaboration des politiques",
            "accountability": "responsabilité",
            "framework": "cadre",
        },
        "fr": {
            "sous-ministre": "Deputy Minister",
            "directeur": "Director",
            "planification stratégique": "strategic planning",
            "élaboration des politiques": "policy development",
            "responsabilité": "accountability",
            "cadre": "framework",
        },
    }

    async def assess_translation_quality(
        self,
        english_text: str,
        french_text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Assess overall translation quality.

        Args:
            english_text: Source English text
            french_text: Target French text
            context: Additional context (domain, previous translations, etc.)

        Returns:
            Quality assessment with score and details
        """
        if not english_text or not french_text:
            return {
                "overall_score": 0,
                "completeness_score": 0,
                "length_ratio_score": 0,
                "terminology_score": 0,
                "consistency_score": 0,
                "issues": ["Missing text"],
                "warnings": [],
                "suggestions": ["Ensure both English and French text are provided"],
            }

        # Calculate individual quality metrics
        completeness = self._check_completeness(english_text, french_text)
        length_ratio = self._check_length_ratio(english_text, french_text)
        terminology = self._check_terminology(english_text, french_text)
        formatting = self._check_formatting_consistency(english_text, french_text)

        # Calculate weighted overall score
        overall_score = (
            completeness["score"] * 0.3
            + length_ratio["score"] * 0.2
            + terminology["score"] * 0.3
            + formatting["score"] * 0.2
        )

        issues = []
        warnings = []
        suggestions = []

        # Collect issues from all checks
        if completeness["issues"]:
            issues.extend(completeness["issues"])
        if length_ratio["issues"]:
            warnings.extend(length_ratio["issues"])
        if terminology["issues"]:
            issues.extend(terminology["issues"])
        if formatting["issues"]:
            warnings.extend(formatting["issues"])

        # Generate suggestions
        if overall_score < 70:
            suggestions.append("Translation quality is below acceptable threshold")
        if completeness["score"] < 80:
            suggestions.append("Review translation completeness")
        if terminology["score"] < 80:
            suggestions.append("Check terminology consistency with glossary")

        return {
            "overall_score": round(overall_score, 1),
            "completeness_score": completeness["score"],
            "length_ratio_score": length_ratio["score"],
            "terminology_score": terminology["score"],
            "formatting_score": formatting["score"],
            "issues": issues,
            "warnings": warnings,
            "suggestions": suggestions,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _check_completeness(
        self, english_text: str, french_text: str
    ) -> Dict[str, Any]:
        """Check if translation is complete."""
        if not french_text.strip():
            return {"score": 0, "issues": ["Translation is empty"]}

        # Check for untranslated placeholders
        untranslated_patterns = [
            r"\[.*?\]",  # Bracketed placeholders
            r"\{.*?\}",  # Curly brace placeholders
        ]

        issues = []
        for pattern in untranslated_patterns:
            matches = re.findall(pattern, french_text)
            if matches:
                issues.append(
                    f"Untranslated placeholders found: {', '.join(matches[:3])}"
                )

        score = 100 if not issues else 50
        return {"score": score, "issues": issues}

    def _check_length_ratio(
        self, english_text: str, french_text: str
    ) -> Dict[str, Any]:
        """Check if translation length is reasonable."""
        en_len = len(english_text)
        fr_len = len(french_text)

        if en_len == 0:
            return {"score": 0, "issues": ["English text is empty"]}

        ratio = fr_len / en_len

        # French translations typically 10-30% longer than English
        issues = []
        if ratio < 0.8:
            issues.append("Translation may be too short (possible missing content)")
            score = 60
        elif ratio > 1.5:
            issues.append("Translation may be too long (possible verbosity)")
            score = 70
        else:
            score = 100

        return {"score": score, "issues": issues}

    def _check_terminology(self, english_text: str, french_text: str) -> Dict[str, Any]:
        """Check terminology consistency."""
        issues = []
        score = 100

        # Check for consistent translation of key terms
        for en_term, expected_fr_term in self.GOVERNMENT_TERMINOLOGY["en"].items():
            if en_term.lower() in english_text.lower():
                if expected_fr_term.lower() not in french_text.lower():
                    issues.append(
                        f"Term '{en_term}' should be translated as '{expected_fr_term}'"
                    )
                    score -= 15

        return {"score": max(0, score), "issues": issues}

    def _check_formatting_consistency(
        self, english_text: str, french_text: str
    ) -> Dict[str, Any]:
        """Check formatting consistency between source and target."""
        issues = []
        score = 100

        # Check bullet points
        en_bullets = english_text.count("•")
        fr_bullets = french_text.count("•")
        if en_bullets != fr_bullets:
            issues.append(
                f"Bullet point count mismatch (EN: {en_bullets}, FR: {fr_bullets})"
            )
            score -= 10

        # Check line breaks
        en_lines = english_text.count("\n")
        fr_lines = french_text.count("\n")
        if abs(en_lines - fr_lines) > 2:
            issues.append("Line break structure differs significantly")
            score -= 10

        return {"score": max(0, score), "issues": issues}

    async def check_document_consistency(
        self,
        segments: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Check consistency across all document segments.

        Args:
            segments: List of bilingual segments

        Returns:
            Consistency analysis results
        """
        issues = []
        terminology_usage: Dict[str, List[Dict[str, Any]]] = {}

        # Track terminology usage across segments
        for segment in segments:
            english = segment.get("english", "")
            french = segment.get("french", "")

            # Check each key term
            for en_term, expected_fr in self.GOVERNMENT_TERMINOLOGY["en"].items():
                if en_term.lower() in english.lower():
                    # Extract actual French translation used
                    if en_term not in terminology_usage:
                        terminology_usage[en_term] = []

                    # Simplified check - in production would use NLP
                    if french:
                        terminology_usage[en_term].append(
                            {"segment_id": segment["id"], "french_used": french}
                        )

        # Identify inconsistencies
        for term, usage_list in terminology_usage.items():
            if len(usage_list) > 1:
                # Check if same translation used everywhere
                expected_fr = self.GOVERNMENT_TERMINOLOGY["en"][term]
                inconsistent_segments = [
                    u["segment_id"]
                    for u in usage_list
                    if expected_fr.lower() not in u["french_used"].lower()
                ]

                if inconsistent_segments:
                    issues.append(
                        {
                            "type": "terminology_inconsistency",
                            "term": term,
                            "expected_translation": expected_fr,
                            "affected_segments": inconsistent_segments,
                        }
                    )

        consistency_score = 100 - (len(issues) * 10)

        return {
            "consistency_score": max(0, consistency_score),
            "issues": issues,
            "terminology_usage": terminology_usage,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def validate_translation(
        self,
        segment_id: str,
        english_text: str,
        french_text: str,
    ) -> Dict[str, Any]:
        """
        Validate a single translation segment.

        Args:
            segment_id: Segment identifier
            english_text: Source text
            french_text: Translation text

        Returns:
            Validation results with pass/fail status
        """
        quality = await self.assess_translation_quality(english_text, french_text)

        # Determine if translation passes validation
        passed = (
            quality["overall_score"] >= 70
            and quality["completeness_score"] >= 80
            and len(quality["issues"]) == 0
        )

        return {
            "segment_id": segment_id,
            "passed": passed,
            "quality_score": quality["overall_score"],
            "validation_details": quality,
            "recommendation": "approve" if passed else "review_required",
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def suggest_improvements(
        self,
        english_text: str,
        french_text: str,
    ) -> List[Dict[str, str]]:
        """
        Suggest improvements for translation.

        Args:
            english_text: Source text
            french_text: Current translation

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        # Check for common issues
        if not french_text.strip():
            suggestions.append(
                {
                    "type": "missing_translation",
                    "priority": "high",
                    "suggestion": "Translation is missing. Please provide French translation.",
                }
            )
            return suggestions

        # Check terminology
        for en_term, expected_fr in self.GOVERNMENT_TERMINOLOGY["en"].items():
            if (
                en_term.lower() in english_text.lower()
                and expected_fr.lower() not in french_text.lower()
            ):
                suggestions.append(
                    {
                        "type": "terminology",
                        "priority": "high",
                        "suggestion": f"Consider using '{expected_fr}' for '{en_term}'",
                        "term": en_term,
                        "recommended_translation": expected_fr,
                    }
                )

        # Check length ratio
        if len(english_text) > 0:
            ratio = len(french_text) / len(english_text)
            if ratio < 0.8:
                suggestions.append(
                    {
                        "type": "length",
                        "priority": "medium",
                        "suggestion": "Translation appears shorter than expected. Review for completeness.",
                    }
                )
            elif ratio > 1.5:
                suggestions.append(
                    {
                        "type": "length",
                        "priority": "low",
                        "suggestion": "Translation appears longer than expected. Consider being more concise.",
                    }
                )

        return suggestions

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (0-1)."""
        if not text1 or not text2:
            return 0.0

        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
