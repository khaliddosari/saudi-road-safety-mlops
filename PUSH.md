# How to Push This Repo to GitHub

This repo is ready to go. You just need to create a new empty repo on GitHub and run the commands below.

## Step 1 — Create the repo on GitHub

1. Go to https://github.com/new
2. Repository name: `saudi-road-safety-mlops`
3. Description: *Multi-source risk intelligence and Vision 2030 forecasting for Saudi road traffic safety*
4. Public
5. **Do NOT** initialize with README, .gitignore, or license (we already have them)
6. Click *Create repository*

## Step 2 — Push from your local machine

Open a terminal in the extracted folder and run:

```bash
git init
git add .
git commit -m "Initial commit: regional data panel + MLOps scaffolding"
git branch -M main
git remote add origin https://github.com/khaliddosari/saudi-road-safety-mlops.git
git push -u origin main
```

If this is your first time pushing from this machine, GitHub will ask you to authenticate (personal access token or SSH key).

## Step 3 — Verify CI ran

- Go to your repo on GitHub
- Click the **Actions** tab
- You should see a `CI` workflow running — it installs deps, lints, and runs the 8 panel tests
- Wait ~2 minutes for the green checkmark

## Step 4 — Add a good repo description on GitHub

In the repo settings (top right of the code page, click the gear icon next to "About"):

- **Description**: `Multi-source risk intelligence and Vision 2030 forecasting for Saudi road traffic safety. GASTAT data + LightGBM + Prophet + FastAPI + Power BI.`
- **Topics** (tags): `saudi-arabia`, `vision-2030`, `road-safety`, `mlops`, `mlflow`, `fastapi`, `data-science`, `time-series`, `lightgbm`, `power-bi`, `arabic`, `bilingual-dashboard`
- Check *"Use your GitHub Pages"* only after you add a demo page

## Step 5 — Pin it on your profile

Go to your GitHub profile → Customize your pins → add `saudi-road-safety-mlops` to the top. This is the one you want recruiters to see first.

---

**Note on the raw data files:** The three GASTAT Excel files you uploaded are gitignored and not included in the push. To reproduce the panel, place them in `data/raw/` and run `make panel`. You may want to add a short note in the README about how to obtain them — they're public from https://stats.gov.sa and https://mot.gov.sa/ar/open-data.
