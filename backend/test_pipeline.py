from pathlib import Path
import json
import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
bundle = joblib.load(ROOT / "backend/models/model_bundle.joblib")
pipeline = bundle["pipeline"]
features = bundle["features"]
schema = json.loads((ROOT / "backend/feature_schema.json").read_text(encoding="utf-8"))
boolean_features = [f["name"] for f in schema["features"] if f["kind"] == "boolean"]

payload = json.loads((ROOT / "backend/test_payload.json").read_text(encoding="utf-8"))
assert set(features) == set(payload), "Payload keys do not match model features"

# Same conversion as app.py: booleans -> int 0/1 before calling the pipeline.
row = {name: payload[name] for name in features}
for name in boolean_features:
    row[name] = int(row[name])
X = pd.DataFrame([row], columns=features)

print("Prediction:", pipeline.predict(X).tolist())
print("Probabilities:", pipeline.predict_proba(X).round(4).tolist())
print("PASS: local inference")
