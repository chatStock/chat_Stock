from app.stock_logic import shape_stock

def test_shape_stock_up_trend():
    raw = {
        "c": 110,
        "pc": 100,
        "t": 1700000000,
    }

    result = shape_stock(raw, "AAPL")

    assert result.symbol == "AAPL"
    assert result.current_price == 110
    assert result.change_pct == 10.0
    assert result.trend == "up"
    assert result.diagram.y == [110]