# app.py — ПОЛНАЯ ВЕРСИЯ

from flask import Flask, render_template, request, jsonify
from services.weather import get_region_weather, fetch_open_meteo
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
        title="Северо-Запад: погода • новости • курсы",
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
    return render_template("weather_search.html", title="Поиск погоды")

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
    Текущая погода по координатам.
    Пример: /api/weather?lat=59.9&lon=30.3
    """
    try:
        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
    except (KeyError, ValueError):
        return jsonify({"error": "lat and lon are required floats"}), 400

    data = fetch_open_meteo(lat, lon)
    cur = data.get("current", {}) or {}
    return jsonify({
        "temp": cur.get("temperature_2m"),
        "feels": cur.get("apparent_temperature"),
        "precip": cur.get("precipitation"),
        "wind": cur.get("wind_speed_10m"),
        "wdir": cur.get("wind_direction_10m"),
        "time": cur.get("time"),
        "code": cur.get("weather_code"),
    })

# -----------------------------
# Тех. проверка
# -----------------------------

@app.route("/health")
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    # локальный запуск
    app.run(debug=True)
