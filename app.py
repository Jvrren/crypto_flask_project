print(">>> RUNNING app.py")
from flask import Flask, render_template, request
import requests


app = Flask(__name__)

# Home page with form
@app.route("/")
def index():
    return render_template("index.html")

# Form submission route
@app.route("/price", methods=["POST"])
def price():
    # Get user inputs
    crypto = request.form.get("crypto")
    currency = request.form.get("currency")
    include_time = request.form.get("include_time")

    # Build API URL
    api_url = f"https://api.coinbase.com/v2/prices/{crypto}-{currency}/spot"

    # Fetch data
    response = requests.get(api_url)
    data = response.json()

    # Process data
    if "data" in data:
        price = data["data"]["amount"]
    else:
        price = "Error: Could not fetch price."

    return render_template(
        "results.html",
        crypto=crypto,
        currency=currency,
        price=price,
        include_time=include_time
    )

if __name__ == "__main__":
    app.run(debug=True)
