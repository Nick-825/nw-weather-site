# app.py — ПОЛНАЯ ВЕРСИЯ

from flask import Flask, render_template, request, jsonify
from services.weather import get_region_weather, fetch_open_meteo, code_to_icon_desc
from services.rates import get_cbr_rates
from services.news import get_headlines
from services.geo import search_cities  # файл services/geo.py из прошлых шагов

app = Flask(__name__)

# -----------------------------
# Страницы (многостраничный сайт)
# -----------------------------

@app.route("/")
def index():
    weather = get_region_weather()
    rates, rates_updated = get_cbr_rates(["USD", "EUR", "CNY"])
    headlines = get_headlines(limit=8)
    return render_template(
        "index.html",
        title="Погода, Новости и Курсы валют",
        weather=weather,
        rates=rates,
        rates_updated=rates_updated,
        headlines=headlines,
    )

@app.route("/rates")
def rates_page():
    rates, rates_updated = get_cbr_rates(["USD", "EUR", "CNY"])
    return render_template(
        "rates.html",
        title="Курсы ЦБ РФ",
        rates=rates,
        rates_updated=rates_updated,
    )

@app.route("/news")
def news_page():
    headlines = get_headlines(limit=20)
    return render_template("news.html", title="Новости", headlines=headlines)

@app.route("/weather")
def weather_search_page():
    # Пустая страница с полем поиска и JS-автодополнением
    return render_template("weather_search.html", title="Поиск по местоположению")


@app.route("/weather/7days")
def weather_weekly_page():
    return render_template("weather_weekly.html", title="Погода на 7 дней")

# -----------------------------
# Внутренние API (JSON)
# -----------------------------

@app.get("/api/cities")
def api_cities():
    """
    Автодополнение городов.
    Прокси к Open-Meteo Geocoding API (БЕЗ ключа).
    Пример: /api/cities?q=санкт
    """
    q = (request.args.get("q") or "").strip()
    results = search_cities(q, count=7, lang="ru")
    return jsonify(results)

@app.get("/api/weather")
def api_weather():
    """
    Прогноз на текущие сутки по координатам.
    Пример: /api/weather?lat=59.9&lon=30.3
    """
    try:
        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
    except (KeyError, ValueError):
        return jsonify({"error": "lat and lon are required floats"}), 400

    data = fetch_open_meteo(
        lat,
        lon,
        hourly=[
            "temperature_2m",
            "apparent_temperature",
            "precipitation",
            "weather_code",
            "wind_speed_10m",
        ],
        daily=[
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max",
            "sunrise",
            "sunset",
        ],
        forecast_days=1,
    )
    cur = data.get("current", {}) or {}
    hourly_block = data.get("hourly", {}) or {}
    hourly_times = hourly_block.get("time") or []

    def pick(block, key, idx):
        arr = block.get(key) or []
        if not isinstance(arr, list):
            return None
        try:
            return arr[idx]
        except IndexError:
            return None

    hourly_points = [
        {
            "time": iso_time,
            "temp": pick(hourly_block, "temperature_2m", idx),
            "feels": pick(hourly_block, "apparent_temperature", idx),
            "precip": pick(hourly_block, "precipitation", idx),
            "code": pick(hourly_block, "weather_code", idx),
            "wind": pick(hourly_block, "wind_speed_10m", idx),
        }
        for idx, iso_time in enumerate(hourly_times)
    ]

    daily = data.get("daily", {}) or {}

    def pick_first(block, key):
        arr = block.get(key) or []
        if isinstance(arr, list) and arr:
            return arr[0]
        return None

    daily_summary = {
        "time": pick_first(daily, "time"),
        "temp_max": pick_first(daily, "temperature_2m_max"),
        "temp_min": pick_first(daily, "temperature_2m_min"),
        "precip_sum": pick_first(daily, "precipitation_sum"),
        "wind_max": pick_first(daily, "wind_speed_10m_max"),
        "sunrise": pick_first(daily, "sunrise"),
        "sunset": pick_first(daily, "sunset"),
    }

    code = cur.get("weather_code")
    icon, desc, anim = code_to_icon_desc(int(code) if code is not None else -1)

    return jsonify(
        {
            "current": {
                "temp": cur.get("temperature_2m"),
                "feels": cur.get("apparent_temperature"),
                "precip": cur.get("precipitation"),
                "wind": cur.get("wind_speed_10m"),
                "wdir": cur.get("wind_direction_10m"),
                "time": cur.get("time"),
                "code": code,
                "icon": icon,
                "desc": desc,
                "anim": anim,
            },
            "hourly": hourly_points,
            "hourly_units": data.get("hourly_units", {}),
            "daily": daily_summary,
            "daily_units": data.get("daily_units", {}),
        }
    )


@app.get("/api/weather/weekly")
def api_weather_weekly():
    """Недельный прогноз по координатам."""
    try:
        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
    except (KeyError, ValueError):
        return jsonify({"error": "lat and lon are required floats"}), 400

    data = fetch_open_meteo(
        lat,
        lon,
        daily=[
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max",
            "sunrise",
            "sunset",
        ],
        forecast_days=7,
    )
    daily = data.get("daily", {}) or {}
    times = daily.get("time") or []

    def pick(block, key, idx):
        arr = block.get(key) or []
        if not isinstance(arr, list):
            return None
        try:
            return arr[idx]
        except IndexError:
            return None

    days = []
    for idx, iso_date in enumerate(times):
        code = pick(daily, "weather_code", idx)
        icon, desc, anim = code_to_icon_desc(int(code) if code is not None else -1)
        days.append(
            {
                "time": iso_date,
                "code": code,
                "icon": icon,
                "desc": desc,
                "anim": anim,
                "temp_max": pick(daily, "temperature_2m_max", idx),
                "temp_min": pick(daily, "temperature_2m_min", idx),
                "precip_sum": pick(daily, "precipitation_sum", idx),
                "wind_max": pick(daily, "wind_speed_10m_max", idx),
                "sunrise": pick(daily, "sunrise", idx),
                "sunset": pick(daily, "sunset", idx),
            }
        )

    return jsonify(
        {
            "days": days,
            "units": data.get("daily_units", {}),
            "timezone": data.get("timezone_abbreviation"),
        }
    )


@app.get("/api/rates/search")
def api_rates_search():
    query = (request.args.get("q") or "").strip().lower()
    rates, updated = get_cbr_rates(None)

    if query:
        def _match(item):
            code, payload = item
            name = (payload.get("name") or "").lower()
            return query in code.lower() or query in name

        filtered = [item for item in rates.items() if _match(item)]
    else:
        filtered = list(rates.items())

    # ограничим до 10 результатов, отсортируем по коду
    filtered.sort(key=lambda item: item[0])
    filtered = filtered[:10]

    return jsonify(
        {
            "updated": updated,
            "items": [
                {
                    "code": code,
                    "name": payload.get("name"),
                    "value": payload.get("value"),
                    "symbol": payload.get("symbol"),
                    "emoji": payload.get("emoji"),
                    "accent": payload.get("accent"),
                    "change": payload.get("change"),
                    "change_percent": payload.get("change_percent"),
                }
                for code, payload in filtered
            ],
        }
    )

# -----------------------------
# Тех. проверка
# -----------------------------

@app.route("/health")
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    # локальный запуск
    app.run(debug=True)
