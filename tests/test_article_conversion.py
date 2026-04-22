"""Snapshot tests for the article HTML conversion pipeline.

Three tests, showing how different extraction methods handle the same page:

  test_meteor_shower_trafilatura  – default extraction
  test_meteor_shower_readability  – explicit readability
  test_meteor_shower_css_selector – explicit CSS selector

Snapshots are plain .html files in tests/snapshots/ – open them in a browser
to inspect the output visually.

Run with:
    uv run pytest tests/ --update-snapshots   # write / refresh snapshots
    uv run pytest tests/                      # verify against stored snapshots
"""

import sys
from pathlib import Path

import pytest

# Make src/ importable without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import extract_content_from_html  # noqa: E402

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def meteor_shower_html() -> str:
    """Raw HTML of the fictitious Perennids meteor shower blog post."""
    return (FIXTURES_DIR / "perennids_meteor_shower.html").read_text(encoding="utf-8")


def test_meteor_shower_trafilatura(html_snapshot, meteor_shower_html):
    """Default extraction via trafilatura"""
    result = extract_content_from_html(meteor_shower_html)
    html_snapshot(result)


def test_meteor_shower_readability(html_snapshot, meteor_shower_html):
    """Explicit readability extraction"""
    config = {"method": "readability"}
    result = extract_content_from_html(meteor_shower_html, config=config)
    html_snapshot(result)


def test_meteor_shower_css_selector(html_snapshot, meteor_shower_html):
    """Explicit CSS selector extraction via .post"""
    config = {"method": "selector", "selectors": {"content": ".post"}}
    result = extract_content_from_html(meteor_shower_html, config=config)
    html_snapshot(result)
