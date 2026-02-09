import pytest
import os
import responses
from app import FINNHUB_BASE_URL


@pytest.mark.integration
class TestQuoteIntegration:
    """Integration tests for quote endpoint."""
    
    @pytest.mark.skipif(
        not os.getenv("FINNHUB_API_KEY") or os.getenv("FINNHUB_API_KEY") == "test_api_key",
        reason="Requires valid FINNHUB_API_KEY"
    )
    def test_real_quote_aapl(self, client):
        """Test real API call for AAPL quote."""
        response = client.get('/quote?symbol=AAPL')
        assert response.status_code == 200
        data = response.json
        assert "c" in data  # current price
        assert "pc" in data  # previous close
        assert data["c"] > 0  # Price should be positive
    
    @pytest.mark.skipif(
        not os.getenv("FINNHUB_API_KEY") or os.getenv("FINNHUB_API_KEY") == "test_api_key",
        reason="Requires valid FINNHUB_API_KEY"
    )
    def test_real_quote_with_company_name(self, client):
        """Test real API call using company name."""
        response = client.get('/quote?symbol=microsoft')
        assert response.status_code == 200
        data = response.json
        assert data["c"] > 0


@pytest.mark.integration
class TestNewsIntegration:
    """Integration tests for news endpoint."""
    
    @pytest.mark.skipif(
        not os.getenv("FINNHUB_API_KEY") or os.getenv("FINNHUB_API_KEY") == "test_api_key",
        reason="Requires valid FINNHUB_API_KEY"
    )
    def test_real_news_aapl(self, client):
        """Test real API call for AAPL news."""
        response = client.get('/news?symbol=AAPL')
        assert response.status_code == 200
        data = response.json
        assert isinstance(data, list)
        # May or may not have news depending on the day
        if len(data) > 0:
            assert "headline" in data[0]
            assert "source" in data[0]
            assert "datetime" in data[0]
    
    @pytest.mark.skipif(
        not os.getenv("FINNHUB_API_KEY") or os.getenv("FINNHUB_API_KEY") == "test_api_key",
        reason="Requires valid FINNHUB_API_KEY"
    )
    def test_real_news_with_company_name(self, client):
        """Test real API call using company name."""
        response = client.get('/news?symbol=tesla')
        assert response.status_code == 200
        data = response.json
        assert isinstance(data, list)


@pytest.mark.integration
class TestEndToEnd:
    """End-to-end integration tests."""
    
    @responses.activate
    def test_quote_to_news_workflow(self, client, sample_quote_response, sample_news_response):
        """Test typical workflow: get quote then news."""
        # Mock both endpoints
        responses.add(
            responses.GET,
            f"{FINNHUB_BASE_URL}/quote",
            json=sample_quote_response,
            status=200
        )
        responses.add(
            responses.GET,
            f"{FINNHUB_BASE_URL}/company-news",
            json=sample_news_response,
            status=200
        )
        
        # Get quote
        quote_response = client.get('/quote?symbol=AAPL')
        assert quote_response.status_code == 200
        
        # Get news
        news_response = client.get('/news?symbol=AAPL')
        assert news_response.status_code == 200
        
        # Verify both succeeded
        assert quote_response.json["c"] == 150.25
        assert len(news_response.json) == 2
    
    @responses.activate
    def test_multiple_symbols_sequence(self, client, sample_quote_response):
        """Test querying multiple symbols in sequence."""
        # Mock responses for different symbols
        responses.add(
            responses.GET,
            f"{FINNHUB_BASE_URL}/quote",
            json=sample_quote_response,
            status=200
        )
        responses.add(
            responses.GET,
            f"{FINNHUB_BASE_URL}/quote",
            json={**sample_quote_response, "c": 200.50},
            status=200
        )
        
        # Query AAPL
        response1 = client.get('/quote?symbol=AAPL')
        assert response1.status_code == 200
        
        # Query MSFT
        response2 = client.get('/quote?symbol=MSFT')
        assert response2.status_code == 200
        
        # Both should succeed
        assert response1.json["c"] == 150.25
        assert response2.json["c"] == 200.50


@pytest.mark.integration
class TestErrorRecovery:
    """Test error handling and recovery."""
    
    @responses.activate
    def test_partial_failure_recovery(self, client, sample_quote_response):
        """Test that one failed request doesn't affect subsequent requests."""
        # First request fails
        responses.add(
            responses.GET,
            f"{FINNHUB_BASE_URL}/quote",
            json={"error": "API error"},
            status=500
        )
        
        # Second request succeeds
        responses.add(
            responses.GET,
            f"{FINNHUB_BASE_URL}/quote",
            json=sample_quote_response,
            status=200
        )
        
        # First request should fail
        response1 = client.get('/quote?symbol=AAPL')
        assert response1.status_code == 503
        
        # Second request should succeed
        response2 = client.get('/quote?symbol=AAPL')
        assert response2.status_code == 200
        assert response2.json["c"] == 150.25
