"""Shared pytest fixtures."""

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_profile_html() -> str:
    """Load the sample russprofile.ru company profile HTML."""
    return (FIXTURES_DIR / "sample_profile.html").read_text(encoding="utf-8")


@pytest.fixture
def sample_search_html() -> str:
    """Load the sample russprofile.ru search results HTML."""
    return (FIXTURES_DIR / "sample_search.html").read_text(encoding="utf-8")
