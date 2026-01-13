from datetime import datetime, timezone
from .models import StockResponse, DiagramData


def shape_stock(raw: dict, symbol: str) -> StockResponse:
    # Accept common quote payloads (Finnhub-like)
    # c = current, pc = previous close, t = epoch seconds
    current = float(raw["c"])
    previous = float(raw["pc"])
    t = int(raw.get("t", 0))

    if previous == 0:
        change_pct = 0.0
    else:
        # If upstream provides dp already you could use it, but we keep this deterministic and simple.
        change_pct = round(((current - previous) / previous) * 100.0, 2)

    if change_pct > 0:
        trend = "up"
    elif change_pct < 0:
        trend = "down"
    else:
        trend = "flat"

    # Diagram-ready (minimal): one point snapshot
    if t > 0:
        x = [datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d")]
    else:
        x = []

    diagram = DiagramData(x=x, y=[current] if x else [])

    return StockResponse(
        symbol=symbol,
        current_price=current,
        change_pct=change_pct,
        trend=trend,
        diagram=diagram,
    )