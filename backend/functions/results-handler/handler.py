"""GET /scans/latest: return the most recent scan and its results (read-only)."""
import json
import logging
import os
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])


def _json_default(o):
    if isinstance(o, Decimal):
        return int(o) if o == o.to_integral_value() else float(o)
    raise TypeError(type(o))


def _response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=_json_default),
    }


def _clean(item):
    return {k: v for k, v in item.items() if k not in ("pk", "sk", "gsi1pk", "gsi1sk", "expires_at")}


def handler(event, context):
    latest = TABLE.query(
        IndexName="gsi1",
        KeyConditionExpression=Key("gsi1pk").eq("SCANS"),
        ScanIndexForward=False,  # newest first
        Limit=1,
    )["Items"]
    if not latest:
        return _response(200, {"scan": None, "results": []})

    meta = latest[0]
    rows = TABLE.query(
        KeyConditionExpression=Key("pk").eq(meta["pk"]) & Key("sk").begins_with("RESULT#")
    )["Items"]
    logger.info(json.dumps({"event": "results_read", "scan_id": meta["scan_id"], "rows": len(rows)}))
    results = sorted((_clean(r) for r in rows), key=lambda r: r["gap_pct"], reverse=True)
    return _response(200, {"scan": _clean(meta), "results": results})
