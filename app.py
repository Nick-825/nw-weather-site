from flask import Flask, render_template, request, jsonify
from services.weather import get_region_weather, fetch_open_meteo, code_to_icon_desc
from services.rates import get_cbr_rates
from services.news import get_headlines
from services.geo import search_cities  # файл services/geo.py
import requests  # <— для крипто-API

app = Flask(__name__)

# Фолбэк для фиатных валют: флаг и символ, если источник их не прислал
FIAT_META = {
    "USD": {"emoji": "🇺🇸", "symbol": "$"},
    "EUR": {"emoji": "🇪🇺", "symbol": "€"},
    "GBP": {"emoji": "🇬🇧", "symbol": "£"},
    "CNY": {"emoji": "🇨🇳", "symbol": "¥"},
    "JPY": {"emoji": "🇯🇵", "symbol": "¥"},
    "TRY": {"emoji": "🇹🇷", "symbol": "₺"},
    "KZT": {"emoji": "🇰🇿", "symbol": "₸"},
    "UAH": {"emoji": "🇺🇦", "symbol": "₴"},
    "AED": {"emoji": "🇦🇪", "symbol": "د.إ"},
    "BYN": {"emoji": "🇧🇾", "symbol": "Br"},
    "AMD": {"emoji": "🇦🇲", "symbol": "֏"},
    "AZN": {"emoji": "🇦🇿", "symbol": "₼"},
    "EGP": {"emoji": "🇪🇬", "symbol": "E£"},
    "CDF": {"emoji": "🇨🇩", "symbol": "FC"},
}


# -----------------------------
# Страницы
# -----------------------------

@app.route("/")
def index():
    weather = get_region_weather()
    rates, rates_updated = get_cbr_rates(["USD", "EUR", "CNY"])
    headlines = get_headlines(limit=10)  # было 8 → стало 10
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
    # на самой странице «Курсы валют» — только поиск (карточки основных курсов НЕ показываем)
    return render_template("rates.html", title="Курсы ЦБ РФ")

@app.route("/news")
def news_page():
    headlines = get_headlines(limit=20)
    return render_template("news.html", title="Новости", headlines=headlines)

@app.route("/weather")
def weather_search_page():
    return render_template("weather_search.html", title="Поиск по местоположению")

@app.route("/weather/7days")
def weather_weekly_page():
    return render_template("weather_weekly.html", title="Погода на 7 дней")


# -----------------------------
# Внутренние API (JSON)
# -----------------------------

@app.get("/api/cities")
def api_cities():
    q = (request.args.get("q") or "").strip()
    results = search_cities(q, count=7, lang="ru")
    return jsonify(results)

@app.get("/api/weather")
def api_weather():
    try:
        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
    except (KeyError, ValueError):
        return jsonify({"error": "lat and lon are required floats"}), 400

    data = fetch_open_meteo(
        lat, lon,
        hourly=["temperature_2m", "apparent_temperature", "precipitation", "weather_code", "wind_speed_10m"],
        daily=["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "wind_speed_10m_max", "sunrise", "sunset"],
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
    try:
        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
    except (KeyError, ValueError):
        return jsonify({"error": "lat and lon are required floats"}), 400

    data = fetch_open_meteo(
        lat, lon,
        daily=["weather_code", "temperature_2m_max", "temperature_2m_min", "precipitation_sum", "wind_speed_10m_max", "sunrise", "sunset"],
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

# ------- Новый API: поиск курсов криптовалют (CoinGecko, в RUB) -------
# /api/crypto/search?q=btc
# Возвращает структуру items, совместимую с /api/rates/search (code/name/value/symbol/emoji/...)
CG_BASE = "https://api.coingecko.com/api/v3"

_CRYPTO_EMOJI = {
    "bitcoin": "₿", "btc": "₿",
    "ethereum": "Ξ", "eth": "Ξ",
    "litecoin": "Ł", "ltc": "Ł",
    "monero": "ɱ", "xmr": "ɱ",
    "ripple": "✕", "xrp": "✕",
    "toncoin": "🧿", "ton": "🧿",
    "tether": "₮", "usdt": "₮",
    "binancecoin": "Ⓑ", "bnb": "Ⓑ",
}

@app.get("/api/crypto/search")
def api_crypto_search():
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"updated": "", "items": ["items": [
    (lambda code, payload: {
        "code": code,
        "name": payload.get("name"),
        "value": payload.get("value"),
        "symbol": payload.get("symbol") or FIAT_META.get(code, {}).get("symbol"),
        "emoji": payload.get("emoji") or FIAT_META.get(code, {}).get("emoji"),
        "accent": payload.get("accent"),
        "change": payload.get("change"),
        "change_percent": payload.get("change_percent"),
    })(code, payload)
    for code, payload in filtered
],],
        }
    )


@app.route("/health")
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(debug=True)
