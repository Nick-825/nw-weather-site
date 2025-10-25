import requests

CBR_DAILY = "https://www.cbr-xml-daily.ru/daily_json.js"

def get_cbr_rates(codes=("USD","EUR","CNY")):
    r = requests.get(CBR_DAILY, timeout=10)
    r.raise_for_status()
    data = r.json().get("Valute", {})
    res = {}
    for code in codes:
        v = data.get(code)
        if v:
            res[code] = {
                "name": v.get("Name"),
                "value": v.get("Value"),
                "prev": v.get("Previous"),
            }
    return res