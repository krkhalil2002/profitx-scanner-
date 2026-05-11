import json
import boto3
import os
import requests
from datetime import datetime

def get_api_key():
    client = boto3.client("secretsmanager")
    secret = client.get_secret_value(SecretId=os.environ["API_KEY_SECRET_NAME"])
    return json.loads(secret["SecretString"])["api_key"]

FILTERS = {
    "min_gap_percent": 4.0,
    "min_volume": 500000,
    "min_rvol": 2.0,
    "max_float": 50000000,
}

def fetch_market_data(symbol, api_key):
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
    params = {"apiKey": api_key}
    response = requests.get(url, params=params, timeout=5)
    response.raise_for_status()
    data = response.json()
    result = data["results"][0]
    prev_close = result["c"]
    todays_open = result["o"]
    volume = result["v"]
    gap_percent = ((todays_open - prev_close) / prev_close) * 100
    return {
        "ticker": symbol,
        "price": result["c"],
        "volume": volume,
        "rvol": 1.0,
        "float": 0,
        "gap_percent": gap_percent,
    }

def passes_filters(stock_data):
    if stock_data["gap_percent"] < FILTERS["min_gap_percent"]:
        return False
    if stock_data["volume"] < FILTERS["min_volume"]:
        return False
    if stock_data["rvol"] < FILTERS["min_rvol"]:
        return False
    # Float filter disabled — Polygon free tier does not return float data
    # if stock_data["float"] > FILTERS["max_float"]:
    #     return False
    return True

def write_result(table, scan_id, stock_data):
    table.put_item(
        Item={
            "PK": f"SCAN#{scan_id}",
            "SK": f"SYMBOL#{stock_data['ticker']}",
            "ticker": stock_data["ticker"],
            "scanId": scan_id,
            "timestamp": datetime.utcnow().isoformat(),
            "price": str(stock_data["price"]),
            "volume": stock_data["volume"],
            "rvol": str(stock_data["rvol"]),
            "float": stock_data["float"],
            "gapPercent": str(stock_data["gap_percent"]),
        }
    )

def lambda_handler(event, context):
    scan_id = event["scan_id"]
    symbols = event["symbols"]
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["DYNAMODB_TABLE_NAME"])
    api_key = get_api_key()
    results = []
    for symbol in symbols:
        try:
            stock_data = fetch_market_data(symbol, api_key)
            if passes_filters(stock_data):
                write_result(table, scan_id, stock_data)
                results.append(symbol)
        except Exception as e:
            print(f"ERROR processing {symbol}: {str(e)}")
    return {
        "statusCode": 200,
        "matched_symbols": results,
        "matched_count": len(results),
    }
