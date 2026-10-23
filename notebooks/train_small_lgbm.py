"""Train the small LightGBM pipeline used by the Flask API.

TEACHING / RESEARCH PROTOTYPE ONLY - not for operational, safety or insurance decisions.

Uses only inputs known at accident onset (no End_Time, Duration_Min,
End_Lat, End_Lng or Distance(mi)). All preprocessing is fitted inside the
sklearn Pipeline on the training split only.

Run from the project root:
    python notebooks\\train_small_lgbm.py [path\\to\\us_accidents_300k_clean_engineered.csv]
"""
from pathlib import Path
import json
import sys

import joblib
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (accuracy_score, balanced_accuracy_score,
                             classification_report, confusion_matrix, f1_score,
                             precision_recall_fscore_support)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = Path("C:/Users/MALIK/Desktop/US-Accidents-ML-Research/data/"
                    "processed/us_accidents_300k_clean_engineered.csv")
DATA = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DATA
MODELS = ROOT / "backend" / "models"

TARGET = "Severity"
FEATURES = ["Source", "State", "Hour", "Day_of_Week", "Temperature(F)",
            "Humidity(%)", "Visibility(mi)", "Wind_Speed(mph)",
            "Weather_Condition", "Crossing", "Junction", "Traffic_Signal"]
CATEGORICAL = ["Source", "State", "Weather_Condition"]
NUMERIC = ["Hour", "Day_of_Week", "Temperature(F)", "Humidity(%)",
           "Visibility(mi)", "Wind_Speed(mph)"]
BOOLEAN = ["Crossing", "Junction", "Traffic_Signal"]  # cast to int 0/1

LABELS = {
    "Source": "Data source", "State": "State",
    "Hour": "Hour of day (0-23)", "Day_of_Week": "Day of week (0=Mon ... 6=Sun)",
    "Temperature(F)": "Temperature (F)", "Humidity(%)": "Humidity (%)",
    "Visibility(mi)": "Visibility (mi)", "Wind_Speed(mph)": "Wind speed (mph)",
    "Weather_Condition": "Weather condition", "Crossing": "Crossing nearby",
    "Junction": "Junction nearby", "Traffic_Signal": "Traffic signal nearby",
}
RANGES = {
    "Hour": [0, 23], "Day_of_Week": [0, 6], "Temperature(F)": [-50, 130],
    "Humidity(%)": [0, 100], "Visibility(mi)": [0, 100],
    "Wind_Speed(mph)": [0, 200],
}
INTEGER = ["Hour", "Day_of_Week"]

df = pd.read_csv(DATA, usecols=FEATURES + [TARGET])
for col in BOOLEAN:
    df[col] = df[col].astype(int)
X = df[FEATURES]
y = df[TARGET]
print("Rows:", len(df), "Class counts:", y.value_counts().sort_index().to_dict())

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42)

# Sparse one-hot output (the default) keeps memory low.
preprocess = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
    ("num", "passthrough", NUMERIC + BOOLEAN),
])
pipeline = Pipeline([
    ("preprocess", preprocess),
    ("model", LGBMClassifier(n_estimators=300, learning_rate=0.05,
                             num_leaves=63, class_weight="balanced",
                             random_state=42, n_jobs=2, verbose=-1)),
])
pipeline.fit(X_train, y_train)

pred = pipeline.predict(X_test)
metrics = {
    "accuracy": round(float(accuracy_score(y_test, pred)), 4),
    "macro_f1": round(float(f1_score(y_test, pred, average="macro")), 4),
    "balanced_accuracy": round(float(balanced_accuracy_score(y_test, pred)), 4),
    "weighted_f1": round(float(f1_score(y_test, pred, average="weighted")), 4),
}
report = classification_report(y_test, pred, digits=3)
cm = confusion_matrix(y_test, pred, labels=[1, 2, 3, 4])
prec, _, f1s, _ = precision_recall_fscore_support(y_test, pred, labels=[1, 2, 3, 4],
                                                  zero_division=0)
