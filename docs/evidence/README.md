# Evidence

Supporting files for the lab report.

| File | What it shows |
|---|---|
| `local_prediction.png` | Screenshot of a local end-to-end prediction: Angular dev server on http://localhost:4200 calling the Flask API on port 5000 through the dev proxy, with the predicted Severity, class probabilities and disclaimer. |
| `model_metrics.txt` | Test-split metrics of the LightGBM model (model_version 1.0): accuracy, macro-F1, balanced accuracy, weighted F1, per-class classification report, confusion matrix, and the comparison with the majority-class baseline. |

## GitHub Actions runs

Workflows: "Full-stack CI" (`.github/workflows/ci.yml`) and "Deploy Angular to GitHub Pages" (`.github/workflows/pages.yml`). All runs: https://github.com/fasimalik908/accident-severity-cicd/actions

| Workflow | Commit | Run URL | Result |
|---|---|---|---|
| Full-stack CI | 05fba81 Add CI and GitHub Pages workflows | https://github.com/fasimalik908/accident-severity-cicd/actions/runs/40125926824 | success (backend: 13 pytest passed; frontend: 9 unit tests passed, build, artifact `angular-build`) |
| Deploy Angular to GitHub Pages | 05fba81 Add CI and GitHub Pages workflows | https://github.com/fasimalik908/accident-severity-cicd/actions/runs/40125926717 | success (first deployment) |
| Full-stack CI | 4cfd8ff Update heading text | https://github.com/fasimalik908/accident-severity-cicd/actions/runs/40126357931 | success |
| Deploy Angular to GitHub Pages | 4cfd8ff Update heading text | https://github.com/fasimalik908/accident-severity-cicd/actions/runs/40126357736 | success (live site shows the updated heading) |

The 4cfd8ff runs are a rehearsal of the lab demo: edit the `<h1>` in `frontend/src/app/app.html`, commit, push, and both workflows rebuild and redeploy the site.

Live site: https://fasimalik908.github.io/accident-severity-cicd/ (static UI only; the Predict button is disabled there with a notice).
