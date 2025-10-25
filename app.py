from flask import Flask, render_template
from services.weather import get_region_weather
from services.rates import get_cbr_rates
from services.news import get_headlines

app = Flask(__name__)

@app.route("/")
def index():
    weather = get_region_weather()
    rates = get_cbr_rates(["USD", "EUR", "CNY"])
    headlines = get_headlines(limit=8)
    return render_template("index.html", weather=weather, rates=rates, headlines=headlines)

# ✅ Добавляем health route
@app.route("/health")
def health():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    app.run(debug=True)
