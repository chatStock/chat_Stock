from app.news_logic import shape_news_item

def test_shape_news_item_basic():
    raw = {
        "headline": "Apple releases new product",
        "source": "Reuters",
        "datetime": 1700000000,
    }

    result = shape_news_item(raw)

    assert result.headline == "Apple releases new product"
    assert result.source == "Reuters"
    assert result.impact == "medium"
    assert result.published_at != "unknown"