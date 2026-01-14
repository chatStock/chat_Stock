from pydantic import BaseModel
from datetime import datetime

class StockQuote(BaseModel):
    symbole: str
    prix_en_temps_réel: str
    évolution_du_jour: str
    évolution_en_pourcentage: str
    plus_haut_du_jour: str
    plus_bas_du_jour: str
    prix_à_l_ouverture: str
    clôture_de_la_veille: str
    dernière_mise_à_jour: str

def shape_stock(raw_data: dict, symbol: str) -> StockQuote:
    """Transforme les données brutes Finnhub en format lisible."""
    c = raw_data.get('c', 0)    # Current price
    d = raw_data.get('d', 0)    # Change
    dp = raw_data.get('dp', 0)  # Percent change
    h = raw_data.get('h', 0)    # High
    l = raw_data.get('l', 0)    # Low
    o = raw_data.get('o', 0)    # Open
    pc = raw_data.get('pc', 0)  # Previous close
    t = raw_data.get('t', 0)    # Timestamp
    
    return StockQuote(
        symbole=symbol.upper(),
        prix_en_temps_réel=f"${c:.2f}",
        évolution_du_jour=f"+${d:.2f}" if d >= 0 else f"-${abs(d):.2f}",
        évolution_en_pourcentage=f"+{dp:.2f}%" if dp >= 0 else f"{dp:.2f}%",
        plus_haut_du_jour=f"${h:.2f}",
        plus_bas_du_jour=f"${l:.2f}",
        prix_à_l_ouverture=f"${o:.2f}",
        clôture_de_la_veille=f"${pc:.2f}",
        dernière_mise_à_jour=datetime.fromtimestamp(t).strftime('%d/%m/%Y à %H:%M:%S') if t else "N/A"
    )