import pytest
import os
from app import app as flask_app


@pytest.fixture
def app():
    """Create Flask app for testing."""
    # Set test configuration
    flask_app.config.update({
        "TESTING": True,
    })
    
    # Set test API key if not already set
    if not os.getenv("FINNHUB_API_KEY"):
        os.environ["FINNHUB_API_KEY"] = "test_api_key"
    
    yield flask_app
    
    # Cleanup
    if os.getenv("FINNHUB_API_KEY") == "test_api_key":
        del os.environ["FINNHUB_API_KEY"]


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def sample_quote_response():
    """Sample Finnhub quote response."""
    return {
        "c": 150.25,      # current price
        "h": 151.00,      # high
        "l": 149.50,      # low
        "o": 150.00,      # open
        "pc": 149.80,     # previous close
        "t": 1706889600   # timestamp
    }


@pytest.fixture
def sample_news_response():
    """Sample Finnhub news response."""
    return [
        {
            "category": "company news",
            "datetime": 1706889600,
            "headline": "Apple announces new product line",
            "id": 123456,
            "image": "https://example.com/image.jpg",
            "related": "AAPL",
            "source": "Reuters",
            "summary": "Apple Inc. announced a new product line...",
            "url": "https://example.com/article"
        },
        {
            "category": "company news",
            "datetime": 1706803200,
            "headline": "Apple reports quarterly earnings",
            "id": 123457,
            "image": "https://example.com/image2.jpg",
            "related": "AAPL",
            "source": "Bloomberg",
            "summary": "Apple reported strong quarterly earnings...",
            "url": "https://example.com/article2"
        }
    ]


@pytest.fixture
def empty_quote_response():
    """Empty quote response (invalid ticker)."""
    return {
        "c": 0,
        "h": 0,
        "l": 0,
        "o": 0,
        "pc": 0,
        "t": 0
    }


@pytest.fixture
def empty_news_response():
    """Empty news response."""
    return []
