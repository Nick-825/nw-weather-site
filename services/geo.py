# services/geo.py
import requests

def search_cities(name: str, count: int = 5, lang: str = "ru"):
    if not name.strip():
        return []
    url = "https://geocoding-api.open-meteo.com/v1/search"
    r = requests.get(url, params={"name": name, "count": count, "language": lang, "format": "json"}, timeout=12)
    r.raise_for_status()
    data = r.json() or {}
    results = []
    for it in data.get("results", [])[:count]:
        results.append({
            "name": it.get("name"),
            "country": it.get("country"),
            "admin1": it.get("admin1"),
            "lat": it.get("latitude"),
            "lon": it.get("longitude"),
        })
    return results
