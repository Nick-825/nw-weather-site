import requests

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
        "&current=temperature_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m"
        "&timezone=auto"
    )
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.json()

def code_to_icon_desc(code: int):
    # Мини-карта кодов Open-Meteo → эмодзи + краткое описание
    # https://open-meteo.com/en/docs#weathervariables
    groups = [
        ((0,),               "☀️", "Ясно", "spin-slow"),
        ((1, 2),             "🌤️", "Переменная облачность", "float"),
        ((3,),               "☁️", "Облачно", "float"),
        ((45, 48),           "🌫️", "Туман/изморозь", "fade"),
        ((51, 53, 55),       "🌦️", "Морось", "float"),
        ((56, 57),           "🌧️", "Ледяная морось", "float"),
        ((61, 63, 65),       "🌧️", "Дождь", "float"),
        ((66, 67),           "🌧️", "Ледяной дождь", "float"),
        ((71, 73, 75, 77),   "❄️", "Снег/снежные зёрна", "float"),
        ((80, 81, 82),       "🌦️", "Ливни", "float"),
        ((85, 86),           "🌨️", "Снегопад", "float"),
        ((95, 96, 99),       "⛈️", "Гроза", "pulse"),
    ]
    for codes, icon, desc, anim in groups:
        if code in codes:
            return icon, desc, anim
    return "🌡️", "Погода", "fade"

def get_region_weather():
    out = []
    for c in CITIES:
        try:
            data = fetch_open_meteo(c["lat"], c["lon"])
            cur = data.get("current", {})
            code = cur.get("weather_code")
            icon, desc, anim = code_to_icon_desc(int(code) if code is not None else -1)
            out.append({
                "city": c["name"],
                "temp": cur.get("temperature_2m"),
                "feels": cur.get("apparent_temperature"),
                "precip": cur.get("precipitation"),
                "wind": cur.get("wind_speed_10m"),
                "wdir": cur.get("wind_direction_10m"),
                "code": code,
                "icon": icon,
                "desc": desc,
                "anim": anim,   # класс анимации для иконки
                "time": cur.get("time"),
            })
        except Exception as e:
            out.append({"city": c["name"], "error": str(e)})
    return out
