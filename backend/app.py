"""Flask API for the US accidents Severity classifier.

Teaching/research prototype only. Not for operational, safety or insurance decisions.
Input validation is driven by backend/feature_schema.json.
"""
from pathlib import Path
import json
import math

import joblib
import pandas as pd
from flask import Flask, jsonify, request

BASE_DIR = Path(__file__).resolve().parent
bundle = joblib.load(BASE_DIR / "models" / "model_bundle.joblib")
pipeline = bundle["pipeline"]
FEATURES = bundle["features"]
TASK = bundle.get("task", "classification")
MODEL_VERSION = bundle.get("model_version", "1.0")

SCHEMA = json.loads((BASE_DIR / "feature_schema.json").read_text(encoding="utf-8"))
SPECS = {f["name"]: f for f in SCHEMA["features"]}
CLASSES = [int(c) for c in pipeline.classes_]
DISCLAIMER = SCHEMA["disclaimer"]

app = Flask(__name__)


def bad_request(error, field=None, detail=None, **extra):
    body = {"error": error}
    if field is not None:
        body["field"] = field
    if detail is not None:
        body["detail"] = detail
    body.update(extra)
    return jsonify(body), 400


def validate_value(name, value):
    """Return (converted_value, None) or (None, error_detail)."""
    spec = SPECS[name]
    kind = spec["kind"]
    if kind == "category":
        if not isinstance(value, str):
            return None, "must be a string"
        if value not in spec["options"]:
            return None, "unknown category value"
        return value, None
    if kind == "boolean":
        if isinstance(value, bool):
            return int(value), None
        if isinstance(value, int) and value in (0, 1):
            return value, None
        return None, "must be true/false (or 0/1)"
    # kind == "number"
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None, "must be a number"
    if not math.isfinite(value):
        return None, "must be a finite number"
    if spec.get("integer") and float(value) != int(value):
        return None, "must be an integer"
    if value < spec["min"] or value > spec["max"]:
        return None, f"must be between {spec['min']} and {spec['max']}"
    return value, None


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "features": len(FEATURES),
        "task": TASK,
        "model_version": MODEL_VERSION,
    })


@app.post("/predict")
def predict():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return bad_request("Expected a JSON object")

    missing = [f for f in FEATURES if f not in payload]
    extra = [k for k in payload if k not in FEATURES]
    if missing or extra:
        return bad_request("Input schema mismatch", missing=missing, extra=extra)

    row = {}
    for name in FEATURES:
        value, detail = validate_value(name, payload[name])
        if detail is not None:
            return bad_request("Invalid feature value", field=name, detail=detail)
        row[name] = value

    try:
        X = pd.DataFrame([row], columns=FEATURES)
        prediction = int(pipeline.predict(X)[0])
        proba = pipeline.predict_proba(X)[0]
        return jsonify({
            "prediction": prediction,
            "label": f"Severity {prediction}",
            "classes": CLASSES,
            "probabilities": [round(float(p), 6) for p in proba],
            "task": TASK,
            "model_version": MODEL_VERSION,
            "disclaimer": DISCLAIMER,
        })
    except Exception:
        app.logger.exception("Prediction failed")
        return jsonify({"error": "Prediction failed"}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
