# Lab demo cheat sheet

Demo goal: edit an HTML/CSS/TS file, push it, show both workflows green on GitHub Actions, and show the updated GitHub Pages site.

- Repository: https://github.com/fasimalik908/accident-severity-cicd
- Actions: https://github.com/fasimalik908/accident-severity-cicd/actions
- Pages: https://fasimalik908.github.io/accident-severity-cicd/

All commands are PowerShell, starting from `D:\ML_Project`.

## Before the demo

```powershell
cd D:\ML_Project
gh auth status          # logged in as fasimalik908; scopes include 'workflow'
git status              # must say: nothing to commit, working tree clean
git pull                # make sure local main matches GitHub
```

If `workflow` is missing from the scopes: `gh auth refresh -h github.com -s workflow` and approve in the browser.

Open these tabs in advance: the Actions page, the Pages site, and **Settings > Pages** (Source = GitHub Actions).

## Main demo: HTML edit

1. Open `frontend/src/app/app.html` and change the `<h1>` text.

   ```html
   <h1>Accident Severity Demo - Updated in Lab</h1>
   ```

   Any text is fine. Keep it as a single, non-empty `<h1>` element: the unit test in `app.spec.ts` checks exactly that.

2. Optional quick local check (about 1 minute):

   ```powershell
   cd frontend; npm run build; cd ..
   ```

3. Commit and push:

   ```powershell
   git add .
   git commit -m "Update heading text"
   git push
   ```

4. Watch the runs:

   ```powershell
   gh run list --limit 4
   gh run watch            # choose the "Full-stack CI" run, then repeat for the Pages run
   ```

5. Open https://fasimalik908.github.io/accident-severity-cicd/ and hard refresh with **Ctrl+F5**. The new heading should appear.

Expected time from `git push` to the updated site: about 2-4 minutes.

## Where to look on GitHub

| Place | What to show |
|---|---|
| Actions tab > **Full-stack CI** | Two green jobs: `backend` (pytest) and `frontend` (npm ci, Vitest, build, artifact `angular-build`) |
| Actions tab > **Deploy Angular to GitHub Pages** | Green `deploy` job (npm ci, unit tests, production build, deploy); the run summary shows the Pages URL |
| Settings > Pages | Source = GitHub Actions; link to the live site |
| Commit list / README badges | The pushed commit with green checks |

## What to show on the Pages site

- The heading change is visible.
- All 12 input fields render (dropdowns built from `backend/feature_schema.json`).
- **Fill sample values** works; the **Predict severity** button is disabled.
- The yellow notice says the site hosts only the static UI and predictions need the Flask API running locally.

## Variants

**CSS edit** - `frontend/src/app/app.css`, for example the heading color:

```css
.page-header h1 {
  margin: 0 0 0.25rem;
  font-size: 1.8rem;
  color: #b03a2e;
}
```

Commit message: `git commit -m "Change heading color"`.

**TS edit** - `frontend/src/app/app.ts`, add a property to the `App` class next to the other `readonly` fields:

```ts
protected readonly demoNote = 'Deployed automatically by GitHub Actions';
```

and show it in `app.html` under the subtitle:

```html
<p class="subtitle">{{ demoNote }}</p>
```

Commit message: `git commit -m "Add demo note"`. Then push and watch the runs exactly as above.

## If a run fails

1. Open the failed run in the Actions tab, click the red job, expand the red step and read the log.
2. Fix the problem locally and check it:

   ```powershell
   cd D:\ML_Project\frontend
   npm test -- --watch=false
   npm run build
   ```

   (Backend: `cd D:\ML_Project; .\.venv\Scripts\Activate.ps1; python -m pytest -q backend\tests`.)
3. Commit and push a new commit:

   ```powershell
   git add .
   git commit -m "Fix failing build"
   git push
   ```

Do not force push and do not rewrite history; just add a fixing commit. To rerun a run without changes: `gh run rerun <run-id>`.

Common causes: the `<h1>` was removed, emptied or duplicated (unit test), a typo in an Angular template (build error), push rejected for workflow files (missing `workflow` scope). See `docs/troubleshooting.md`.

## Optional: local full-stack demo

Terminal 1 - Flask:

```powershell
cd D:\ML_Project
.\.venv\Scripts\Activate.ps1
$env:OPENBLAS_NUM_THREADS='1'; $env:OMP_NUM_THREADS='1'
python backend\app.py
```

Terminal 2 - Angular (wait until Flask answers `/health` first):

```powershell
cd D:\ML_Project\frontend
npx ng serve --proxy-config proxy.conf.json --poll 2000
```

Terminal 3 - check the API:

```powershell
cd D:\ML_Project
curl.exe -s -m 5 http://127.0.0.1:5000/health
curl.exe -s -X POST http://127.0.0.1:5000/predict -H "Content-Type: application/json" --data-binary "@backend/test_payload.json"
```

Open http://localhost:4200, click **Fill sample values**, then **Predict severity**: the predicted class, probabilities and disclaimer appear. Stop both servers with Ctrl+C afterwards.
