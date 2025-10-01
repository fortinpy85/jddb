"""
Template Generation Service

Provides AI-powered job description template generation with:
- Classification-based template selection
- Context-aware section suggestions
- Bilingual template generation (EN/FR)
- Template customization and variations
- Smart placeholder replacement
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class TemplateGenerationService:
    """Service for generating and managing job description templates."""

    # Template categories based on Canadian government classifications
    TEMPLATE_CATEGORIES = {
        "EX": "Executive",
        "EC": "Economics and Social Science Services",
        "PM": "Program Management",
        "AS": "Administrative Services",
        "CS": "Computer Systems",
        "IS": "Information Services",
        "PE": "Personnel Administration",
        "FI": "Financial Management",
        "CO": "Commerce",
        "EN": "Engineering and Scientific Support",
    }

    # Standard job description sections
    STANDARD_SECTIONS = [
        "position_summary",
        "key_responsibilities",
        "essential_qualifications",
        "asset_qualifications",
        "organizational_context",
        "working_conditions",
        "language_requirements",
    ]

    def __init__(self):
        """Initialize the template generation service."""
        self.templates_cache: Dict[str, Dict] = {}

    async def get_template_by_classification(
        self,
        classification: str,
        language: str = "en",
        level: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a template for a specific classification.

        Args:
            classification: Job classification (e.g., "EX", "EC", "PM")
            language: Template language ("en" or "fr")
            level: Classification level (e.g., "01", "02", "03")

        Returns:
            Template dictionary with sections and content
        """
        cache_key = f"{classification}_{level}_{language}"

        if cache_key in self.templates_cache:
            logger.info(f"Returning cached template for {cache_key}")
            return self.templates_cache[cache_key]

        template = self._generate_template(classification, language, level)
        self.templates_cache[cache_key] = template

        return template

    def _generate_template(
        self, classification: str, language: str, level: Optional[str]
    ) -> Dict[str, Any]:
        """Generate a template based on classification and language."""
        category_name = self.TEMPLATE_CATEGORIES.get(
            classification, "General Position"
        )

        if language == "fr":
            return self._generate_french_template(classification, category_name, level)
        else:
            return self._generate_english_template(classification, category_name, level)

    def _generate_english_template(
        self, classification: str, category_name: str, level: Optional[str]
    ) -> Dict[str, Any]:
        """Generate English template."""
        level_text = f"-{level}" if level else ""

        return {
            "classification": f"{classification}{level_text}",
            "category": category_name,
            "language": "en",
            "sections": {
                "position_summary": {
                    "title": "Position Summary",
                    "content": f"This {classification}{level_text} position in {category_name} is responsible for [key function]. "
                    f"The incumbent will [primary responsibility] and support [organizational goal].",
                    "placeholders": [
                        "[key function]",
                        "[primary responsibility]",
                        "[organizational goal]",
                    ],
                },
                "key_responsibilities": {
                    "title": "Key Responsibilities",
                    "content": "• Lead and manage [specific area of responsibility]\n"
                    "• Develop and implement [strategies/policies/programs]\n"
                    "• Provide expert advice and guidance on [subject matter]\n"
                    "• Collaborate with [stakeholders] to achieve [outcomes]\n"
                    "• Monitor, evaluate and report on [performance metrics]",
                    "placeholders": [
                        "[specific area of responsibility]",
                        "[strategies/policies/programs]",
                        "[subject matter]",
                        "[stakeholders]",
                        "[outcomes]",
                        "[performance metrics]",
                    ],
                },
                "essential_qualifications": {
                    "title": "Essential Qualifications",
                    "content": "Education:\n"
                    "• [Degree level] in [field of study] or an acceptable combination of education, training and/or experience\n\n"
                    "Experience:\n"
                    "• Significant* experience in [relevant area]\n"
                    "• Experience in [specific skill or responsibility]\n\n"
                    "*Significant experience is defined as the depth and breadth of experience normally associated with [duration].",
                    "placeholders": [
                        "[Degree level]",
                        "[field of study]",
                        "[relevant area]",
                        "[specific skill or responsibility]",
                        "[duration]",
                    ],
                },
                "asset_qualifications": {
                    "title": "Asset Qualifications",
                    "content": "• Experience with [specialized tools/systems]\n"
                    "• Knowledge of [relevant legislation/frameworks]\n"
                    "• Professional certification in [field]\n"
                    "• Experience working in [specific environment]",
                    "placeholders": [
                        "[specialized tools/systems]",
                        "[relevant legislation/frameworks]",
                        "[field]",
                        "[specific environment]",
                    ],
                },
                "organizational_context": {
                    "title": "Organizational Context",
                    "content": "This position is located within [Branch/Division] and reports to the [Supervisor Title]. "
                    "The organization is responsible for [mandate] and serves [client base].",
                    "placeholders": [
                        "[Branch/Division]",
                        "[Supervisor Title]",
                        "[mandate]",
                        "[client base]",
                    ],
                },
                "working_conditions": {
                    "title": "Working Conditions",
                    "content": "• Standard office environment with [specific conditions]\n"
                    "• [Travel requirements]\n"
                    "• [Overtime/on-call requirements]\n"
                    "• Hybrid work arrangement available",
                    "placeholders": [
                        "[specific conditions]",
                        "[travel requirements]",
                        "[overtime/on-call requirements]",
                    ],
                },
                "language_requirements": {
                    "title": "Language Requirements",
                    "content": "Bilingual Imperative: [BBB/CBC/CCC]\n"
                    "or\n"
                    "English or French Essential",
                    "placeholders": ["[BBB/CBC/CCC]"],
                },
            },
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "version": "1.0",
                "source": "template_generation_service",
            },
        }

    def _generate_french_template(
        self, classification: str, category_name: str, level: Optional[str]
    ) -> Dict[str, Any]:
        """Generate French template."""
        level_text = f"-{level}" if level else ""

        # Translate category names
        category_translations = {
            "Executive": "Direction",
            "Economics and Social Science Services": "Services d'économie et de sciences sociales",
            "Program Management": "Gestion de programmes",
            "Administrative Services": "Services administratifs",
            "Computer Systems": "Systèmes d'ordinateurs",
            "Information Services": "Services d'information",
            "Personnel Administration": "Administration du personnel",
            "Financial Management": "Gestion financière",
            "Commerce": "Commerce",
            "Engineering and Scientific Support": "Soutien technique et scientifique",
        }

        category_fr = category_translations.get(category_name, category_name)

        return {
            "classification": f"{classification}{level_text}",
            "category": category_fr,
            "language": "fr",
            "sections": {
                "position_summary": {
                    "title": "Sommaire du poste",
                    "content": f"Ce poste {classification}{level_text} en {category_fr} est responsable de [fonction clé]. "
                    f"Le titulaire devra [responsabilité principale] et soutenir [objectif organisationnel].",
                    "placeholders": [
                        "[fonction clé]",
                        "[responsabilité principale]",
                        "[objectif organisationnel]",
                    ],
                },
                "key_responsibilities": {
                    "title": "Responsabilités clés",
                    "content": "• Diriger et gérer [domaine de responsabilité spécifique]\n"
                    "• Élaborer et mettre en œuvre [stratégies/politiques/programmes]\n"
                    "• Fournir des conseils d'experts sur [sujet]\n"
                    "• Collaborer avec [intervenants] pour atteindre [résultats]\n"
                    "• Surveiller, évaluer et faire rapport sur [indicateurs de rendement]",
                    "placeholders": [
                        "[domaine de responsabilité spécifique]",
                        "[stratégies/politiques/programmes]",
                        "[sujet]",
                        "[intervenants]",
                        "[résultats]",
                        "[indicateurs de rendement]",
                    ],
                },
                "essential_qualifications": {
                    "title": "Qualifications essentielles",
                    "content": "Études:\n"
                    "• [Niveau de diplôme] en [domaine d'études] ou une combinaison acceptable d'études, de formation et/ou d'expérience\n\n"
                    "Expérience:\n"
                    "• Expérience importante* dans [domaine pertinent]\n"
                    "• Expérience en [compétence ou responsabilité spécifique]\n\n"
                    "*L'expérience importante se définit comme la profondeur et l'étendue de l'expérience normalement associée à [durée].",
                    "placeholders": [
                        "[Niveau de diplôme]",
                        "[domaine d'études]",
                        "[domaine pertinent]",
                        "[compétence ou responsabilité spécifique]",
                        "[durée]",
                    ],
                },
                "asset_qualifications": {
                    "title": "Qualifications constituant un atout",
                    "content": "• Expérience avec [outils/systèmes spécialisés]\n"
                    "• Connaissance de [législation/cadres pertinents]\n"
                    "• Certification professionnelle en [domaine]\n"
                    "• Expérience de travail dans [environnement spécifique]",
                    "placeholders": [
                        "[outils/systèmes spécialisés]",
                        "[législation/cadres pertinents]",
                        "[domaine]",
                        "[environnement spécifique]",
                    ],
                },
                "organizational_context": {
                    "title": "Contexte organisationnel",
                    "content": "Ce poste est situé au sein de [Direction/Division] et relève du [Titre du superviseur]. "
                    "L'organisation est responsable de [mandat] et dessert [clientèle].",
                    "placeholders": [
                        "[Direction/Division]",
                        "[Titre du superviseur]",
                        "[mandat]",
                        "[clientèle]",
                    ],
                },
                "working_conditions": {
                    "title": "Conditions de travail",
                    "content": "• Environnement de bureau standard avec [conditions spécifiques]\n"
                    "• [Exigences de déplacement]\n"
                    "• [Exigences d'heures supplémentaires/sur appel]\n"
                    "• Modalités de travail hybride disponibles",
                    "placeholders": [
                        "[conditions spécifiques]",
                        "[exigences de déplacement]",
                        "[exigences d'heures supplémentaires/sur appel]",
                    ],
                },
                "language_requirements": {
                    "title": "Exigences linguistiques",
                    "content": "Impératif bilingue: [BBB/CBC/CCC]\n"
                    "ou\n"
                    "Anglais ou français essentiel",
                    "placeholders": ["[BBB/CBC/CCC]"],
                },
            },
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "version": "1.0",
                "source": "template_generation_service",
            },
        }

    async def customize_template(
        self,
        template: Dict[str, Any],
        customizations: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Customize a template by replacing placeholders.

        Args:
            template: Base template
            customizations: Dictionary of placeholder -> replacement value

        Returns:
            Customized template
        """
        customized = template.copy()

        for section_id, section_data in customized["sections"].items():
            content = section_data["content"]

            # Replace all placeholders with customizations
            for placeholder, value in customizations.items():
                if placeholder in content:
                    content = content.replace(placeholder, value)
                    logger.info(
                        f"Replaced {placeholder} with {value} in {section_id}"
                    )

            section_data["content"] = content

        customized["metadata"]["customized_at"] = datetime.utcnow().isoformat()
        customized["metadata"]["customizations_applied"] = len(customizations)

        return customized

    async def generate_template_variations(
        self,
        base_template: Dict[str, Any],
        variation_count: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple variations of a template.

        Args:
            base_template: Base template to vary
            variation_count: Number of variations to generate

        Returns:
            List of template variations
        """
        variations = []

        # For now, create simple variations by adjusting tone and structure
        # In production, this would use AI to generate meaningful variations
        tones = ["formal", "conversational", "detailed"]

        for i in range(min(variation_count, len(tones))):
            variation = base_template.copy()
            variation["metadata"]["variation"] = tones[i]
            variation["metadata"]["variation_number"] = i + 1

            # Add tone indicator to each section
            for section_id, section_data in variation["sections"].items():
                section_data["tone"] = tones[i]

            variations.append(variation)

        return variations

    async def extract_placeholders(self, template: Dict[str, Any]) -> List[str]:
        """
        Extract all placeholders from a template.

        Args:
            template: Template to analyze

        Returns:
            List of unique placeholders
        """
        placeholders = set()

        for section_data in template["sections"].values():
            if "placeholders" in section_data:
                placeholders.update(section_data["placeholders"])

        return sorted(list(placeholders))

    async def validate_template(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate template structure and content.

        Args:
            template: Template to validate

        Returns:
            Validation results with errors and warnings
        """
        errors = []
        warnings = []

        # Check required fields
        required_fields = ["classification", "category", "language", "sections"]
        for field in required_fields:
            if field not in template:
                errors.append(f"Missing required field: {field}")

        # Check sections
        if "sections" in template:
            for section_id in self.STANDARD_SECTIONS:
                if section_id not in template["sections"]:
                    warnings.append(f"Missing standard section: {section_id}")

            for section_id, section_data in template["sections"].items():
                if "title" not in section_data:
                    errors.append(f"Section {section_id} missing title")
                if "content" not in section_data:
                    errors.append(f"Section {section_id} missing content")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "sections_count": len(template.get("sections", {})),
        }

    def get_available_classifications(self) -> List[Dict[str, str]]:
        """Get list of available classifications."""
        return [
            {"code": code, "name": name}
            for code, name in self.TEMPLATE_CATEGORIES.items()
        ]

    async def get_bilingual_template(
        self, classification: str, level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get both English and French versions of a template.

        Args:
            classification: Job classification
            level: Classification level

        Returns:
            Dictionary with both language versions
        """
        en_template = await self.get_template_by_classification(
            classification, "en", level
        )
        fr_template = await self.get_template_by_classification(
            classification, "fr", level
        )

        return {
            "classification": f"{classification}{'-' + level if level else ''}",
            "languages": {
                "en": en_template,
                "fr": fr_template,
            },
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "bilingual": True,
            },
        }