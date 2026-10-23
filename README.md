# US Accident Severity Prediction

[![Full-stack CI](https://github.com/fasimalik908/accident-severity-cicd/actions/workflows/ci.yml/badge.svg)](https://github.com/fasimalik908/accident-severity-cicd/actions/workflows/ci.yml)
[![Deploy Angular to GitHub Pages](https://github.com/fasimalik908/accident-severity-cicd/actions/workflows/pages.yml/badge.svg)](https://github.com/fasimalik908/accident-severity-cicd/actions/workflows/pages.yml)

A full-stack machine learning lab project: a LightGBM classifier predicts the **Severity (1-4)** of a US traffic accident from 12 inputs known at the moment the accident happens. The model is served by a **Flask** REST API, used through an **Angular** form, tested and built by **GitHub Actions**, and the static Angular UI is deployed to **GitHub Pages**.

> **Teaching/research prototype only.** This model is not accurate enough for real use and must not be used for operational, safety or insurance decisions. See [Limitations](#limitations).

## Live links

| What | Link |
|---|---|
| Repository | https://github.com/fasimalik908/accident-severity-cicd |
| GitHub Pages (static UI) | https://fasimalik908.github.io/accident-severity-cicd/ |
| GitHub Actions runs | https://github.com/fasimalik908/accident-severity-cicd/actions |

The Pages site shows the form only. The **Predict severity** button is disabled there and a notice explains that predictions need the Flask API running locally (see [Running locally](#running-locally)).

## Architecture

```text
                     LOCAL MACHINE (full stack)
 +-------------------------------+   /api/*   +------------------------------+
 | Angular dev server :4200      | ---------> | Flask API :5000              |
 | (ng serve + proxy.conf.json)  |  (proxy    |  GET  /health                |
 | form built from               |  strips    |  POST /predict               |
 | backend/feature_schema.json   |  /api)     |  validates with the schema   |
 +-------------------------------+            |  model_bundle.joblib         |
                                              |  (sklearn Pipeline + LGBM)   |
                                              +------------------------------+

                     GITHUB
 push to main --> "Full-stack CI": backend job (pytest) + frontend job (Vitest, build)
              \-> "Deploy Angular to GitHub Pages": Vitest, ng build --> GitHub Pages

 GitHub Pages = static Angular files only (no Python, no model, no API).
```

`backend/feature_schema.json` is the single contract between the two halves: Flask uses it to validate requests, and the Angular app imports the same file at build time to generate its form fields, so the two cannot drift apart.

## Problem

Multiclass classification of the `Severity` column (1 = least impact on traffic, 4 = most) of US traffic accidents.

Only information available **at accident onset** is used. Columns that are only known after the accident is over (`End_Time`, `Duration_Min`, `End_Lat`, `End_Lng`, `Distance(mi)`) are deliberately excluded, because using them would leak the outcome into the inputs.

## Data provenance

- Source: the public Kaggle **"US Accidents"** dataset (Sobhan Moosavi et al.).
- We used a 300,000-row cleaned and feature-engineered sample, `us_accidents_300k_clean_engineered.csv`, produced in an earlier research project of ours.
- The CSV (134 MB) is **not** included in this repository. Only `data/sample_inputs.csv` (3 example rows) is committed.
- Class counts in the 300k sample:

| Severity | Rows | Share |
|---|---:|---:|
| 1 | 2,619 | 0.9% |
| 2 | 238,905 | 79.6% |
| 3 | 50,617 | 16.9% |
| 4 | 7,859 | 2.6% |

## Model and preprocessing

A single scikit-learn `Pipeline`, saved as `backend/models/model_bundle.joblib` (3.15 MB; keys `pipeline`, `features`, `task`, `model_version = "1.0"`):

1. `ColumnTransformer`
   - `OneHotEncoder(handle_unknown="ignore")` on `Source`, `State`, `Weather_Condition`
   - numeric columns passed through unchanged
   - boolean columns passed through as 0/1
2. `LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=63, class_weight="balanced", random_state=42)`

Data split: stratified 80/20 train/test (240,000 / 60,000 rows), `random_state=42`. All preprocessing is fitted on the training split only, inside the pipeline. Training script: `notebooks/train_small_lgbm.py`.

## Input features

All 12 fields are required. The API rejects missing or extra fields, unknown categories and out-of-range values with HTTP 400.

| Name | Type | Allowed values / range |
|---|---|---|
| `Source` | category | `Source1`, `Source2`, `Source3` |
| `State` | category | 49 two-letter codes seen in training (48 states + `DC`; no `AK`, `HI`) |
| `Hour` | integer | 0-23 |
| `Day_of_Week` | integer | 0-6 (0 = Monday ... 6 = Sunday) |
| `Temperature(F)` | number | -50 to 130 |
| `Humidity(%)` | number | 0 to 100 |
| `Visibility(mi)` | number | 0 to 100 |
| `Wind_Speed(mph)` | number | 0 to 200 |
| `Weather_Condition` | category | 101 values seen in training (e.g. `Fair`, `Cloudy`, `Light Rain`, `Fog`) |
| `Crossing` | boolean | `true` / `false` |
| `Junction` | boolean | `true` / `false` |
| `Traffic_Signal` | boolean | `true` / `false` |

The full lists of allowed values are in [`backend/feature_schema.json`](backend/feature_schema.json).

## Results

Test split: 60,000 rows. Full report: [`docs/evidence/model_metrics.txt`](docs/evidence/model_metrics.txt).

| Metric | Model | Majority-class baseline (always Severity 2) |
|---|---:|---:|
| Accuracy | 0.5681 | **0.7964** |
| Macro-F1 | **0.3826** | 0.2217 |
| Balanced accuracy | **0.6509** | 0.2500 |
| Weighted F1 | 0.6353 | 0.7061 |

Baseline macro-F1, balanced accuracy and weighted F1 are computed from the test class counts (47,781 of 60,000 rows are Severity 2).

Per class (test split):

| Severity | Precision | Recall | F1 | Test rows |
|---|---:|---:|---:|---:|
| 1 | 0.067 | 0.601 | 0.121 | 524 |
| 2 | 0.953 | 0.516 | 0.669 | 47,781 |
| 3 | 0.451 | 0.794 | 0.575 | 10,123 |
| 4 | 0.094 | 0.693 | 0.165 | 1,572 |

## Limitations

- **Accuracy is below the trivial baseline.** Always predicting Severity 2 gives 0.7964 accuracy; the model gives 0.5681. `class_weight="balanced"` deliberately trades overall accuracy for recall on the rare classes. Macro-F1 and balanced accuracy are the more honest headline metrics for this imbalanced task.
- **Rare classes are predicted poorly.** Severity 1 precision is 0.067 and Severity 4 precision is 0.094: most predictions of 1 or 4 are wrong.
- **`Source` is a data-provider field.** It may act as a proxy for how severity was recorded by each provider (a dataset artifact) rather than a causal factor.
- **Closed category lists.** `State` and `Weather_Condition` accept only values seen in training; anything else is rejected with HTTP 400.
- **Static hosting only.** GitHub Pages serves the Angular UI without a backend, so predictions require running Flask and Angular locally.
- **Prototype.** Built for teaching and research; not for operational, safety or insurance decisions.

## Versions

| Tool | Version |
|---|---|
| OS (development) | Windows 11 Home 10.0.22631 |
| Python | 3.14.0 (project `.venv`) |
| Node.js / npm | v22.23.1 / 10.9.8 |
| Git | 2.54.0 |
| Angular CLI / @angular/core | 22.2.4 / 22.2.3 (engines: node `^22.22.3 \|\| ^24.15.0 \|\| >=26`) |
| Flask | 3.1.3 |
| pandas / numpy | 3.1.0 / 2.5.4 |
| scikit-learn | 1.9.1 |
| lightgbm | 4.7.0 |
| joblib | 1.6.0 |
| pytest | 9.1.1 |

All Python pins are in `backend/requirements.txt`; the frontend lock file is `frontend/package-lock.json`. Recorded environment: `docs/environment.txt`. On the development PC the Angular CLI is installed locally under `D:\.lab-cache\npm-global` rather than globally; `npx ng ...` from the `frontend` folder works everywhere.

## Project structure

```text
accident-severity-cicd/
├── .github/workflows/
│   ├── ci.yml                 # Full-stack CI (backend + frontend jobs)
│   └── pages.yml              # Deploy Angular to GitHub Pages
├── backend/
│   ├── app.py                 # Flask API (/health, /predict)
│   ├── feature_schema.json    # shared input contract (API + UI)
│   ├── models/model_bundle.joblib
│   ├── requirements.txt
│   ├── test_payload.json      # example request body
│   └── tests/                 # pytest: test_api.py, test_structure.py
├── data/sample_inputs.csv     # 3 example rows (full dataset not included)
├── docs/
│   ├── demo_cheatsheet.md     # lab demo steps (edit -> push -> CI/CD -> Pages)
│   ├── environment.txt
│   ├── troubleshooting.md
│   └── evidence/              # metrics, screenshot, run links
├── frontend/                  # Angular 22 app
│   ├── proxy.conf.json        # /api -> http://127.0.0.1:5000
│   └── src/app/               # app.ts, app.html, app.css, service, specs
├── notebooks/train_small_lgbm.py
└── README.md
```

## Setup

Prerequisites: Python 3.14, Node.js 22 (with npm), Git. Commands are for Windows PowerShell.

```powershell
git clone https://github.com/fasimalik908/accident-severity-cicd.git
cd accident-severity-cicd

# Backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt

# Frontend
cd frontend
npm ci
cd ..
```

## Running locally

Use three PowerShell terminals. Start Flask first and wait until `/health` answers before starting Angular. (Paths below use the development folder `D:\ML_Project`; adjust to your clone.)

**Terminal 1 - Flask API (port 5000)**

```powershell
cd D:\ML_Project
.\.venv\Scripts\Activate.ps1
$env:OPENBLAS_NUM_THREADS='1'; $env:OMP_NUM_THREADS='1'
python backend\app.py
```

**Terminal 2 - Angular dev server with API proxy (port 4200)**

```powershell
cd D:\ML_Project\frontend
npx ng serve --proxy-config proxy.conf.json --poll 2000
```

Then open http://localhost:4200, click **Fill sample values** (or fill the form) and click **Predict severity**. The browser calls `/api/predict`; the dev proxy forwards it to `http://127.0.0.1:5000/predict`.

**Terminal 3 - checks, tests and git**

```powershell
cd D:\ML_Project
curl.exe -s -m 5 http://127.0.0.1:5000/health
```

Notes for the low-memory development PC:

- The two `*_NUM_THREADS` variables stop OpenBLAS from failing with `Memory allocation still failed` when memory is tight.
- `--poll 2000` is needed because the native file watcher makes `ng serve` exit silently on this machine. On other machines `npx ng serve --proxy-config proxy.conf.json` is enough.

## Testing

```powershell
# Backend: 13 tests (tests/test_api.py 12 + tests/test_structure.py 1)
cd D:\ML_Project
.\.venv\Scripts\Activate.ps1
python -m pytest -q backend\tests

# Frontend: 9 Vitest tests, then a production build
cd D:\ML_Project\frontend
npm test -- --watch=false
npm run build
```

## API

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Status, number of features, task, model version |
| POST | `/predict` | JSON object with all 12 features; returns the predicted class and probabilities |

Request rules: categories are strings, numbers are JSON numbers, booleans are `true`/`false`. Invalid input returns HTTP 400 with `error` and, where relevant, `field`, `detail`, `missing`, `extra`.

```powershell
curl.exe -s http://127.0.0.1:5000/health
# {"features":12,"model_version":"1.0","status":"ok","task":"classification"}

curl.exe -s -X POST http://127.0.0.1:5000/predict -H "Content-Type: application/json" --data-binary "@backend/test_payload.json"
```

Example request (`backend/test_payload.json`):

```json
{
  "Source": "Source2", "State": "PA", "Hour": 17, "Day_of_Week": 1,
  "Temperature(F)": 36.0, "Humidity(%)": 59.0, "Visibility(mi)": 10.0,
  "Wind_Speed(mph)": 9.0, "Weather_Condition": "Fair",
  "Crossing": false, "Junction": true, "Traffic_Signal": false
}
```

Response shape (the numbers only illustrate the format):

```json
{
  "prediction": 2,
  "label": "Severity 2",
  "classes": [1, 2, 3, 4],
  "probabilities": [0.1, 0.5, 0.3, 0.1],
  "task": "classification",
  "model_version": "1.0",
  "disclaimer": "Teaching/research prototype only. Not for operational, safety or insurance decisions."
}
```

## CI/CD

Both workflows run on every push to `main` and can also be started manually (`workflow_dispatch`).

**`.github/workflows/ci.yml` - "Full-stack CI"** (also runs on pull requests to `main`)

- `backend` job: Ubuntu, Python 3.14, `pip install -r backend/requirements.txt`, `python -m pytest -q backend/tests` (API, validation and model-loading tests).
- `frontend` job: Ubuntu, Node 22, `npm ci`, `npm test -- --watch=false`, `npm run build`, then uploads `frontend/dist/` as the `angular-build` artifact.

**`.github/workflows/pages.yml` - "Deploy Angular to GitHub Pages"**

- `deploy` job: Node 22, `npm ci`, `npm test -- --watch=false` (the unit tests run again before building, so a failing test blocks the deployment), `npx ng build --configuration production --base-href /accident-severity-cicd/`, uploads `frontend/dist/frontend/browser` as the Pages artifact and deploys it with `actions/deploy-pages`.
- Repository setting required: **Settings > Pages > Source = GitHub Actions**.

One-time prerequisite for pushing workflow files with the GitHub CLI: the login needs the `workflow` scope.

```powershell
gh auth refresh -h github.com -s workflow   # approve in the browser
gh auth status                              # scopes should include 'workflow'
```

## Retraining

The dataset is not in the repository, so pass the path to your copy of the CSV:

```powershell
.\.venv\Scripts\Activate.ps1
python notebooks\train_small_lgbm.py <path-to-csv>
```

This rewrites `backend/models/model_bundle.joblib`. If the category values change, update `backend/feature_schema.json` as well, then rerun the backend and frontend tests.

## Troubleshooting and demo

- Errors met during development and their fixes: [`docs/troubleshooting.md`](docs/troubleshooting.md)
- Lab demo steps (edit, push, CI/CD, Pages): [`docs/demo_cheatsheet.md`](docs/demo_cheatsheet.md)
- Evidence (metrics, screenshot, run links): [`docs/evidence/`](docs/evidence/README.md)

## Disclaimer

This project is a teaching/research prototype built on a public dataset with known biases and recording artifacts. Its predictions are unreliable, especially for Severity 1 and 4. Do not use it for operational, safety, emergency-response or insurance decisions.
