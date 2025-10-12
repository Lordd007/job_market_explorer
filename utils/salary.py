def normalize_salary(min_v, max_v, currency: str | None, period: str | None) -> float | None:
    if min_v is None and max_v is None:
        return None
    cur = (currency or "USD").upper()
    per = (period or "yearly").lower()

    v = ( (min_v or max_v or 0) + (max_v or min_v or 0) ) / 2.0
    if per in ("hour","hourly"):   v *= 2080
    elif per in ("day","daily"):   v *= 260
    elif per in ("week","weekly"): v *= 52
    elif per in ("month","monthly"): v *= 12

    rates = {"USD":1.0, "EUR":1.07, "GBP":1.26, "CAD":0.73, "AUD":0.66}
    usd = v * rates.get(cur, 1.0)
    return round(usd, 0)
