import re
from typing import Dict, Any
from dataclasses import dataclass, field


@dataclass
class StructuredFields:
    position_title: str = ""
    job_number: str = ""
    classification: str = ""
    department: str = ""
    reports_to: str = ""
    location: str = ""
    fte_count: int = None
    salary_budget: float = None
    effective_date: str = ""


@dataclass
class ProcessedContent:
    cleaned_content: str = ""
    sections: Dict[str, str] = field(default_factory=dict)
    structured_fields: StructuredFields = field(default_factory=StructuredFields)
    processing_errors: list = field(default_factory=list)


class ContentProcessor:
    def __init__(self, raw_content: str = "", language: str = "en"):
        self.raw_content = raw_content
        self.language = language

    def extract_sections(self) -> Dict[str, str]:
        sections = {}
        section_headers = [
            "GENERAL ACCOUNTABILITY",
            "ORGANIZATIONAL STRUCTURE",
            "ORGANIZATION STRUCTURE",  # Alternative spelling
            "NATURE & SCOPE",
            "SPECIFIC ACCOUNTABILITIES",
            "DIMENSIONS",
            "EDUCATION",
            "EXPERIENCE",
            "KNOWLEDGE",
            "ABILITIES",
            "PERSONAL SUITABILITY",
            "OFFICIAL LANGUAGE PROFICIENCY",
            "CONDITIONS OF EMPLOYMENT",
            "POSITION SUMMARY",
            "KEY RESPONSIBILITIES",
            "QUALIFICATIONS",
        ]

        # Use the actual raw content
        processed_content = self.raw_content or ""

        # Step 1: Find all header matches and their positions
        header_matches = []
        header_regex = re.compile(
            r"(?:\n|^|\s)(?P<header>"
            + "|".join(re.escape(h) for h in section_headers)
            + r"):?\s*",  # Match headers with optional colon and whitespace, including after spaces
            re.IGNORECASE,  # Removed MULTILINE as it's handled by (?:\\n|^)
        )
        for match in header_regex.finditer(processed_content):
            header_matches.append(
                {
                    "header": match.group("header").strip(),
                    "start": match.start(),
                    "end": match.end(),
                }
            )

        # Step 2: Extract content between headers
        for i, current_header_info in enumerate(header_matches):
            header_text = current_header_info["header"]
            content_start = current_header_info["end"]

            if i + 1 < len(header_matches):
                # Content ends at the start of the next header
                content_end = header_matches[i + 1]["start"]
            else:
                # Last header, content goes to the end of the document
                content_end = len(processed_content)

            content = processed_content[content_start:content_end].strip()
            sections[header_text] = content

        return sections

    def clean_text(self, text: str) -> str:
        """
        Cleans the input text by removing common formatting artifacts,
        extra whitespace, and normalizing content.
        """
        # Remove multiple spaces/tabs with a single space
        text = re.sub(r"\s+", " ", text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text

    def identify_language(self) -> str:
        """
        Identifies the language of the raw content.
        For now, it returns the language passed in the constructor,
        but can be enhanced with a language detection library (e.g., langdetect).
        """
        return self.language

    def parse_structured_fields(self) -> Dict[str, Any]:
        """
        Parses structured fields from the raw content, such as position title,
        reporting structure, department, etc.
        This will require specific regex patterns for each field.
        """
        structured_fields = {
            "position_title": None,
            "reports_to": None,
            "department": None,
            "location": None,
            "fte_count": None,
            "salary_budget": None,
            "effective_date": None,
        }

        # Extract Position Title - multiple patterns
        patterns = [
            r"POSITION\s+TITLE[:\.\s]*(.+?)(?:\n|$)",
            r"TITLE[:\.\s]*(.+?)(?:\n|$)",
            r"ector,\s*(.+?)(?:\s+GROUP|$)",  # From sample: "ector, Bilateral and Regional Labour Affairs"
        ]
        for pattern in patterns:
            match = re.search(pattern, self.raw_content, re.IGNORECASE)
            if match:
                structured_fields["position_title"] = self.clean_text(match.group(1))
                break

        # Extract Reports To
        match = re.search(
            r"Reports\s+to:\s*(.+?)(?:\n|$)", self.raw_content, re.IGNORECASE
        )
        if match:
            structured_fields["reports_to"] = self.clean_text(match.group(1))

        # Extract Department
        match = re.search(
            r"Department:\s*(.+?)(?:\n|$)", self.raw_content, re.IGNORECASE
        )
        if match:
            structured_fields["department"] = self.clean_text(match.group(1))

        # Extract Staff Supervised (FTE count) - multiple patterns
        patterns = [
            r"Staff\s+Supervised:\s*(\d+)",
            r"Supervises:\s*(\d+)\s*FTE",
            r"Direct\s+Reports:\s*(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, self.raw_content, re.IGNORECASE)
            if match:
                try:
                    structured_fields["fte_count"] = int(match.group(1))
                    break
                except ValueError:
                    continue

        # Extract Budget Responsibility - multiple patterns
        patterns = [
            r"Budget\s+Responsibility:\s*\$?([\d,\.]+)(?:\s*[MK])?",
            r"Budget\s+Authority:\s*\$?([\d,\.]+)(?:\s*[MK])?",
        ]
        for pattern in patterns:
            match = re.search(pattern, self.raw_content, re.IGNORECASE)
            if match:
                try:
                    # Remove commas and convert to float
                    budget_str = match.group(1).replace(",", "")
                    budget_value = float(budget_str)

                    # Check if it's in millions (M) or thousands (K)
                    if re.search(r"Budget\s+(?:Responsibility|Authority):\s*\$?[\d,\.]+\s*M", self.raw_content, re.IGNORECASE):
                        budget_value = budget_value * 1_000_000
                    elif re.search(r"Budget\s+(?:Responsibility|Authority):\s*\$?[\d,\.]+\s*K", self.raw_content, re.IGNORECASE):
                        budget_value = budget_value * 1_000

                    structured_fields["salary_budget"] = budget_value
                    break
                except ValueError:
                    continue


        return structured_fields

    def process_content(
        self, raw_content: str, language: str = "en"
    ) -> ProcessedContent:
        """
        Main processing method that orchestrates all content processing tasks.

        Args:
            raw_content: The raw content to process
            language: Language code (default: "en")

        Returns:
            ProcessedContent object with all processed data
        """
        self.raw_content = raw_content
        self.language = language

        try:
            # Clean the content
            cleaned_content = self.clean_text(raw_content)

            # Extract sections
            sections = self.extract_sections()

            # Parse structured fields
            structured_fields_dict = self.parse_structured_fields()
            structured_fields = StructuredFields(**structured_fields_dict)

            return ProcessedContent(
                cleaned_content=cleaned_content,
                sections=sections,
                structured_fields=structured_fields,
                processing_errors=[],
            )

        except Exception as e:
            return ProcessedContent(
                cleaned_content=raw_content,
                sections={},
                structured_fields=StructuredFields(),
                processing_errors=[str(e)],
            )

    def chunk_content(
        self, content: str, chunk_size: int = 500, overlap: int = 50
    ) -> list:
        """
        Split content into overlapping chunks for embedding generation.

        Args:
            content: The content to chunk
            chunk_size: Target size for each chunk in characters
            overlap: Number of characters to overlap between chunks

        Returns:
            List of content chunks
        """
        if not content or len(content) <= chunk_size:
            return [content] if content else []

        chunks = []
        start = 0

        while start < len(content):
            end = start + chunk_size

            # If we're not at the end, try to break at a sentence boundary
            if end < len(content):
                # Look for sentence endings within the last 100 characters
                last_sentence_end = content.rfind(".", end - 100, end)
                if last_sentence_end > start:
                    end = last_sentence_end + 1

            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position (with overlap)
            # Ensure we always make progress to prevent infinite loops
            next_start = max(start + 1, end - overlap)
            start = next_start

        return chunks
