import pytest
import os
import django
from django.conf import settings
from django.test.utils import get_runner


def pytest_configure():
    """Configure Django settings for pytest."""
    if not settings.configured:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
        django.setup()


@pytest.fixture(scope="session")
def django_db_setup():
    """Setup test database configuration."""
    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "ATOMIC_REQUESTS": False,
        "OPTIONS": {
            "timeout": 20,
        },
    }


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Grant database access to all tests.
    This fixture automatically applies to all tests.
    """
    pass


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response for testing."""
    return {
        "optimized_content": "This is a mock optimized content with better SEO.",
        "improvements_done": [
            "Improved keyword density",
            "Enhanced readability",
            "Better structure",
        ],
    }


@pytest.fixture
def mock_seo_analysis():
    """Mock SEO analysis results for testing."""
    return {
        "input_type": "content",
        "word_count": 100,
        "keyword_density": 2.5,
        "headings": {},
        "has_meta_description": None,
        "readability_score": 75.0,
        "avg_sentence_length": 15.0,
        "seo_score": 85,
        "issues": {
            "keyword_density_low": {
                "severity": "medium",
                "message": "Keyword density is too low.",
            }
        },
    }
