from pathlib import Path
import json
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app import app, FEATURES  # noqa: E402


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def payload():
    return json.loads((ROOT / "backend" / "test_payload.json").read_text(encoding="utf-8"))


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["features"] == len(FEATURES)
    assert body["task"] == "classification"
    assert body["model_version"] == "1.0"


def test_predict_valid(client, payload):
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    body = response.get_json()
    assert body["classes"] == [1, 2, 3, 4]
    assert body["prediction"] in body["classes"]
    assert body["label"] == f"Severity {body['prediction']}"
    assert len(body["probabilities"]) == 4
    assert abs(sum(body["probabilities"]) - 1.0) < 1e-3


def test_predict_accepts_int_booleans(client, payload):
    payload["Crossing"] = 1
    payload["Junction"] = 0
    response = client.post("/predict", json=payload)
    assert response.status_code == 200


def test_predict_missing_feature(client, payload):
    payload.pop(FEATURES[0])
    response = client.post("/predict", json=payload)
    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "Input schema mismatch"
    assert FEATURES[0] in body["missing"]


def test_predict_invalid_json(client):
    response = client.post("/predict", data="{not json", content_type="application/json")
    assert response.status_code == 400
    assert response.get_json()["error"] == "Expected a JSON object"


def test_predict_non_object_json(client):
    response = client.post("/predict", json=[1, 2, 3])
    assert response.status_code == 400


def test_predict_out_of_range(client, payload):
    payload["Humidity(%)"] = 150
    response = client.post("/predict", json=payload)
    assert response.status_code == 400
    assert response.get_json()["field"] == "Humidity(%)"


def test_predict_non_integer_hour(client, payload):
    payload["Hour"] = 5.5
    response = client.post("/predict", json=payload)
    assert response.status_code == 400
    assert response.get_json()["field"] == "Hour"


def test_predict_bool_for_number(client, payload):
    payload["Temperature(F)"] = True
    response = client.post("/predict", json=payload)
    assert response.status_code == 400


def test_predict_nan_rejected(client, payload):
    payload["Temperature(F)"] = float("nan")
    response = client.post("/predict", data=json.dumps(payload),
                           content_type="application/json")
    assert response.status_code == 400


def test_predict_unknown_category(client, payload):
    payload["State"] = "ZZ"
    response = client.post("/predict", json=payload)
    assert response.status_code == 400
    assert response.get_json()["field"] == "State"


def test_predict_extra_field(client, payload):
    payload["Distance(mi)"] = 1.0
    response = client.post("/predict", json=payload)
    assert response.status_code == 400
    assert "Distance(mi)" in response.get_json()["extra"]
