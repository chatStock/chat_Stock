from pydantic import BaseModel
from datetime import datetime

class NewsItem(BaseModel):
    headline: str
    source: str
    published_at: str
    summary: str
    url: str
    impact: str

def shape_news_item(raw_item: dict) -> NewsItem:
    """Transforme un article de news brut Finnhub en format structuré."""
    # Estimer l'impact basé sur le sentiment (si disponible)
    sentiment = raw_item.get('sentiment', 0)
    if sentiment > 0.3:
        impact = "positif"
    elif sentiment < -0.3:
        impact = "négatif"
    else:
        impact = "neutre"
    
    # Formatter la date
    timestamp = raw_item.get('datetime', 0)
    if timestamp:
        published = datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y à %H:%M:%S')
    else:
        published = "Date inconnue"
    
    # Récupérer le résumé et le limiter
    summary = raw_item.get('summary', '')
    if len(summary) > 200:
        summary = summary[:197] + '...'
    elif not summary:
        summary = 'Résumé non disponible'
    
    return NewsItem(
        headline=raw_item.get('headline', 'Titre non disponible'),
        source=raw_item.get('source', 'Source inconnue'),
        published_at=published,
        summary=summary,
        url=raw_item.get('url', ''),
        impact=impact
    )