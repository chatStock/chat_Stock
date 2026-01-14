import httpx
from datetime import datetime, timedelta
from .config import FINNHUB_API_KEY, FINNHUB_BASE_URL, REQUEST_TIMEOUT

# Mapping des noms de compagnies vers leurs tickers
COMPANY_TO_TICKER = {
    # Tech US
    'nvidia': 'NVDA',
    'apple': 'AAPL',
    'microsoft': 'MSFT',
    'tesla': 'TSLA',
    'amazon': 'AMZN',
    'google': 'GOOGL',
    'alphabet': 'GOOGL',
    'meta': 'META',
    'facebook': 'META',
    'netflix': 'NFLX',
    'amd': 'AMD',
    'intel': 'INTC',
    # France
    'airbus': 'AIR.PA',
    'lvmh': 'MC.PA',
    'total': 'TTE.PA',
    'totalenergies': 'TTE.PA',
    'loreal': 'OR.PA',
    'l\'oreal': 'OR.PA',
    'sanofi': 'SAN.PA',
    'bnp': 'BNP.PA',
    'bnp paribas': 'BNP.PA',
    # Autres
    'coca cola': 'KO',
    'coca-cola': 'KO',
    'mcdonalds': 'MCD',
    'nike': 'NKE',
    'disney': 'DIS',
}

def normalize_symbol(symbol: str) -> str:
    """Convertit un nom de compagnie en ticker officiel si nécessaire."""
    # Nettoyer le symbole
    clean_symbol = symbol.strip().lower()
    
    # Chercher dans le mapping
    if clean_symbol in COMPANY_TO_TICKER:
        ticker = COMPANY_TO_TICKER[clean_symbol]
        import logging
        log = logging.getLogger("market_client")
        log.info(f"Converted '{symbol}' to ticker '{ticker}'")
        return ticker
    
    # Si pas trouvé, retourner tel quel (supposer que c'est déjà un ticker)
    return symbol.upper()

async def fetch_quote(symbol: str) -> dict:
    """Récupère la cotation actuelle d'un symbole boursier via Finnhub."""
    # Normaliser le symbole (convertir nom en ticker si nécessaire)
    ticker = normalize_symbol(symbol)
    
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        url = f"{FINNHUB_BASE_URL}/quote"
        params = {
            'symbol': ticker,
            'token': FINNHUB_API_KEY
        }
        
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        
        # Logging pour debug
        import logging
        log = logging.getLogger("market_client")
        log.info(f"Finnhub response for {ticker}: {data}")
        
        # Vérifier si on a une erreur dans la réponse
        if 'error' in data:
            raise ValueError(f"Erreur API Finnhub: {data['error']}")
        
        # Vérifier si le marché a retourné des données valides
        # Note: c=0 peut être valide si le marché est fermé, on vérifie plutôt si les données existent
        if not data or data.get('c') is None:
            raise ValueError(f"Aucune donnée disponible pour {ticker}. Vérifiez le symbole ou votre clé API.")
        
        # Ajouter le symbole dans les données pour le traitement
        data['symbol'] = ticker
        return data


async def fetch_news(symbol: str, days_back: int = 7) -> list[dict]:
    """Récupère les dernières actualités d'un symbole boursier via Finnhub."""
    # Normaliser le symbole (convertir nom en ticker si nécessaire)
    ticker = normalize_symbol(symbol)
    
    date_to = datetime.now().strftime('%Y-%m-%d')
    date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        url = f"{FINNHUB_BASE_URL}/company-news"
        params = {
            'symbol': ticker,
            'from': date_from,
            'to': date_to,
            'token': FINNHUB_API_KEY
        }
        
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        
        # Finnhub retourne directement une liste
        if not isinstance(data, list):
            raise ValueError("Finnhub /company-news doit retourner une liste JSON")
        
        return data if data else []