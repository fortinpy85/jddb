import pytest
from pathlib import Path
import tempfile
from jd_ingestion.core.file_discovery import FileDiscovery


@pytest.fixture
def temp_dir_with_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir)
        (dir_path / "EX-01 Dir, Business Analysis 103249 - JD.txt").write_text(
            "test content", encoding="utf-8"
        )
        (dir_path / "JD_EX-01_123456_Director.txt").write_text(
            "test content", encoding="utf-8"
        )
        (dir_path / "Director Business Analysis EX-01 103249.txt").write_text(
            "test content", encoding="utf-8"
        )
        (dir_path / "unsupported.zip").write_text("test content", encoding="utf-8")
        (dir_path / "empty.txt").write_text("", encoding="utf-8")

        subdir = dir_path / "subdir"
        subdir.mkdir()
        (subdir / "EX-02 Manager, IT 203457 - DE.txt").write_text(
            "french content", encoding="latin-1"
        )

        yield dir_path


def test_scan_directory_recursive(temp_dir_with_files):
    discovery = FileDiscovery(data_directory=temp_dir_with_files)
    results = discovery.scan_directory(recursive=True)

    assert len(results) == 5

    filenames = {r.file_path.name for r in results}
    assert "EX-01 Dir, Business Analysis 103249 - JD.txt" in filenames
    assert "JD_EX-01_123456_Director.txt" in filenames
    assert "Director Business Analysis EX-01 103249.txt" in filenames
    assert "empty.txt" in filenames
    assert "EX-02 Manager, IT 203457 - DE.txt" in filenames

    # Check metadata for one file
    metadata = next(
        r for r in results if r.file_path.name == "EX-02 Manager, IT 203457 - DE.txt"
    )
    assert metadata.classification == "EX-02"
    assert metadata.job_number == "203457"
    assert metadata.language == "fr"
    assert metadata.title == "Manager IT"
    assert metadata.encoding == "latin-1"


def test_scan_directory_non_recursive(temp_dir_with_files):
    discovery = FileDiscovery(data_directory=temp_dir_with_files)
    results = discovery.scan_directory(recursive=False)

    assert len(results) == 4

    filenames = {r.file_path.name for r in results}
    assert "EX-01 Dir, Business Analysis 103249 - JD.txt" in filenames
    assert "JD_EX-01_123456_Director.txt" in filenames
    assert "Director Business Analysis EX-01 103249.txt" in filenames
    assert "empty.txt" in filenames
    assert "EX-02 Manager, IT 203457 - DE.txt" not in filenames


def test_get_stats(temp_dir_with_files):
    discovery = FileDiscovery(data_directory=temp_dir_with_files)
    results = discovery.scan_directory(recursive=True)
    stats = discovery.get_stats(results)

    assert stats["total_files"] == 5
    assert stats["valid_files"] == 4  # empty.txt is invalid
    assert stats["invalid_files"] == 1
    assert stats["by_classification"] == {"EX-01": 3, "EX-02": 1, "unknown": 1}
    assert stats["by_language"] == {"en": 4, "fr": 1}
    assert stats["by_extension"] == {".txt": 5}
