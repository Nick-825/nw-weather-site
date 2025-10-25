from services.cache import ttl_cache
import requests
from datetime import datetime

# Города СЗФО (минимальный набор; добавим позже больше)
CITIES = [
    {"name": "Санкт-Петербург", "lat": 59.9386, "lon": 30.3141},
    {"name": "Петрозаводск", "lat": 61.7850, "lon": 34.3469},
    {"name": "Мурманск", "lat": 68.9730, "lon": 33.0925},
    {"name": "Псков", "lat": 57.8136, "lon": 28.3496},
    {"name": "Великий Новгород", "lat": 58.5215, "lon": 31.2755},
    {"name": "Калининград", "lat": 54.7104, "lon": 20.4522},
]

def fetch_open_meteo(lat, lon):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,"
        "weather_code,wind_speed_10m,wind_direction_10m"
        "&hourly=temperature_2m,precipitation_probability"
        "&timezone=auto"
    )
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.json()

@ttl_cache(600)
def get_region_weather():
    ...
    
def get_region_weather():
    out = []
    for c in CITIES:
        try:
            data = fetch_open_meteo(c["lat"], c["lon"])
            cur = data.get("current", {})
            out.append({
                "city": c["name"],
                "temp": cur.get("temperature_2m"),
                "feels": cur.get("apparent_temperature"),
                "precip": cur.get("precipitation"),
                "wind": cur.get("wind_speed_10m"),
                "wdir": cur.get("wind_direction_10m"),
                "time": cur.get("time"),
            })
        except Exception as e:
            out.append({"city": c["name"], "error": str(e)})

    return out
