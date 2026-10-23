from pathlib import Path
import json
import requests

ROOT = Path(__file__).resolve().parent.parent
payload = json.loads((ROOT / "backend/test_payload.json").read_text(encoding="utf-8"))

session = requests.Session()
session.trust_env = False  # ignore system proxy settings for localhost
response = session.post("http://127.0.0.1:5000/predict", json=payload, timeout=10)

print("HTTP Status:", response.status_code)
print("Response:", response.json())
response.raise_for_status()
print("PASS: API request")
