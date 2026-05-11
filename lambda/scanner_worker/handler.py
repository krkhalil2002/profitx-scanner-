import json
import boto3
import os
import uuid
import requests
from datetime import datetime

# -------------------------------------------------------
# WHAT IS THIS FILE?
# This is the Scanner Worker Lambda. Its job is to:
# 1. Receive a batch of stock symbols
# 2. Fetch market data for each symbol from the external API
# 3. Evaluate each symbol against your filter criteria
# 4. Write any matches to DynamoDB
# -------------------------------------------------------


# -------------------------------------------------------
# SECRETS MANAGER
# We never hardcode API keys in the code. Instead we pull
# them from AWS Secrets Manager at runtime. This is why
# your architecture doc says "no hardcoded secrets."
# -------------------------------------------------------
def get_api_key():
    client = boto3.client("secretsmanager")
    secret = client.get_secret_value(SecretId=os.environ["API_KEY_SECRET_NAME"])
    return json.loads(secret["SecretString"])["api_key"]


# -------------------------------------------------------
# FILTER CRITERIA
# These are your deterministic rules. A stock must pass
# ALL four filters to be considered a match.
# These values should match what you documented in your README.
# -------------------------------------------------------
FILTERS = {
    "min_gap_percent": 4.0,
    "min_volume": 500000,
    "min_rvol": 2.0,
    "max_float": 50000000,
}


# -------------------------------------------------------
# FETCH MARKET DATA
# This function calls the external market data API for a
# single symbol and returns the data we need.
# The fields returned must include: price, volume, float, rvol, gap %
# You will swap the URL and parsing logic here based on
# whichever API you choose (Polygon, Alpaca, etc.)
# -------------------------------------------------------
def fetch_market_data(symbol, api_key):
    url = f"https://api.yourprovider.com/v1/snapshot/{symbol}"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers, timeout=5)
    response.raise_for_status()  # throws an error if the request failed
    data = response.json()

    # Parse the fields out of the API response
    # These field names will change depending on your API provider
    return {
        "ticker": symbol,
        "price": data["price"],
        "volume": data["volume"],
        "rvol": data["relative_volume"],
        "float": data["float_shares"],
        "gap_percent": data["gap_percent"],
    }


# -------------------------------------------------------
# EVALUATE SYMBOL
# This is the core scanning logic. It takes a stock's data
# and checks it against every filter.
# Returns True if the stock passes all filters, False if not.
# This is what "deterministic rules" means — same input,
# same output, every single time.
# -------------------------------------------------------
def passes_filters(stock_data):
    if stock_data["gap_percent"] < FILTERS["min_gap_percent"]:
        return False
    if stock_data["volume"] < FILTERS["min_volume"]:
        return False
    if stock_data["rvol"] < FILTERS["min_rvol"]:
        return False
    if stock_data["float"] > FILTERS["max_float"]:
        return False
    return True


# -------------------------------------------------------
# WRITE TO DYNAMODB
# If a stock passes all filters, we store it as a scan result.
# The PK and SK format matches your architecture doc exactly:
#   PK = SCAN#<scanId>
#   SK = SYMBOL#<ticker>
# TTL is set so old records auto-expire and don't pile up.
# -------------------------------------------------------
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


# -------------------------------------------------------
# LAMBDA HANDLER
# This is the entry point AWS calls when the Lambda runs.
# The "event" contains the data passed in by the Orchestrator —
# specifically the scan_id and the list of symbols to evaluate.
# -------------------------------------------------------
def lambda_handler(event, context):
    # Pull the scan ID and symbol batch from the event payload
    scan_id = event["scan_id"]
    symbols = event["symbols"]  # e.g. ["AAPL", "TSLA", "NVDA"]

    # Connect to DynamoDB
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["DYNAMODB_TABLE_NAME"])

    # Get the API key from Secrets Manager
    api_key = get_api_key()

    results = []

    for symbol in symbols:
        try:
            # Step 1: Fetch market data for this symbol
            stock_data = fetch_market_data(symbol, api_key)

            # Step 2: Check if it passes all filters
            if passes_filters(stock_data):
                # Step 3: Write the match to DynamoDB
                write_result(table, scan_id, stock_data)
                results.append(symbol)

        except Exception as e:
            # If one symbol fails, log it and keep going
            # We don't want one bad API response to kill the whole batch
            print(f"ERROR processing {symbol}: {str(e)}")

    # Return how many symbols matched — the Orchestrator uses this
    # to update the resultCount on the Scan Job record
    return {
        "statusCode": 200,
        "matched_symbols": results,
        "matched_count": len(results),
    }