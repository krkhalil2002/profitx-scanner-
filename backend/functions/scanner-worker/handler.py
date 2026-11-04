"""Runs a scan. Triggered by EventBridge Scheduler (market open) or POST /scans."""
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import boto3

from filters import DEFAULT_FILTERS, passes
from providers import get_provider

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Created once per cold start, then reused by every warm invocation.
TABLE = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
SYMBOLS = [s.strip().upper() for s in os.environ["SYMBOLS"].split(",") if s.strip()]
PROVIDER = get_provider()
TTL_SECONDS = 30 * 24 * 3600  # DynamoDB deletes items ~30 days after creation

FILTER_KEYS = set(DEFAULT_FILTERS)


def _dec(x):
    return Decimal(str(round(float(x), 4)))


def _store(d):
    """DynamoDB wants Decimal, not float."""
    return {k: (_dec(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v) for k, v in d.items()}


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


def _parse_filters(event):
    cfg = dict(DEFAULT_FILTERS)
    raw = event.get("body")
    if not raw:
        return cfg
    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError("Body must be valid JSON")
    if not isinstance(body, dict):
        raise ValueError("Body must be a JSON object")
    for key, value in body.items():
        if key not in FILTER_KEYS:
            raise ValueError(f"Unknown filter: {key}")
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"{key} must be a number")
        if number < 0:
            raise ValueError(f"{key} must be >= 0")
        cfg[key] = number
    return cfg


def handler(event, context):
    via_api = "requestContext" in event
    try:
        cfg = _parse_filters(event) if via_api else dict(DEFAULT_FILTERS)
    except ValueError as err:
        return _response(400, {"error": str(err)})

    triggered_by = "schedule"
    if via_api:
        claims = event["requestContext"].get("authorizer", {}).get("jwt", {}).get("claims", {})
        triggered_by = claims.get("sub", "unknown")

    scan_id = uuid.uuid4().hex[:12]
    created_at = datetime.now(timezone.utc).isoformat()
    expires_at = int(time.time()) + TTL_SECONDS

    results, errors = [], 0
    for symbol in SYMBOLS:
        try:
            data = PROVIDER.fetch(symbol)
        except Exception:
            errors += 1
            logger.exception("fetch failed for %s", symbol)
            continue
        matched, metrics = passes(data, cfg)
        if matched:
            results.append(
                {
                    "symbol": symbol,
                    "price": data["open"],
                    "gap_pct": round(metrics["gap_pct"], 2),
                    "volume": data["volume"],
                    "rvol": round(metrics["rvol"], 2),
                    "float": data["float"],
                }
            )

    meta = {
        "scan_id": scan_id,
        "created_at": created_at,
        "triggered_by": triggered_by,
        "scanned": len(SYMBOLS),
        "matched": len(results),
        "errors": errors,
        "filters": cfg,
    }

    with TABLE.batch_writer() as batch:
        batch.put_item(
            Item={
                "pk": f"SCAN#{scan_id}",
                "sk": "META",
                "gsi1pk": "SCANS",
                "gsi1sk": created_at,
                "expires_at": expires_at,
                **_store({k: v for k, v in meta.items() if k != "filters"}),
                "filters": _store(cfg),
            }
        )
        for r in results:
            batch.put_item(
                Item={"pk": f"SCAN#{scan_id}", "sk": f"RESULT#{r['symbol']}", "expires_at": expires_at, **_store(r)}
            )

    logger.info(json.dumps({"event": "scan_complete", **{k: v for k, v in meta.items() if k != "filters"}}))
    return _response(200, {"scan": meta, "results": results})
