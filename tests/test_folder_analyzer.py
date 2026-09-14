"""Tests for folder_analyzer.py — behaviour contracts, not snapshots."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Import the module under test (project root on path)
sys.path.insert(0, str(Path(__file__).parent.parent))
import folder_analyzer as fa


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_listing(tmp_path: Path) -> Path:
    """A small synthetic listing covering all the main categories.

    Includes:
      - .git (known hidden dir)  -> dir/dir
      - .gitignore (dot config file) -> file/config
      - .env (dot config file) -> file/config
      - .hidden_file (unknown dotfile) -> file/hidden
      - .hidden_dir (unknown dotdir, no trailing sep — treated as file/hidden
        because we can't know it's a dir without the separator or a known set entry)
      - src/main.py -> file/code
      - config/settings.yaml -> file/config
      - docs/README.md -> file/doc
      - data/users.csv -> file/data
      - images/logo.png -> file/image
      - archive/backup.zip -> file/archive
      - normal_file.xyz -> file/other
    """
    content = """
C:\\project\\.git
C:\\project\\.gitignore
C:\\project\\.env
C:\\project\\.hidden_file
C:\\project\\.hidden_dir
C:\\project\\src\\main.py
C:\\project\\src\\utils.py
C:\\project\\src\\__init__.py
C:\\project\\config\\settings.yaml
C:\\project\\data\\users.csv
C:\\project\\docs\\README.md
C:\\project\\images\\logo.png
C:\\project\\archive\\backup.zip
C:\\project\\normal_file.xyz
C:\\project\\deep\\nested\\path\\file.py
"""
    p = tmp_path / "listing.txt"
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# Unit tests — _classify
# ---------------------------------------------------------------------------

class TestClassify:
    """Contract tests: each input produces the expected (type, category, name)."""

    def test_git_dir_is_dir(self):
        typ, cat, name = fa._classify("C:\\project\\.git")
        assert typ == "dir"
        assert cat == "dir"
        assert name == ".git"

    def test_gitignore_is_config(self):
        typ, cat, name = fa._classify("C:\\project\\.gitignore")
        assert typ == "file"
        assert cat == "config"
        assert name == ".gitignore"

    def test_env_is_config(self):
        typ, cat, name = fa._classify("C:\\project\\.env")
        assert typ == "file"
        assert cat == "config"
        assert name == ".env"

    def test_hidden_file_falls_to_hidden(self):
        typ, cat, name = fa._classify("C:\\project\\.hidden_file")
        assert typ == "file"
        assert cat == "hidden"
        assert name == ".hidden_file"

    def test_unknown_dotdir_falls_to_hidden(self):
        # .hidden_dir is not in _KNOWN_HIDDEN_DIRS and has no trailing sep,
        # so we cannot confirm it is a directory — classify as file/hidden.
        typ, cat, name = fa._classify("C:\\project\\.hidden_dir")
        assert typ == "file"
        assert cat == "hidden"
        assert name == ".hidden_dir"

    def test_python_file_is_code(self):
        typ, cat, name = fa._classify("C:\\project\\main.py")
        assert typ == "file"
        assert cat == "code"
        assert name == "main.py"

    def test_yaml_is_config(self):
        typ, cat, name = fa._classify("C:\\project\\settings.yaml")
        assert typ == "file"
        assert cat == "config"
        assert name == "settings.yaml"

    def test_md_is_doc(self):
        typ, cat, name = fa._classify("C:\\project\\README.md")
        assert typ == "file"
        assert cat == "doc"
        assert name == "README.md"

    def test_csv_is_data(self):
        typ, cat, name = fa._classify("C:\\project\\users.csv")
        assert typ == "file"
        assert cat == "data"
        assert name == "users.csv"

    def test_png_is_image(self):
        typ, cat, name = fa._classify("C:\\project\\logo.png")
        assert typ == "file"
        assert cat == "image"
        assert name == "logo.png"

    def test_zip_is_archive(self):
        typ, cat, name = fa._classify("C:\\project\\backup.zip")
        assert typ == "file"
        assert cat == "archive"
        assert name == "backup.zip"

    def test_xyz_is_other(self):
        typ, cat, name = fa._classify("C:\\project\\normal_file.xyz")
        assert typ == "file"
        assert cat == "other"
        assert name == "normal_file.xyz"

    def test_empty_line_is_unknown(self):
        typ, cat, name = fa._classify("")
        assert typ == "unknown"
        assert cat == "other"
        assert name == ""


# ---------------------------------------------------------------------------
# Integration tests — analyze_listing on the fixture
# ---------------------------------------------------------------------------

class TestAnalyzeListing:
    """End-to-end checks on the synthetic fixture."""

    def test_counts_nonzero(self, sample_listing):
        results = fa.analyze_listing(str(sample_listing))
        assert results["total_lines"] > 0
        assert results["total_dirs"] > 0
        assert results["total_files"] > 0

    def test_code_category_has_python_files(self, sample_listing):
        results = fa.analyze_listing(str(sample_listing))
        assert results["categories"]["code"] >= 4  # main.py, utils.py, __init__.py, file.py

    def test_config_category_has_dot_config_files(self, sample_listing):
        results = fa.analyze_listing(str(sample_listing))
        # .gitignore, .env, settings.yaml = 3 config entries
        assert results["categories"]["config"] >= 3

    def test_hidden_category_has_unknown_dotfiles(self, sample_listing):
        results = fa.analyze_listing(str(sample_listing))
        # .hidden_file and .hidden_dir both land in "hidden"
        assert results["categories"]["hidden"] >= 2

    def test_doc_category_has_markdown(self, sample_listing):
        results = fa.analyze_listing(str(sample_listing))
        assert results["categories"]["doc"] >= 1

    def test_image_category_has_png(self, sample_listing):
        results = fa.analyze_listing(str(sample_listing))
        assert results["categories"]["image"] >= 1

    def test_archive_category_has_zip(self, sample_listing):
        results = fa.analyze_listing(str(sample_listing))
        assert results["categories"]["archive"] >= 1

    def test_other_category_exists(self, sample_listing):
        results = fa.analyze_listing(str(sample_listing))
        assert results["categories"]["other"] >= 1

    def test_hidden_dirs_only_known_dirs(self, sample_listing):
        results = fa.analyze_listing(str(sample_listing))
        # Only .git is a known hidden dir; .hidden_dir is unknown and thus file/hidden
        assert ".git" in results["hidden_dirs"]
        assert ".hidden_dir" not in results["hidden_dirs"]

    def test_hidden_files_includes_unknown_dotfiles(self, sample_listing):
        results = fa.analyze_listing(str(sample_listing))
        assert ".hidden_file" in results["hidden_files"]

    def test_json_stderr_output(self, sample_listing, capsys):
        """main() should emit parseable JSON on stderr."""
        try:
            fa.main()
        except SystemExit:
            pass
        captured = capsys.readouterr()
        stderr = captured.err
        marker = "--- JSON (stderr) ---"
        assert marker in stderr
        payload = stderr.split(marker, 1)[1].strip()
        data = json.loads(payload)
        assert isinstance(data, dict)
        assert "total_lines" in data
        assert data["total_lines"] > 0


# ---------------------------------------------------------------------------
# CLI contract tests
# ---------------------------------------------------------------------------

class TestCLI:
    """Behaviour of the script when invoked as a subprocess."""

    @pytest.fixture(scope="module")
    def script_path(self) -> Path:
        return Path(__file__).parent.parent / "folder_analyzer.py"

    def test_no_args_exits_1(self, script_path):
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True, text=True,
        )
        assert proc.returncode == 1
        assert "Usage" in proc.stderr

    def test_nonexistent_file_exits_1(self, script_path, tmp_path):
        proc = subprocess.run(
            [sys.executable, str(script_path), str(tmp_path / "nope.txt")],
            capture_output=True, text=True,
        )
        assert proc.returncode == 1
        assert "not found" in proc.stderr.lower() or "Error" in proc.stderr


# ---------------------------------------------------------------------------
# Real-data smoke tests
# ---------------------------------------------------------------------------

_REAL_LISTING = Path(__file__).parent.parent / "screenshot" / "folder_listing.txt"
_REAL_LISTING_PRESENT = _REAL_LISTING.exists()


@pytest.fixture(scope="session")
def real_listing_path() -> str | None:
    if _REAL_LISTING_PRESENT:
        return str(_REAL_LISTING)
    return None


@pytest.mark.skipif(not _REAL_LISTING_PRESENT, reason="folder_listing.txt not present")
class TestRealDataSmoke:
    """Lightweight smoke tests against the real 123K-line listing.

    These assert relationships, not frozen values — safe to keep across updates.
    """

    def test_real_listing_is_large(self, real_listing_path):
        results = fa.analyze_listing(real_listing_path)
        assert results["total_lines"] > 1000

    def test_real_listing_has_code(self, real_listing_path):
        results = fa.analyze_listing(real_listing_path)
        assert results["categories"]["code"] > 100

    def test_category_sum_matches_total(self, real_listing_path):
        results = fa.analyze_listing(real_listing_path)
        total = sum(results["categories"].values())
        assert total == results["total_lines"], (
            f"category sum {total} != total lines {results['total_lines']}"
        )

    def test_real_json_output(self, real_listing_path, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["folder_analyzer.py", real_listing_path])
        try:
            fa.main()
        except SystemExit:
            pass
        captured = capsys.readouterr()
        stderr = captured.err
        marker = "--- JSON (stderr) ---"
        assert marker in stderr
        data = json.loads(stderr.split(marker, 1)[1].strip())
        assert data["total_lines"] > 1000
