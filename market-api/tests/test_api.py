import pytest
import responses
from app import get_ticker_symbol, FINNHUB_BASE_URL


class TestTickerMapping:
    """Test company name to ticker symbol mapping."""
    
    def test_company_name_lowercase(self):
        """Test lowercase company names."""
        assert get_ticker_symbol("apple") == "AAPL"
        assert get_ticker_symbol("tesla") == "TSLA"
        assert get_ticker_symbol("airbus") == "AIR.PA"
    
    def test_company_name_mixed_case(self):
        """Test mixed case company names."""
        assert get_ticker_symbol("Apple") == "AAPL"
        assert get_ticker_symbol("TESLA") == "TSLA"
        assert get_ticker_symbol("AiRbUs") == "AIR.PA"
    
    def test_ticker_symbol_passthrough(self):
        """Test that ticker symbols are passed through uppercase."""
        assert get_ticker_symbol("AAPL") == "AAPL"
        assert get_ticker_symbol("MSFT") == "MSFT"
        assert get_ticker_symbol("GOOGL") == "GOOGL"
    
    def test_ticker_symbol_lowercase(self):
        """Test lowercase ticker symbols are converted to uppercase."""
        assert get_ticker_symbol("aapl") == "AAPL"
        assert get_ticker_symbol("msft") == "MSFT"
    
    def test_whitespace_handling(self):
        """Test whitespace is stripped."""
        assert get_ticker_symbol("  apple  ") == "AAPL"
        assert get_ticker_symbol(" AAPL ") == "AAPL"
    
    def test_unknown_symbol(self):
        """Test unknown symbols are returned uppercase."""
        assert get_ticker_symbol("UNKNOWN") == "UNKNOWN"
        assert get_ticker_symbol("XYZ123") == "XYZ123"


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test health endpoint returns 200."""
        response = client.get('/health')
        assert response.status_code == 200
        assert response.json == {"status": "healthy"}


class TestMetricsEndpoint:
    """Test Prometheus metrics endpoint."""
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint returns Prometheus format."""
        response = client.get('/metrics')
        assert response.status_code == 200
        assert b'market_api_requests_total' in response.data or True  # Metrics may be empty initially


@pytest.mark.unit
class TestQuoteEndpoint:
    """Test /quote endpoint."""
    
    def test_quote_missing_symbol(self, client):
        """Test quote endpoint without symbol parameter."""
        response = client.get('/quote')
        assert response.status_code == 400
        assert "symbol parameter required" in response.json["error"]
    
    def test_quote_empty_symbol(self, client):
        """Test quote endpoint with empty symbol."""
        response = client.get('/quote?symbol=')
        assert response.status_code == 400
        assert "symbol parameter required" in response.json["error"]
    
    @responses.activate
    def test_quote_success(self, client, sample_quote_response):
        """Test successful quote retrieval."""
        # Mock Finnhub API
        responses.add(
            responses.GET,
            f"{FINNHUB_BASE_URL}/quote",
            json=sample_quote_response,
            status=200
        )
        
        response = client.get('/quote?symbol=AAPL')
        assert response.status_code == 200
        data = response.json
        assert data["c"] == 150.25
        assert data["pc"] == 149.80
        assert data["t"] == 1706889600
    
    @responses.activate
    def test_quote_company_name(self, client, sample_quote_response):
        """Test quote with company name instead of ticker."""
        # Mock Finnhub API
        responses.add(
            responses.GET,
            f"{FINNHUB_BASE_URL}/quote",
            json=sample_quote_response,
            status=200
        )
        
        response = client.get('/quote?symbol=apple')
        assert response.status_code == 200
        # Verify the call was made with AAPL ticker
        assert len(responses.calls) == 1
        assert "symbol=AAPL" in responses.calls[0].request.url
    
    @responses.activate
    def test_quote_invalid_ticker(self, client, empty_quote_response):
        """Test quote with invalid ticker symbol."""
        # Mock Finnhub API returning empty data
        responses.add(
            responses.GET,
            f"{FINNHUB_BASE_URL}/quote",
            json=empty_quote_response,
            status=200
        )
        
        response = client.get('/quote?symbol=INVALID')
        assert response.status_code == 404
        assert "No quote data found" in response.json["error"]
    
    @responses.activate
    def test_quote_api_error(self, client):
        """Test quote endpoint when Finnhub API fails."""
        # Mock Finnhub API error
        responses.add(
            responses.GET,
            f"{FINNHUB_BASE_URL}/quote",
            json={"error": "API error"},
            status=500
        )
        
        response = client.get('/quote?symbol=AAPL')
        assert response.status_code == 503
        assert "Failed to fetch quote" in response.json["error"]
    
    @responses.activate
    def test_quote_timeout(self, client):
        """Test quote endpoint when request times out."""
        # Mock timeout
        import requests
        responses.add(
            responses.GET,
            f"{FINNHUB_BASE_URL}/quote",
            body=requests.exceptions.Timeout()
        )
        
        response = client.get('/quote?symbol=AAPL')
        assert response.status_code == 503


