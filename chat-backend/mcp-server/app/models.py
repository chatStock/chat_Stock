from pydantic import BaseModel
from typing import List


class DiagramData(BaseModel):
    x: List[str]
    y: List[float]


class StockResponse(BaseModel):
    symbol: str
    current_price: float
    change_pct: float
    trend: str
    diagram: DiagramData


class NewsResponse(BaseModel):
    headline: str
    source: str
    published_at: str
    impact: str