# Troubleshooting log

Real errors we met while building this project on Windows 11 (low-memory PC), with the fix that worked. "Stage" is the build step in which the error happened. A quick reference for common problems is at the end.

| Stage | Command | Error | Fix |
|---|---|---|---|
| 4 | `python notebooks\train_small_lgbm.py` (first draft) | `numpy._core._exceptions._ArrayMemoryError` while one-hot encoding 300,000 rows (7.9 GB RAM, about 0.5 GB free) | Kept `OneHotEncoder(handle_unknown="ignore")` with its default sparse output so LightGBM trains directly on the sparse matrix. Also set `n_jobs=2` and read only the needed columns with `usecols=`. Training then completed; the bundle is 3.15 MB. |
| 7 | `Get-Process -Id <pid>` after `Stop-Process` | PowerShell exits with code 1 ("Cannot find a process") | Expected: the Flask process was already stopped. Port 5000 was confirmed free with `Get-NetTCPConnection -LocalPort 5000`. |
| 8 | `ng.cmd version` | `Program 'ng.cmd' failed to run: The system cannot find the file specified` (`cmd.exe` was not reachable from that PowerShell session; `ng version` also reported `Package Manager : npm <error>`) | Used the PowerShell shim `ng` (ng.ps1) or `node node_modules\@angular\cli\bin\ng.js` instead of the `.cmd` shims. Ran `ng new` with `--skip-install`, then `npm install` separately. For `npm run build` / `npm test`, set `$env:npm_config_script_shell='C:\Program Files\Git\bin\bash.exe'` so npm scripts run through Git Bash. |
| 8 | `ng serve` (Angular 22.2) | Dev server exits right after `Application bundle generation complete` (exit code 9/127, nothing listening on port 4200, no error message) | The native file watcher crashes on this machine. `ng serve --watch=false` and `ng serve --poll 2000` both stay up; local runs use `ng serve --proxy-config proxy.conf.json --poll 2000`. `ng build` is not affected. |
| 8 | PowerShell polling loop with `curl.exe` (no `-m`) while the dev server was down | The loop hung until it was stopped | Added `-m 5` (5-second timeout) to every `curl.exe` call in wait loops. |
| 10 | `python backend\app.py` started right after `ng serve` | `OpenBLAS error: Memory allocation still failed after 10 retries, giving up.` and Flask exited (free virtual memory was about 200 MB) | Started Flask first with `$env:OPENBLAS_NUM_THREADS='1'; $env:OMP_NUM_THREADS='1'; $env:MKL_NUM_THREADS='1'`, waited for `/health` to return 200, then started `ng serve`. |
| 10 | POST `/api/predict` through the dev proxy with Flask stopped | `HTTP/1.1 502 Bad Gateway` (dev server log: `http proxy error: /predict ... ECONNREFUSED 127.0.0.1:5000`) | Expected behaviour. The UI shows `HTTP 502 Bad Gateway: the prediction API is unavailable. Start the Flask server and try again.` |
| 11 | `git grep -i -I -E "<pattern>" --cached` | `fatal: option '--cached' must come before non-option arguments` | Put the option before the pattern: `git grep --cached -i -I -E "<pattern>"`. |
| 13 | `npx ng build --configuration production --base-href /accident-severity-cicd/` (local, npm script shell = Git Bash) | The built `index.html` contained `<base href="C:/Program Files/Git/accident-severity-cicd/">` (Git Bash converted the POSIX-style argument into a Windows path) | Set `$env:MSYS_NO_PATHCONV='1'` for the local check; the result was `<base href="/accident-severity-cicd/">`. The Ubuntu runners in GitHub Actions are not affected. |

## Common problems (quick reference)

| Symptom | Likely cause | Fix |
|---|---|---|
| Flask fails with `Address already in use` / port 5000 busy | An old Flask process is still running | `Get-NetTCPConnection -LocalPort 5000` to find the owning process, then `Stop-Process -Id <pid>`; start Flask again. |
| `/api/predict` returns 404 from `ng serve` | Dev server started without the proxy | Restart with `npx ng serve --proxy-config proxy.conf.json --poll 2000` from the `frontend` folder. |
| `/api/predict` returns 502 Bad Gateway | Flask is not running on `127.0.0.1:5000` | Start Flask (Terminal 1), check `curl.exe -s -m 5 http://127.0.0.1:5000/health`, then retry. |
| GitHub Pages shows a blank page or 404 for JS/CSS files | Wrong `--base-href` or wrong upload path | Build with `--base-href /accident-severity-cicd/` (leading and trailing slash) and upload `frontend/dist/frontend/browser` in `pages.yml`. Check Settings > Pages > Source = GitHub Actions. |
| `git push` rejected: refusing to allow an OAuth App to create or update workflow ... without `workflow` scope | The GitHub CLI token lacks the `workflow` scope | `gh auth refresh -h github.com -s workflow`, approve in the browser, check with `gh auth status`, push again. |
| Local build has `<base href="C:/Program Files/Git/...">` | Git Bash path conversion of `--base-href` when the build runs through npm scripts on Windows | Run `npx ng build ...` directly from PowerShell, or set `$env:MSYS_NO_PATHCONV='1'` first. |
| `OpenBLAS error: Memory allocation still failed` when starting Flask | Too little free memory for OpenBLAS thread buffers | `$env:OPENBLAS_NUM_THREADS='1'; $env:OMP_NUM_THREADS='1'` before `python backend\app.py`; start Flask before `ng serve`. |
| `ng serve` exits silently after the first build | Native file watcher crash on this machine | Add `--poll 2000` (or use `--watch=false`). |
| 9 | `npm test -- --watch=false` after editing the page heading | Spec asserted the exact h1 wording, so changing the heading would fail CI | The heading test now checks that there is exactly one h1 with non-empty trimmed text. Verified with the heading temporarily set to "Demo heading check" (9/9 passed), then restored. |