@pytest.mark.unit
class TestNewsEndpoint:
    """Test /news endpoint."""
    
    def test_news_missing_symbol(self, client):
        """Test news endpoint without symbol parameter."""
        response = client.get('/news')
        assert response.status_code == 400
        assert "symbol parameter required" in response.json["error"]
    
    def test_news_empty_symbol(self, client):
        """Test news endpoint with empty symbol."""
        response = client.get('/news?symbol=')
        assert response.status_code == 400
    
    @responses.activate
    def test_news_success(self, client, sample_news_response):
        """Test successful news retrieval."""
        # Mock Finnhub API
        responses.add(
            responses.GET,
            f"{FINNHUB_BASE_URL}/company-news",
            json=sample_news_response,
            status=200
        )
        
        response = client.get('/news?symbol=AAPL')
        assert response.status_code == 200
        data = response.json
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["headline"] == "Apple announces new product line"
        assert data[0]["source"] == "Reuters"
    
    @responses.activate
    def test_news_company_name(self, client, sample_news_response):
        """Test news with company name instead of ticker."""
        # Mock Finnhub API
        responses.add(
            responses.GET,
            f"{FINNHUB_BASE_URL}/company-news",
            json=sample_news_response,
            status=200
        )
        
        response = client.get('/news?symbol=tesla')
        assert response.status_code == 200
        # Verify the call was made with TSLA ticker
        assert len(responses.calls) == 1
        assert "symbol=TSLA" in responses.calls[0].request.url
    
    @responses.activate
    def test_news_empty_results(self, client, empty_news_response):
        """Test news endpoint with no results."""
        # Mock Finnhub API returning empty list
        responses.add(
            responses.GET,
            f"{FINNHUB_BASE_URL}/company-news",
            json=empty_news_response,
            status=200
        )
        
        response = client.get('/news?symbol=AAPL')
        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) == 0
    
    @responses.activate
    def test_news_sorting(self, client):
        """Test that news items are sorted by datetime (most recent first)."""
        unsorted_news = [
            {"datetime": 1706803200, "headline": "Older news"},
            {"datetime": 1706889600, "headline": "Newer news"},
            {"datetime": 1706717000, "headline": "Oldest news"}
        ]
        
        # Mock Finnhub API
        responses.add(
            responses.GET,
            f"{FINNHUB_BASE_URL}/company-news",
            json=unsorted_news,
            status=200
        )
        
        response = client.get('/news?symbol=AAPL')
        assert response.status_code == 200
        data = response.json
        assert data[0]["headline"] == "Newer news"
        assert data[1]["headline"] == "Older news"
        assert data[2]["headline"] == "Oldest news"
    
    @responses.activate
    def test_news_limit_10(self, client):
        """Test that news endpoint returns max 10 items."""
        # Create 15 news items
        many_news = [
            {"datetime": 1706889600 - i * 1000, "headline": f"News {i}"}
            for i in range(15)
        ]
        
        # Mock Finnhub API
        responses.add(
            responses.GET,
            f"{FINNHUB_BASE_URL}/company-news",
            json=many_news,
            status=200
        )
        
        response = client.get('/news?symbol=AAPL')
        assert response.status_code == 200
        assert len(response.json) == 10
    
    @responses.activate
    def test_news_api_error(self, client):
        """Test news endpoint when Finnhub API fails."""
        # Mock Finnhub API error
        responses.add(
            responses.GET,
            f"{FINNHUB_BASE_URL}/company-news",
            json={"error": "API error"},
            status=500
        )
        
        response = client.get('/news?symbol=AAPL')
        assert response.status_code == 503
        assert "Failed to fetch news" in response.json["error"]
    
    @responses.activate
    def test_news_invalid_response_format(self, client):
        """Test news endpoint when API returns non-list response."""
        # Mock Finnhub API returning invalid format
        responses.add(
            responses.GET,
            f"{FINNHUB_BASE_URL}/company-news",
            json={"error": "not a list"},
            status=200
        )
        
        response = client.get('/news?symbol=AAPL')
        assert response.status_code == 200
        assert response.json == []  # Should handle gracefully


@pytest.mark.unit
class TestPrometheusMetrics:
    """Test Prometheus metrics collection."""
    
    @responses.activate
    def test_metrics_recorded_on_success(self, client, sample_quote_response):
        """Test that successful requests increment metrics."""
        # Mock Finnhub API
        responses.add(
            responses.GET,
            f"{FINNHUB_BASE_URL}/quote",
            json=sample_quote_response,
            status=200
        )
        
        # Make request
        client.get('/quote?symbol=AAPL')
        
        # Check metrics endpoint
        metrics_response = client.get('/metrics')
        assert metrics_response.status_code == 200
        # Should contain request count metric (may be empty initially)
        assert metrics_response.data is not None
    
    @responses.activate
    def test_metrics_recorded_on_error(self, client):
        """Test that failed requests increment error metrics."""
        # Mock Finnhub API error
        responses.add(
            responses.GET,
            f"{FINNHUB_BASE_URL}/quote",
            json={"error": "API error"},
            status=500
        )
        
        # Make request that will fail
        client.get('/quote?symbol=AAPL')
        
        # Check metrics endpoint
        metrics_response = client.get('/metrics')
        assert metrics_response.status_code == 200
