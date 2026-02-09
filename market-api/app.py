import os
import logging
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import requests

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("market-api")

app = Flask(__name__)

# Configuration
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"

# Prometheus metrics
REQUEST_COUNT = Counter(
    "market_api_requests_total",
    "Total requests to market API",
    ["endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "market_api_request_duration_seconds",
    "Request latency in seconds",
    ["endpoint"]
)


def get_ticker_symbol(symbol: str) -> str:
    """
    Convert company name or ticker to a valid ticker symbol.
    This is a simple lookup - in production you'd want a more robust solution.
    """
    # Common mappings
    name_to_ticker = {
        "airbus": "AIR.PA",
        "apple": "AAPL",
        "tesla": "TSLA",
        "microsoft": "MSFT",
        "google": "GOOGL",
        "amazon": "AMZN",
        "meta": "META",
        "nvidia": "NVDA",
    }
    
    symbol_lower = symbol.lower().strip()
    
    # If it's a known name, return the ticker
    if symbol_lower in name_to_ticker:
        return name_to_ticker[symbol_lower]
    
    # Otherwise assume it's already a ticker
    return symbol.strip().upper()


@app.route("/quote", methods=["GET"])
def get_quote():
    """
    Get current stock quote for a symbol.
    Query params:
        - symbol: stock ticker or company name (e.g., 'AAPL', 'Apple')
    
    Returns:
        {
            "c": current_price,
            "pc": previous_close,
            "t": timestamp,
            "h": high,
            "l": low,
            "o": open
        }
    """
    with REQUEST_LATENCY.labels(endpoint="quote").time():
        try:
            symbol = request.args.get("symbol", "").strip()
            if not symbol:
                REQUEST_COUNT.labels(endpoint="quote", status="error").inc()
                return jsonify({"error": "symbol parameter required"}), 400
            
            # Convert to ticker if needed
            ticker = get_ticker_symbol(symbol)
            log.info(f"[QUOTE] Requested symbol={symbol}, using ticker={ticker}")
            
            # Call Finnhub API
            url = f"{FINNHUB_BASE_URL}/quote"
            params = {"symbol": ticker, "token": FINNHUB_API_KEY}
            
            response = requests.get(url, params=params, timeout=5.0)
            response.raise_for_status()
            
            data = response.json()
            
            # Finnhub returns: c, h, l, o, pc, t
            # Ensure we have valid data
            if data.get("c", 0) == 0 and data.get("pc", 0) == 0:
                log.warning(f"[QUOTE] No data found for ticker={ticker}")
                REQUEST_COUNT.labels(endpoint="quote", status="error").inc()
                return jsonify({"error": f"No quote data found for {ticker}"}), 404
            
            log.info(f"[QUOTE] Success for {ticker}: c={data.get('c')}, pc={data.get('pc')}")
            REQUEST_COUNT.labels(endpoint="quote", status="success").inc()
            
            return jsonify(data), 200
            
        except requests.exceptions.RequestException as e:
            log.error(f"[QUOTE] Finnhub API error: {e}")
            REQUEST_COUNT.labels(endpoint="quote", status="error").inc()
            return jsonify({"error": "Failed to fetch quote from upstream"}), 503
        except Exception as e:
            log.error(f"[QUOTE] Unexpected error: {e}")
            REQUEST_COUNT.labels(endpoint="quote", status="error").inc()
            return jsonify({"error": "Internal server error"}), 500


@app.route("/news", methods=["GET"])
def get_news():
    """
    Get recent company news for a symbol.
    Query params:
        - symbol: stock ticker or company name
    
    Returns:
        [
            {
                "headline": "...",
                "source": "...",
                "datetime": epoch_timestamp,
                "url": "...",
                "summary": "..."
            },
            ...
        ]
    """
    with REQUEST_LATENCY.labels(endpoint="news").time():
        try:
            symbol = request.args.get("symbol", "").strip()
            if not symbol:
                REQUEST_COUNT.labels(endpoint="news", status="error").inc()
                return jsonify({"error": "symbol parameter required"}), 400
            
            # Convert to ticker if needed
            ticker = get_ticker_symbol(symbol)
            log.info(f"[NEWS] Requested symbol={symbol}, using ticker={ticker}")
            
            # Call Finnhub company news endpoint
            # Get news from last 7 days
            from_date = (datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                        .timestamp() - 7 * 24 * 3600)
            to_date = datetime.now(timezone.utc).timestamp()
            
            from_str = datetime.fromtimestamp(from_date, tz=timezone.utc).strftime("%Y-%m-%d")
            to_str = datetime.fromtimestamp(to_date, tz=timezone.utc).strftime("%Y-%m-%d")
            
            url = f"{FINNHUB_BASE_URL}/company-news"
            params = {
                "symbol": ticker,
                "from": from_str,
                "to": to_str,
                "token": FINNHUB_API_KEY
            }
            
            response = requests.get(url, params=params, timeout=5.0)
            response.raise_for_status()
            
            data = response.json()
            
            if not isinstance(data, list):
                log.warning(f"[NEWS] Unexpected response format for {ticker}")
                REQUEST_COUNT.labels(endpoint="news", status="error").inc()
                return jsonify([]), 200
            
            # Limit to top 10 most recent
            news_items = sorted(data, key=lambda x: x.get("datetime", 0), reverse=True)[:10]
            
            log.info(f"[NEWS] Success for {ticker}: {len(news_items)} items")
            REQUEST_COUNT.labels(endpoint="news", status="success").inc()
            
            return jsonify(news_items), 200
            
        except requests.exceptions.RequestException as e:
            log.error(f"[NEWS] Finnhub API error: {e}")
            REQUEST_COUNT.labels(endpoint="news", status="error").inc()
            return jsonify({"error": "Failed to fetch news from upstream"}), 503
        except Exception as e:
            log.error(f"[NEWS] Unexpected error: {e}")
            REQUEST_COUNT.labels(endpoint="news", status="error").inc()
            return jsonify({"error": "Internal server error"}), 500


@app.route("/metrics", methods=["GET"])
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    if not FINNHUB_API_KEY:
        log.warning("⚠️  FINNHUB_API_KEY not set - API calls will fail!")
    else:
        log.info("✓ Finnhub API key configured")
    
    port = int(os.getenv("PORT", "9000"))
    log.info(f"Starting market-api on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)