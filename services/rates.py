from datetime import datetime
from typing import Optional

from services.cache import ttl_cache
import requests

CBR_DAILY = "https://www.cbr-xml-daily.ru/daily_json.js"

CURRENCY_META = {
    "USD": {
        "symbol": "$",
        "emoji": "🇺🇸",
        "accent": "from-blue-900/90 via-indigo-700/80 to-sky-600/70",
    },
    "EUR": {
        "symbol": "€",
        "emoji": "🇪🇺",
        "accent": "from-indigo-900/90 via-violet-700/80 to-purple-600/70",
    },
    "CNY": {
        "symbol": "¥",
        "emoji": "🇨🇳",
        "accent": "from-rose-900/90 via-red-700/80 to-amber-600/70",
    },
}

def _format_timestamp(raw: str) -> Optional[str]:
    if not raw:
        return None

    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None

    offset = dt.strftime("%z")
    if offset:
        offset = f" UTC{offset[:3]}:{offset[3:]}"

    return f"{dt.strftime('%d.%m.%Y %H:%M')}{offset}".strip()


@ttl_cache(600)
def _get_all_cbr_rates():
    r = requests.get(CBR_DAILY, timeout=10)
    r.raise_for_status()
    payload = r.json()
    data = payload.get("Valute", {})
    updated_label = (
        _format_timestamp(payload.get("Date"))
        or _format_timestamp(payload.get("Timestamp"))
        or ""
    )
    res = {}

    for code, v in data.items():
        if not v:
            continue
        value = v.get("Value")
        prev = v.get("Previous")
        change = value - prev if (value is not None and prev is not None) else None
        change_pct = (change / prev * 100) if (change is not None and prev) else None
        meta = CURRENCY_META.get(code, {})

        res[code] = {
            "name": v.get("Name"),
            "value": value,
            "prev": prev,
            "change": change,
            "change_percent": change_pct,
            "symbol": meta.get("symbol", ""),
            "emoji": meta.get("emoji"),
            "accent": meta.get("accent", "from-slate-800/80 to-slate-900/80"),
            "updated_at": updated_label,
        }

    return res, updated_label


def get_cbr_rates(codes=None):
    res, updated_label = _get_all_cbr_rates()

    if codes is None:
        return res, updated_label

    filtered = {}
    for code in codes:
        if code in res:
            filtered[code] = res[code]

    return filtered, updated_label
