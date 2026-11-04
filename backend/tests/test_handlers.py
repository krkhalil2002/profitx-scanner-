import importlib.util
import json
import os

import boto3
import pytest
from moto import mock_aws

ROOT = os.path.join(os.path.dirname(__file__), "..", "functions")


def _load(name):
    spec = importlib.util.spec_from_file_location(f"{name}_handler", os.path.join(ROOT, name, "handler.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def handlers(monkeypatch):
    with mock_aws():
        ddb = boto3.client("dynamodb", region_name="us-east-1")
        ddb.create_table(
            TableName="t",
            BillingMode="PAY_PER_REQUEST",
            KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}, {"AttributeName": "sk", "KeyType": "RANGE"}],
            AttributeDefinitions=[{"AttributeName": n, "AttributeType": "S"} for n in ("pk", "sk", "gsi1pk", "gsi1sk")],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "gsi1",
                    "KeySchema": [{"AttributeName": "gsi1pk", "KeyType": "HASH"}, {"AttributeName": "gsi1sk", "KeyType": "RANGE"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
        )
        monkeypatch.setenv("TABLE_NAME", "t")
        monkeypatch.setenv("SYMBOLS", ",".join(f"SYM{i}" for i in range(60)))
        monkeypatch.setenv("DATA_PROVIDER", "mock")
        yield _load("scanner"), _load("results")


def api_event(body=None):
    return {"requestContext": {"authorizer": {"jwt": {"claims": {"sub": "user-1"}}}}, "body": body}


def test_scan_then_read_latest(handlers):
    scanner, results = handlers
    resp = scanner.handler(api_event(), None)
    assert resp["statusCode"] == 200
    scan = json.loads(resp["body"])
    assert scan["scan"]["scanned"] == 60
    assert scan["scan"]["triggered_by"] == "user-1"

    latest = json.loads(results.handler({}, None)["body"])
    assert latest["scan"]["scan_id"] == scan["scan"]["scan_id"]
    assert len(latest["results"]) == scan["scan"]["matched"]


def test_scheduled_event_works(handlers):
    scanner, _ = handlers
    resp = scanner.handler({"source": "schedule"}, None)
    assert json.loads(resp["body"])["scan"]["triggered_by"] == "schedule"


def test_bad_filter_rejected(handlers):
    scanner, _ = handlers
    assert scanner.handler(api_event('{"min_rvol": "abc"}'), None)["statusCode"] == 400
    assert scanner.handler(api_event('{"hack": 1}'), None)["statusCode"] == 400
    assert scanner.handler(api_event("not json"), None)["statusCode"] == 400


def test_empty_table_returns_empty(handlers):
    _, results = handlers
    assert json.loads(results.handler({}, None)["body"]) == {"scan": None, "results": []}
