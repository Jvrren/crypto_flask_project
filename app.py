from flask import Flask, render_template
from flask_wtf import FlaskForm
from wtforms import SelectField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange
import requests
import os
from datetime import datetime

app = Flask(__name__)
# Needed for Flask-WTF CSRF protection
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev_secret_key")


# ---------- 1. FORM DEFINITION ----------
class CryptoForm(FlaskForm):
    coin = SelectField(
        "Cryptocurrency",
        choices=[
            ("bitcoin", "Bitcoin"),
            ("ethereum", "Ethereum"),
            ("dogecoin", "Dogecoin"),
            ("cardano", "Cardano"),
            ("litecoin", "Litecoin"),
        ],
        validators=[DataRequired()],
    )

    currency = SelectField(
        "Fiat Currency",
        choices=[
            ("usd", "USD"),
            ("eur", "EUR"),
            ("gbp", "GBP"),
        ],
        validators=[DataRequired()],
    )

    days = IntegerField(
        "Days of price history (1–30)",
        validators=[DataRequired(), NumberRange(min=1, max=30)],
    )

    submit = SubmitField("Get Prices")


# ---------- 2. ROUTES ----------
@app.route("/", methods=["GET", "POST"])
def index():
    form = CryptoForm()
    crypto_data = None
    error = None

    if form.validate_on_submit():
        coin = form.coin.data
        currency = form.currency.data
        days = form.days.data

        try:
            crypto_data = fetch_crypto_data(coin, currency, days)
        except Exception as e:
            error = f"Error fetching data from API: {e}"

        return render_template(
            "results.html",
            form=form,
            crypto_data=crypto_data,
            error=error,
        )

    return render_template("form.html", form=form)


# ---------- 3. API FETCH + JSON PROCESSING ----------
def fetch_crypto_data(coin_id: str, vs_currency: str, days: int) -> dict:
    """
    Fetch current price and historical data from CoinGecko
    and return processed information for the templates.
    """

    # --- Current price + 24h change ---
    simple_url = "https://api.coingecko.com/api/v3/simple/price"
    simple_params = {
        "ids": coin_id,
        "vs_currencies": vs_currency,
        "include_24hr_change": "true",
        "include_last_updated_at": "true",
    }
    simple_resp = requests.get(simple_url, params=simple_params, timeout=10)
    simple_resp.raise_for_status()
    simple_json = simple_resp.json()

    if coin_id not in simple_json:
        raise ValueError("Coin not found in API response")

    coin_simple = simple_json[coin_id]

    current_price = coin_simple[vs_currency]
    change_24h = coin_simple.get(f"{vs_currency}_24h_change")
    last_updated = coin_simple.get("last_updated_at")

    # --- Historical prices ---
    chart_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    chart_params = {"vs_currency": vs_currency, "days": days}
    chart_resp = requests.get(chart_url, params=chart_params, timeout=10)
    chart_resp.raise_for_status()
    chart_json = chart_resp.json()

    prices = chart_json.get("prices", [])
    if not prices:
        raise ValueError("No price history returned")

    # prices is a list of [timestamp_ms, price]
    price_values = [p[1] for p in prices]
    min_price = min(price_values)
    max_price = max(price_values)
    avg_price = sum(price_values) / len(price_values)

    start_price = price_values[0]
    end_price = price_values[-1]
    period_change_pct = ((end_price - start_price) / start_price) * 100

    # Prepare history data for table (convert timestamps to readable dates)
    history = []
    for ts_ms, price in prices:
        dt = datetime.fromtimestamp(ts_ms / 1000.0)
        history.append(
            {
                "datetime": dt.strftime("%Y-%m-%d %H:%M"),
                "price": round(price, 4),
            }
        )

    # Convert last_updated timestamp
    last_updated_str = None
    if last_updated is not None:
        last_updated_str = datetime.fromtimestamp(last_updated).strftime(
            "%Y-%m-%d %H:%M"
        )

    return {
        "coin_id": coin_id,
        "currency": vs_currency.upper(),
        "current_price": round(current_price, 4),
        "change_24h": round(change_24h, 2) if change_24h is not None else None,
        "last_updated": last_updated_str,
        "min_price": round(min_price, 4),
        "max_price": round(max_price, 4),
        "avg_price": round(avg_price, 4),
        "period_change_pct": round(period_change_pct, 2),
        "days": days,
        "history": history,
    }


if __name__ == "__main__":
    app.run(debug=True)
