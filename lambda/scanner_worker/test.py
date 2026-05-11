import requests

API_KEY = "qagSa9cppYO5CyRI5azXj49dOExX0jTe"
symbol = "AAPL"

url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
params = {"apiKey": API_KEY}

response = requests.get(url, params=params, timeout=5)
data = response.json()

print(data)