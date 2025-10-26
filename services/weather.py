import requests

DEFAULT_CURRENT_FIELDS = (
    "temperature_2m,apparent_temperature,precipitation,weather_code,"
    "wind_speed_10m,wind_direction_10m"
)

CITIES = [
    {"name": "Санкт-Петербург", "lat": 59.9386, "lon": 30.3141},
    {"name": "Петрозаводск", "lat": 61.7850, "lon": 34.3469},
    {"name": "Мурманск", "lat": 68.9730, "lon": 33.0925},
    {"name": "Псков", "lat": 57.8136, "lon": 28.3496},
    {"name": "Великий Новгород", "lat": 58.5215, "lon": 31.2755},
    {"name": "Калининград", "lat": 54.7104, "lon": 20.4522},
]

def fetch_open_meteo(
    lat,
    lon,
    *,
    hourly=None,
    daily=None,
    forecast_days=None,
):
    params = [
        f"latitude={lat}",
        f"longitude={lon}",
        f"current={DEFAULT_CURRENT_FIELDS}",
        "timezone=auto",
    ]
    if hourly:
        params.append("hourly=" + ",".join(hourly))
    if daily:
        params.append("daily=" + ",".join(daily))
    if forecast_days:
        params.append(f"forecast_days={forecast_days}")
    url = "https://api.open-meteo.com/v1/forecast?" + "&".join(params)
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.json()

def code_to_icon_desc(code: int):
    # Мини-карта кодов Open-Meteo → эмодзи + краткое описание
    # https://open-meteo.com/en/docs#weathervariables
    groups = [
        ((0,),               "☀️", "Ясно", "sunny"),
        ((1, 2),             "🌤️", "Переменная облачность", "partly"),
        ((3,),               "☁️", "Облачно", "cloudy"),
        ((45, 48),           "🌫️", "Туман/изморозь", "foggy"),
        ((51, 53, 55),       "🌦️", "Морось", "rainy"),
        ((56, 57),           "🌧️", "Ледяная морось", "icy-rain"),
        ((61, 63, 65),       "🌧️", "Дождь", "rainy"),
        ((66, 67),           "🌧️", "Ледяной дождь", "icy-rain"),
        ((71, 73, 75, 77),   "❄️", "Снег/снежные зёрна", "snowy"),
        ((80, 81, 82),       "🌦️", "Ливни", "rainy"),
        ((85, 86),           "🌨️", "Снегопад", "snowy"),
        ((95, 96, 99),       "⛈️", "Гроза", "stormy"),
    ]
    for codes, icon, desc, anim in groups:
        if code in codes:
            return icon, desc, anim
    return "🌡️", "Погода", "calm"

def get_region_weather():
    out = []
    for c in CITIES:
        try:
            data = fetch_open_meteo(
                c["lat"],
                c["lon"],
                daily=[
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "wind_speed_10m_max",
                ],
                forecast_days=1,
            )
            cur = data.get("current", {})
            code = cur.get("weather_code")
            icon, desc, anim = code_to_icon_desc(int(code) if code is not None else -1)
            daily = data.get("daily", {})
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
                "temp_max": (daily.get("temperature_2m_max") or [None])[0],
                "temp_min": (daily.get("temperature_2m_min") or [None])[0],
                "precip_sum": (daily.get("precipitation_sum") or [None])[0],
                "wind_max": (daily.get("wind_speed_10m_max") or [None])[0],
            })
        except Exception as e:
            out.append({"city": c["name"], "error": str(e)})
    return out
