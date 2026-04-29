# ChalinTrends deployment and security checklist

This repo is prepared for deployment to Streamlit Community Cloud from GitHub.

## Current deploy shape

- App entrypoint: `streamlit_app.py`
- Production branch: `main`
- Python version to select in Streamlit Cloud: `3.11`
- Python dependencies for Streamlit Cloud: `requirements.txt`
- Daily data refresh workflow: `.github/workflows/daily-prices.yml`
- CI workflow: `.github/workflows/ci.yml`
- Data committed for the app: `data/prices.csv`

## Security review summary

No application secrets are currently required. The app reads public price data, stores it in `data/prices.csv`, and renders the dashboard from that CSV.

Checked before deployment:

- No `st.secrets`, API keys, passwords, tokens, or environment secret reads are used by the app.
- Local secret files are ignored: `.streamlit/secrets.toml`, `.env`, `.env.*`, `*.pem`, and `*.key`.
- The GitHub Actions daily workflow is not triggered by pull requests. It only runs on schedule or manual dispatch.
- The CI workflow has read-only repository permissions.
- The daily workflow uses the narrow permission it needs, `contents: write`, because it commits `data/prices.csv`.
- The daily workflow now runs tests before committing a data update.
- User/data strings rendered through custom HTML are escaped in the Streamlit HTML helpers.
- The custom live-search component does not inject external HTML; it renders a local input and sends its value back to Streamlit.
- The Chalin API parser is tolerant of malformed individual products: it skips those records with warnings and continues with usable rows. It fails the workflow only if the response is globally unusable, such as invalid JSON, missing `data.listas`, no Salon/Delivery lists, or no valid product rows.
- New product names that are not in `chalintrends/categories.py` are assigned to `Sin categorizar`. This keeps the app working and makes future category assignment explicit.

Known residual risks:

- The scraper still depends on the public Chalin API. Minor product-level issues are skipped with warnings; broad contract changes should fail the GitHub Action before committing data. Review `Sin categorizar` after deploys to classify newly added products.
- GitHub Actions uses version tags like `actions/checkout@v4` and `actions/setup-python@v5`. For maximum supply-chain hardening, pin those actions to full commit SHAs later.
- The app is not authenticated at the application layer. Use Streamlit Community Cloud sharing settings if the deployed app should be private.

## GitHub setup

1. Create a GitHub repository.
2. Add it as the local remote:

   ```powershell
   git remote add origin https://github.com/<owner>/<repo>.git
   ```

3. Push `main`:

   ```powershell
   git push -u origin main
   ```

4. In GitHub, enable branch protection for `main`:
   - Require pull request before merging.
   - Require status checks to pass.
   - Select the `CI / test` check once it appears.
   - Restrict who can push directly to `main` if this becomes a shared repo.

5. In repository settings, review Actions permissions:
   - Allow GitHub Actions for this repository.
   - Keep workflow permissions as read-only by default if possible.
   - The `daily-prices.yml` workflow declares `contents: write` explicitly for its data commit.

## Streamlit Community Cloud setup

1. Go to `share.streamlit.io`.
2. Create a new app from the GitHub repo.
3. Use:
   - Branch: `main`
   - Main file path: `streamlit_app.py`
   - Python version: `3.11`
4. No secrets are required for the current app.
5. If secrets are needed later, add them through Streamlit Cloud app settings, not GitHub. For local development, put them in `.streamlit/secrets.toml`; that file is ignored by git.
6. After the first deploy, open the app logs and confirm:
   - Dependencies install from `requirements.txt`.
   - `streamlit_app.py` starts without import errors.
   - The app can read `data/prices.csv`.

## Release checklist

Before pushing a release:

```powershell
$env:TMP="$PWD\.pytest_tmp"
$env:TEMP="$PWD\.pytest_tmp"
python -m pytest
python -m compileall chalintrends streamlit_app.py scripts tests
python -c "import tomllib; tomllib.load(open('pyproject.toml','rb')); print('pyproject-ok')"
```

Before enabling the daily data refresh:

1. Confirm GitHub Actions CI passes on `main`.
2. Run the `Daily prices` workflow manually once with `workflow_dispatch`.
3. Confirm the workflow only commits `data/prices.csv`.
4. Confirm Streamlit Cloud redeploys after the CSV commit.

## Operational notes

- `data/prices.csv` is intentionally committed so Streamlit Cloud can serve the latest data without a database.
- The daily workflow should be the only automated writer to `data/prices.csv`.
- If the CSV grows too large, move history storage to a database or object storage and use Streamlit secrets for credentials.
- If Chalin changes the API or pricing categories, update tests before trusting new data.

## References checked

- Streamlit Community Cloud deployment: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- Streamlit Community Cloud dependencies: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies
- Streamlit Community Cloud secrets: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- Streamlit trust and security: https://docs.streamlit.io/deploy/streamlit-community-cloud/get-started/trust-and-security
- GitHub Actions workflow permissions: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#permissions
- GitHub Actions security guidance: https://docs.github.com/actions/security-guides
