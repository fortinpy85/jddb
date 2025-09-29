import re
import hashlib
import chardet
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class FileMetadata:
    """Metadata extracted from job description files."""

    file_path: Path
    job_number: Optional[str] = None
    classification: Optional[str] = None
    language: Optional[str] = None
    title: Optional[str] = None
    file_size: int = 0
    file_hash: str = ""
    encoding: str = "utf-8"
    last_modified: Optional[datetime] = None
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)


class FileDiscovery:
    """Discovers and analyzes job description files."""

    # Pattern to extract job info from filename
    # Primary pattern: "EX-01 Dir, Business Analysis 103249 - JD.txt"
    # Alternative patterns: "JD_EX-01_123456_Director.txt", "DE_EX-02_789012_Directeur.txt"
    FILENAME_PATTERNS = [
        # New pattern: "EX-01 Dir, Business Analysis 103249 - JD.txt"
        re.compile(
            r"(?P<classification>EX-\d{2})\s+(?P<title>[^0-9]+?)\s+(?P<job_number>\d+)\s*-\s*(?P<lang_code>JD|DE)\.(?P<extension>\w+)$",
            re.IGNORECASE,
        ),
        # Pattern for SJD files with language code: "EX-01 SJD Director, Special Projects EN.docx"
        re.compile(
            r"(?P<classification>EX-\d{2})\s+(?P<title>.+?)\s+(?P<lang_code>EN|FR)\.(?P<extension>\w+)$",
            re.IGNORECASE,
        ),
        # Legacy pattern: "JD_EX-01_123456_Director.txt"
        re.compile(
            r"(?P<lang_code>JD|DE)_(?P<classification>EX-\d{2})_(?P<job_number>\d+)_?(?P<title>.*)?\.(?P<extension>\w+)$",
            re.IGNORECASE,
        ),
        # Flexible pattern for variations: "Director Business Analysis EX-01 103249.txt"
        re.compile(
            r"(?P<title>.+?)\s+(?P<classification>EX-\d{2})\s+(?P<job_number>\d+)(?:\s*-\s*(?P<lang_code>JD|DE))?\.(?P<extension>\w+)$",
            re.IGNORECASE,
        ),
    ]

    # Language code mapping
    LANGUAGE_MAPPING = {
        "JD": "en",  # Job Description (English)
        "DE": "fr",  # Description d'Emploi (French)
        "EN": "en",  # English
        "FR": "fr",  # French
    }

    # Supported file extensions
    SUPPORTED_EXTENSIONS = {".txt", ".doc", ".docx", ".pdf"}

    def __init__(self, data_directory: Path):
        """Initialize file discovery with data directory."""
        self.data_directory = Path(data_directory)
        logger.info("Initialized FileDiscovery", data_dir=str(self.data_directory))

    def scan_directory(self, recursive: bool = True) -> List[FileMetadata]:
        """Scan directory for job description files."""
        logger.info("Starting directory scan", recursive=recursive)

        if not self.data_directory.exists():
            logger.error("Data directory does not exist", path=str(self.data_directory))
            return []

        files_metadata = []

        # Use glob pattern to find files
        pattern = "**/*" if recursive else "*"

        for file_path in self.data_directory.glob(pattern):
            if (
                file_path.is_file()
                and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS
            ):
                try:
                    metadata = self._extract_file_metadata(file_path)
                    files_metadata.append(metadata)
                except Exception as e:
                    logger.error(
                        "Error processing file", file=str(file_path), error=str(e)
                    )
                    # Still add the file but mark as invalid
                    metadata = FileMetadata(
                        file_path=file_path,
                        is_valid=False,
                        validation_errors=[f"Processing error: {str(e)}"],
                    )
                    files_metadata.append(metadata)

        logger.info(
            "Directory scan completed",
            total_files=len(files_metadata),
            valid_files=sum(1 for f in files_metadata if f.is_valid),
        )

        return files_metadata

    def _extract_file_metadata(self, file_path: Path) -> FileMetadata:
        """Extract metadata from a single file."""
        metadata = FileMetadata(file_path=file_path)

        # Get basic file info
        stats = file_path.stat()
        metadata.file_size = stats.st_size
        metadata.last_modified = datetime.fromtimestamp(stats.st_mtime)

        # Calculate file hash
        metadata.file_hash = self._calculate_file_hash(file_path)

        # Extract metadata from filename
        self._extract_metadata_from_filename(file_path.name, metadata)

        # Detect file encoding
        metadata.encoding = self._detect_encoding(file_path)

        # Validate file
        self._validate_file(metadata)

        return metadata

    def _extract_metadata_from_filename(
        self, filename: str, metadata: FileMetadata
    ) -> None:
        """Extract job metadata from filename using regex patterns."""
        match_found = False

        for pattern in self.FILENAME_PATTERNS:
            match = pattern.match(filename)
            if match:
                groups = match.groupdict()
                metadata.classification = groups.get("classification")
                metadata.job_number = groups.get("job_number")

                # Handle language code - default to English if not specified
                lang_code = (
                    groups.get("lang_code", "").upper()
                    if groups.get("lang_code")
                    else "JD"
                )
                metadata.language = self.LANGUAGE_MAPPING.get(lang_code, "en")

                # Clean up title - handle commas, underscores, and extra spaces
                title = groups.get("title", "") if groups.get("title") else None
                if title:
                    title = title.replace("_", " ").replace(",", "").strip()
                    # Remove extra whitespace
                    title = " ".join(title.split())
                metadata.title = title

                match_found = True
                logger.debug(
                    "Extracted metadata from filename",
                    filename=filename,
                    pattern_used=pattern.pattern,
                    classification=metadata.classification,
                    job_number=metadata.job_number,
                    language=metadata.language,
                    title=metadata.title,
                )
                break

        if not match_found:
            # Try to extract at least the classification and job number with a more lenient approach
            classification_match = re.search(r"(EX-\d{2})", filename, re.IGNORECASE)
            job_number_match = re.search(r"(\d{6})", filename)
            language_match = re.search(r"\b(EN|FR|JD|DE)\b", filename, re.IGNORECASE)

            if classification_match:
                metadata.classification = classification_match.group(1).upper()

            if job_number_match:
                metadata.job_number = job_number_match.group(1)
            else:
                # Generate a temporary job number based on file hash (first 6 chars)
                import hashlib

                file_hash = hashlib.md5(filename.encode()).hexdigest()[:6].upper()
                metadata.job_number = file_hash
                metadata.validation_errors.append(
                    f"Generated job number from filename hash: {file_hash}"
                )

            # Extract language from filename
            if language_match:
                lang_code = language_match.group(1).upper()
                metadata.language = self.LANGUAGE_MAPPING.get(lang_code, "en")
            else:
                metadata.language = "en"

            # Try to extract title from filename
            if metadata.classification:
                # Remove classification and language codes to get title
                title_pattern = (
                    filename.replace(metadata.classification, "")
                    .replace(".docx", "")
                    .replace(".txt", "")
                    .replace(".doc", "")
                    .replace(".pdf", "")
                )
                if language_match:
                    title_pattern = title_pattern.replace(language_match.group(1), "")
                # Clean up the title
                title = title_pattern.strip(" -.,_")
                title = " ".join(title.split())  # Remove extra whitespace
                if title:
                    metadata.title = title

            metadata.validation_errors.append(
                f"Filename doesn't match expected patterns but extracted basic info: {filename}"
            )
            logger.warning(
                "Filename pattern not recognized, extracted basic info",
                filename=filename,
                classification=metadata.classification,
                job_number=metadata.job_number,
            )

    def _detect_encoding(self, file_path: Path) -> str:
        """Detect file encoding for proper text processing."""
        # Skip encoding detection for binary file formats
        if file_path.suffix.lower() in {".docx", ".doc", ".pdf"}:
            logger.debug(
                "Skipping encoding detection for binary file",
                file=str(file_path),
                extension=file_path.suffix.lower(),
            )
            return "utf-8"  # Not used for binary files, but return default

        try:
            with open(file_path, "rb") as f:
                # Read first chunk to detect encoding
                raw_data = f.read(10000)  # Read first 10KB

            if raw_data:
                result = chardet.detect(raw_data)
                encoding = result.get("encoding", "utf-8")
                confidence = result.get("confidence", 0)

                if confidence < 0.7:
                    logger.warning(
                        "Low confidence encoding detection",
                        file=str(file_path),
                        encoding=encoding,
                        confidence=confidence,
                    )

                return encoding or "utf-8"
            else:
                return "utf-8"

        except Exception as e:
            logger.warning(
                "Encoding detection failed", file=str(file_path), error=str(e)
            )
            return "utf-8"

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file for change detection."""
        sha256_hash = hashlib.sha256()

        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error("Hash calculation failed", file=str(file_path), error=str(e))
            return ""

    def _validate_file(self, metadata: FileMetadata) -> None:
        """Validate file and metadata quality."""
        # Check file size
        if metadata.file_size == 0:
            metadata.validation_errors.append("File is empty")
            metadata.is_valid = False
        elif metadata.file_size > 100 * 1024 * 1024:  # 100MB limit
            metadata.validation_errors.append("File too large (>100MB)")
            metadata.is_valid = False

        # Check if required metadata is present
        if not metadata.job_number:
            metadata.validation_errors.append("Job number not found in filename")

        if not metadata.classification:
            metadata.validation_errors.append("Classification not found in filename")

        if not metadata.language:
            metadata.validation_errors.append("Language not detected from filename")

        # Check file extension
        if metadata.file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            metadata.validation_errors.append(
                f"Unsupported file extension: {metadata.file_path.suffix}"
            )
            metadata.is_valid = False

        # Only mark as invalid for critical errors (file size, unsupported extension)
        # Allow files with minor validation issues (missing job number, pattern mismatch) to be processed
        critical_errors = [
            error
            for error in metadata.validation_errors
            if "File is empty" in error
            or "File too large" in error
            or "Unsupported file extension" in error
        ]
        if critical_errors:
            metadata.is_valid = False
        else:
            # File can be processed even with warnings about filename patterns
            metadata.is_valid = True

        logger.debug(
            "File validation completed",
            file=str(metadata.file_path),
            is_valid=metadata.is_valid,
            errors=metadata.validation_errors,
        )

    def get_stats(self, files_metadata: List[FileMetadata]) -> Dict[str, Any]:
        """Generate statistics about discovered files."""
        stats: Dict[str, Any] = {
            "total_files": len(files_metadata),
            "valid_files": sum(1 for f in files_metadata if f.is_valid),
            "invalid_files": sum(1 for f in files_metadata if not f.is_valid),
            "by_classification": {},
            "by_language": {},
            "by_extension": {},
            "total_size_mb": sum(f.file_size for f in files_metadata) / (1024 * 1024),
            "avg_size_kb": (
                sum(f.file_size for f in files_metadata) / len(files_metadata) / 1024
                if files_metadata
                else 0
            ),
        }

        for metadata in files_metadata:
            # Count by classification
            classification = metadata.classification or "unknown"
            stats["by_classification"][classification] = (
                stats["by_classification"].get(classification, 0) + 1
            )

            # Count by language
            language = metadata.language or "unknown"
            stats["by_language"][language] = stats["by_language"].get(language, 0) + 1

            # Count by extension
            extension = metadata.file_path.suffix.lower()
            stats["by_extension"][extension] = (
                stats["by_extension"].get(extension, 0) + 1
            )

        return stats