n_major = int((y_test == 2).sum())
baseline = n_major / len(y_test)  # always predicting Severity 2
print("Test metrics:", metrics, "Majority baseline:", round(baseline, 4))
print(report)
print("Confusion matrix (rows=true 1-4, cols=pred 1-4):")
print(cm)

EVIDENCE = ROOT / "docs" / "evidence"
EVIDENCE.mkdir(parents=True, exist_ok=True)
lines = [
    "Model metrics - LightGBM Severity classifier, model_version 1.0",
    "Teaching/research prototype only. Not for operational, safety or insurance decisions.",
    "",
    f"Data: {DATA.name} ({len(df)} rows)",
    "Split: stratified 80/20 train/test, random_state=42",
    f"Train rows: {len(X_train)}  Test rows: {len(X_test)}",
    "Features: " + ", ".join(FEATURES),
    "Model: OneHotEncoder(sparse, handle_unknown=ignore) + LGBMClassifier("
    "n_estimators=300, learning_rate=0.05, num_leaves=63, class_weight=balanced, "
    "random_state=42)",
    "",
    "Test-split metrics:",
] + [f"  {k}: {v}" for k, v in metrics.items()] + [
    "",
    "Classification report (test split):",
    report,
    "Confusion matrix (rows = true Severity 1-4, cols = predicted 1-4):",
    str(cm),
    "",
    "Note on these results:",
    f"- Test accuracy {metrics['accuracy']:.4f} is BELOW the majority-class baseline of "
    f"{baseline:.4f} (always predicting Severity 2: {n_major} of {len(y_test)} test rows).",
    f"- Severity 1 and Severity 4 are predicted poorly: Severity 1 precision {prec[0]:.3f} / "
    f"F1 {f1s[0]:.3f}, Severity 4 precision {prec[3]:.3f} / F1 {f1s[3]:.3f}.",
    "  Most predictions of class 1 or 4 are wrong.",
    "- class_weight=balanced raises recall on the rare classes at the cost of overall accuracy.",
    f"- Macro-F1 {metrics['macro_f1']:.4f} is the more honest headline metric for this "
    "imbalanced task.",
    "- Teaching/research prototype only. Not for operational, safety or insurance decisions.",
]
(EVIDENCE / "model_metrics.txt").write_text("\n".join(lines) + "\n",
                                                 encoding="utf-8")

MODELS.mkdir(parents=True, exist_ok=True)
bundle = {
    "pipeline": pipeline,
    "features": FEATURES,
    "task": "classification",
    "model_version": "1.0",
}
joblib.dump(bundle, MODELS / "model_bundle.joblib", compress=3)

# Contract file used by Flask validation and the Angular form.
schema_features = []
for name in FEATURES:
    item = {"name": name, "label": LABELS[name]}
    if name in CATEGORICAL:
        item["kind"] = "category"
        item["options"] = sorted(str(v) for v in X_train[name].unique())
    elif name in BOOLEAN:
        item["kind"] = "boolean"
    else:
        item["kind"] = "number"
        item["min"], item["max"] = RANGES[name]
        if name in INTEGER:
            item["integer"] = True
    schema_features.append(item)
schema = {
    "model_version": "1.0",
    "task": "classification",
    "target": TARGET,
    "classes": [int(c) for c in pipeline.classes_],
    "disclaimer": "Teaching/research prototype only. Not for operational, "
                  "safety or insurance decisions.",
    "features": schema_features,
    "test_metrics": metrics,
}
(ROOT / "backend" / "feature_schema.json").write_text(
    json.dumps(schema, indent=2), encoding="utf-8")

# Three test-set records (no target); booleans written back as True/False.
(ROOT / "data").mkdir(exist_ok=True)
sample = X_test.head(3).copy()
for col in BOOLEAN:
    sample[col] = sample[col].astype(bool)
sample.to_csv(ROOT / "data" / "sample_inputs.csv", index=False)

first = X_test.iloc[[0]]
print("X_test.iloc[0] prediction:", pipeline.predict(first).tolist(),
      "proba:", pipeline.predict_proba(first).round(4).tolist())
size_mb = (MODELS / "model_bundle.joblib").stat().st_size / (1024 * 1024)
print(f"Saved model_bundle.joblib ({size_mb:.2f} MB)")
