import os
os.environ["DYNAMODB_TABLE_NAME"] = "test-table"
os.environ["API_KEY_SECRET_NAME"] = "test-secret"

# Import the functions directly from handler
from handler import fetch_market_data, passes_filters

API_KEY = "qagSa9cppYO5CyRI5azXj49dOExX0jTe"  # paste your actual key

# Test with a few symbols
symbols = ["AAPL", "TSLA", "NVDA"]

for symbol in symbols:
    try:
        print(f"\nFetching {symbol}...")
        data = fetch_market_data(symbol, API_KEY)
        print(f"Data: {data}")
        
        passed = passes_filters(data)
        print(f"Passes filters: {passed}")
        
    except Exception as e:
        print(f"Error: {str(e)}")