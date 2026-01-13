from datetime import datetime, timezone
from .models import NewsResponse


def shape_news_item(raw: dict) -> NewsResponse:
    # Expect: headline, source, datetime (epoch seconds)
    headline = str(raw["headline"])
    source = str(raw.get("source", "unknown"))
    ts = int(raw.get("datetime", 0))

    published_at = (
        datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        if ts > 0
        else "unknown"
    )

    # Stub: keep deterministic for now
    impact = "medium"

    return NewsResponse(
        headline=headline,
        source=source,
        published_at=published_at,
        impact=impact,
    )