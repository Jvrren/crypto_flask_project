print(">>> RUNNING app.py")
from flask import Flask, render_template, request
import requests


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/price", methods=["POST"])
def price():
    
    crypto = request.form.get("crypto")
    currency = request.form.get("currency")
    include_time = request.form.get("include_time")

    
    api_url = f"https://api.coinbase.com/v2/prices/{crypto}-{currency}/spot"

    
    response = requests.get(api_url)
    data = response.json()

    
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
