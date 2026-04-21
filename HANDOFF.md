# Saudi Road Safety MLOps — Session Handoff

> Paste this entire document as the opening message of a new chat session. Everything below is self-contained context; do not assume the new session has read earlier chats.

---

I'm continuing an MLOps project I started in earlier chats. Please read this whole context before proposing actions.

## Project

**Saudi Road Safety Analytics Platform** — a Vision 2030-aligned MLOps project that analyzes road-traffic accident data across Saudi Arabia's 13 administrative regions (2020–2024) using official GASTAT Ministry of Transport data.

**Core thesis:** official reporting uses raw death counts, which rewards population size and sends policy attention to the wrong regions. This project computes **exposure-adjusted** regional risk (deaths per 1,000 registered vehicles) and shows the gap via forecasting + an explainable regional model + an anomaly detector + a clustering archetype view, feeding a bilingual Power BI dashboard.

- **Repo:** https://github.com/khaliddosari/saudi-road-safety-mlops
- **Local path:** `c:\Users\Khalid\Downloads\Coding Projects\saudi-road-safety-mlops`
- **CI:** GitHub Actions green.

## Current state

### Repo structure

```
saudi-road-safety-mlops/
├── .github/workflows/           CI
├── configs/
├── data/
│   ├── raw/                     gitignored
│   ├── interim/                 gitignored
│   └── processed/               ML-ready CSVs, committed
├── docker/                      empty so far
├── docs/                        ARCHITECTURE.md, API.md, README.ar.md
├── notebooks/                   01, 02, 03, 04, 05 all done
├── powerbi/                     empty so far
├── src/
│   ├── api/                     empty so far (FastAPI)
│   ├── data/build_panel.py      reproducible panel builder
│   ├── features/
│   ├── models/                  empty so far
│   └── utils/
├── tests/test_panel.py          8 tests passing
├── Makefile, pyproject.toml, requirements.txt
├── HANDOFF.md                   this file
```

### Processed data — `data/processed/` (all committed)

| File | Shape | Produced by |
|---|---|---|
| `regional_panel.csv` | 65 × 20 (13 regions × 5 yrs, wide) | `src/data/build_panel.py` |
| `regional_panel_long.csv` | tidy long | `src/data/build_panel.py` |
| `national_trend.csv` | 10 × 5 (2014–2023) | `src/data/build_panel.py` |
| `traffic_monthly.csv` | 156 × 5 (13 regions × 12 months, 2024) | `src/data/build_panel.py` |
| `causes_trend.csv` | 20 × 3 (5 causes × 4 years) | `src/data/build_panel.py` |
| `national_forecast.csv` | 45 × 6 (6 rows/model × 2014–2030) | `notebooks/02_forecasting.ipynb` |
| `regional_risk.csv` | 65 × 13 | `notebooks/03_regional_risk.ipynb` |
| `traffic_anomalies.csv` | 156 × 13 | `notebooks/04_anomaly.ipynb` |
| `regional_clusters.csv` | 13 × 18 | `notebooks/05_clustering.ipynb` |

**Panel columns** (the key one to remember for modeling):
`region, year, injuries, deaths, severe_in_city, severe_out_city, severe_total, vehicles_new, vehicles_renewal, licenses_new, licenses_renewal, road_density_per_capita, road_density_per_area, vehicles_total, licenses_total, deaths_per_1k_vehicles, injuries_per_1k_vehicles, severe_per_1k_vehicles, fatality_ratio, region_ar`

**13 canonical regions** (English → Arabic used in `region_ar` col):
Riyadh/الرياض, Makkah/مكة المكرمة, Madinah/المدينة المنورة, Qassim/القصيم, Eastern/المنطقة الشرقية, Aseer/عسير, Tabuk/تبوك, Hail/حائل, Northern Borders/الحدود الشمالية, Jazan/جازان, Najran/نجران, Al-Baha/الباحة, Al-Jouf/الجوف

### Notebooks (all executed end-to-end, outputs embedded, committed & pushed)

#### `notebooks/01_eda.ipynb`

7 sections: panel overview + completeness, national trend 2014–2023 with Vision 2030 milestones (launch 2016, Saher 2018, COVID 2020, target <10/100k 2030), regional raw vs exposure-adjusted deaths (**Tabuk + Jazan paradox** highlighted in red), YoY change 2020→2024 bar+diamond chart, monthly traffic 2024 with Hajj (Jun 14–19 2024) and Ramadan (Mar 11–Apr 9 2024) windows, causes evolution (absolute + share-of-total), correlation matrix with top drivers of `deaths_per_1k_vehicles`. Ends with findings mapped to the modeling roadmap.

#### `notebooks/02_forecasting.ipynb`

National `death_rate_per_100k` forecast to 2030. COVID-2020 modeled as **step dummy** (`covid = 1 if year ≥ 2020 else 0`) — not a pulse, because post-2020 levels never revert. Four models:

- NaiveDrift (baseline)
- OLS + COVID step (3 params, interpretable)
- SARIMAX grid-searched over `(p,d,q) ∈ {0,1}³ \ (0,0,0)` by AIC, COVID as exog → winner **SARIMAX(0,1,1)**
- Prophet, seasonalities off, manual changepoint at 2020-01-01, COVID as `add_regressor`

Walk-forward backtest on 2021–2023 (leave-last-one-out). SARIMAX wins (MAE 0.66). Inverse-MAE weighted ensemble:

| Model | 2030 forecast | 95% CI |
|---|---|---|
| NaiveDrift | 2.65 | [-9.89, 15.19] |
| OLS+Intervention | 0.86 | [-5.39, 7.11] |
| SARIMAX(0,1,1) | 12.83 | [-4.75, 30.40] |
| Prophet | 7.06 | [-3.82, 17.76] |
| **Ensemble** | **7.64** | **[-0.85, 16.13]** |

- Target: <10 / 100k by 2030
- **P(rate < 10 | ensemble) ≈ 71%** under normal approximation
- Linear models (OLS, NaiveDrift) extrapolate implausibly near zero by 2030 — flagged as a known failure mode in the findings.
- Findings recommend exposing per-model outputs in the FastAPI endpoint, not just the ensemble point.

#### `notebooks/03_regional_risk.ipynb`

Target: `deaths_per_1k_vehicles`. **Formal leakage audit** as an in-notebook markdown table (excludes target, `fatality_ratio`, raw `deaths`/`injuries`/`severe_*` aggregates, `region`, `region_ar`). Final feature set: `year, vehicles_new, vehicles_renewal, licenses_new, licenses_renewal, road_density_per_capita, road_density_per_area, vehicles_total, licenses_total, injuries_per_1k_vehicles, severe_per_1k_vehicles`.

**Validation:** `LeaveOneGroupOut` by region — 13 folds, each region held out entirely (all 5 rows). This is the deployment-relevant generalization test.

**Conservative LightGBM hyperparams for n=65:**

```python
objective="regression_l1", n_estimators=500, learning_rate=0.05,
num_leaves=15, max_depth=4, min_data_in_leaf=3,
feature_fraction=0.85, bagging_fraction=0.85, bagging_freq=1,
reg_lambda=1.0, random_state=42
```

Early stopping inside each fold; final model retrained on full data at `n_estimators = median(CV best_iterations)`.

Results (13-fold LOGO):

| Model | MAE | RMSE | R² |
|---|---|---|---|
| Mean baseline | 1.961 | 2.293 | -0.143 |
| Ridge | 1.502 | 1.787 | 0.306 |
| LightGBM | 1.218 | 1.530 | 0.491 |

SHAP: base value 4.175 (≈ global mean of target). Tabuk 2024 predicted 5.71 with drivers `vehicles_new` (+0.65), `injuries_per_1k_vehicles` (+0.55), `severe_per_1k_vehicles` (+0.45) — all pushing risk up. Riyadh 2024 predicted 1.45 with the same features all negative. Same signals, opposite directions — quantifies the Tabuk/Jazan paradox.

Artifact `data/processed/regional_risk.csv` schema: `region, region_ar, year, actual_risk, predicted_risk_oof, predicted_risk_full, shap_base_value, top1_feature, top1_shap, top2_feature, top2_shap, top3_feature, top3_shap`.

BI-ready for a "why is this region risky?" tooltip.

#### `notebooks/04_anomaly.ipynb`

Month-level anomaly detection on `data/processed/traffic_monthly.csv` (156 rows = 13 regions × 12 months, 2024 only). Framed explicitly as **deviation-from-own-2024-baseline**, not forecasting or seasonal decomposition — n = 12 per region makes STL with `period = 12` degenerate (one cycle, zero free df).

**Sensor-point heterogeneity called out up front:** `count_points` varies from 3 (Jazan) to 41 (Makkah), so raw cross-region counts are not comparable. All downstream features are region-normalized.

**Two detectors:**

1. **Robust MAD z-score per region** — `z = (x - median) / (1.4826 · MAD)`, threshold `|z| ≥ 2.5`. The 1.4826 constant makes MAD a consistent estimator of σ under a Gaussian. Robust to the single-month outliers we expect (Hajj, data-quality gaps).
2. **Isolation Forest globally on standardized region-normalized features** — `z_score_mad`, `share_of_annual` (month's share of region's 2024 total), `log_count = log1p(traffic_count)`. `n_estimators=200`, `contamination=0.05`, `random_state=42`. Score inverted so higher = more anomalous.

**Contextual labels:** `is_hajj_month` (month = 6), `is_ramadan_month` (months ∈ {3, 4}). Flagged months are tagged so BI tooltip can distinguish "expected spike" from "investigate this."

Results:
- 16 MAD-flagged, 8 iForest-flagged (iForest is a strict subset of MAD — it re-ranks MAD flags by multivariate anomaly-ness rather than adding new flags).
- **0 of 16 flags fell in a Hajj or Ramadan month** — per-region baselines already absorb expected religious-calendar spikes.
- Top flags split cleanly into two stories:
  - **Sensor-outage cluster:** Al-Jouf Dec (z = -10.0), Northern Borders Dec (-8.7), Hail Oct/Nov/Dec (-7.2 / -6.7 / -7.4) — sustained collapses in low-sensor-count regions at year-end. Data quality, not traffic behavior.
  - **Legitimate behavioral spikes:** Makkah Jul (+2.9, summer peak), Al-Baha Jul (+2.9), Makkah May (-3.8, post-Ramadan lull), Jazan Sep–Nov (+3.5 / +3.9 / +2.6, sustained uptick).

Artifact `data/processed/traffic_anomalies.csv` schema: `region, region_ar, year, month, traffic_count, region_median, region_mad, z_score_mad, mad_flag, iforest_score, is_anomaly, is_hajj_month, is_ramadan_month`. 156 rows — every region-month gets a score, not just the flagged ones, so BI can render a full heatmap.

#### `notebooks/05_clustering.ipynb`

K-Means on the 2024 regional snapshot (n = 13). Framed as a **descriptive exercise on n = 13**, not inferential — no p-values, Ward-linkage ARI reported as the stronger robustness signal than silhouette alone.

**Features (6, n/p ≈ 2.2):**

| # | Feature | Captures |
|---|---|---|
| 1 | `deaths_per_1k_vehicles` | Exposure-adjusted risk |
| 2 | `fatality_ratio` | Crash severity share |
| 3 | `log_vehicles_total` | Urban scale |
| 4 | `road_density_per_capita` | Road km per person |
| 5 | `road_density_per_area` | Road km per km² (orthogonal to #4) |
| 6 | `n_anomaly_flags` | Volatility, joined from `traffic_anomalies.csv` |

Correlation check passed (no pair exceeds |r| = 0.85). Standardized via `StandardScaler`.

**k-sweep over [2..6]:** silhouette peaks at k = 4 (0.260) marginally above k = 3 (0.241); any k ≥ 3 produces a 2-region minimum cluster. Chose **k = 3** on domain + diagnostics. KMeans with `n_init=50, random_state=42`.

**K-Means ↔ Ward cross-check: ARI = 0.224.** Honestly reported — K-Means emphasizes scale, Ward emphasizes `road_density_per_area` (putting Jazan + Makkah together). The dashboard should caveat the archetype as descriptive on n = 13, not a stable taxonomy.

**Three archetypes (deterministic labels from z-profile signatures):**

- **Urban Core** (5): Eastern, Madinah, Makkah, Qassim, Riyadh — `z(log_vehicles_total) ≥ 0.8`
- **Dense High-Injury** (2): Al-Baha, Jazan — `z(road_density_per_area) ≥ 0.8` with `z(fatality_ratio) < 0`. Small, built-up, injury-heavy but proportionally fewer fatal crashes.
- **Sparse High-Severity** (6): Al-Jouf, Aseer, Hail, Najran, Northern Borders, Tabuk — high `fatality_ratio` and high `road_density_per_capita`. Fewer crashes per vehicle but each is much likelier to be fatal. Hail's `fatality_ratio ≈ 0.38` is the extreme case.

Key finding: **the empirical split rejected the pre-registered prior** ("Tabuk/Jazan/Al-Baha together"). Jazan + Al-Baha share a distinct coastal-dense injury-heavy signature; Tabuk lands with the other peripheral regions on the sparse-deadly signature. These are two genuinely different policy failure modes, and the clustering surfaces the distinction the single "Tabuk/Jazan paradox" narrative was collapsing.

Artifact `data/processed/regional_clusters.csv` schema (13 × 18): `region, region_ar, cluster_id, cluster_label, pc1, pc2, <6 raw features>, <6 z-scored features>`. PCA: PC1 = 40.1% var, PC2 = 25.2% var, cumulative 65.3%. Drop-in for a Power BI scatter with radar-chart tooltip.

### Code / tests

- `src/data/build_panel.py` — extracts GASTAT Excel yearbooks (2022, 2023, 2024) and the national 10-yr CSV into the processed panel + companion series. Uses a `REGION_MAP` for canonicalization and `REGION_AR` for Arabic names. Entry point `main()`.
- `tests/test_panel.py` — 8 tests passing (shape, region coverage, derived metrics sanity, no negative counts, monotone year, etc.).
- **No `src/models/**` code yet** — all ML logic still lives in the five notebooks. Refactor is the next stage.

## Environment notes

- **Python 3.14 on Windows.** Installed this session (not yet pinned in requirements.txt, which lists looser bounds): prophet 1.3.0, statsmodels 0.14.6, scikit-learn 1.8.0, lightgbm 4.6.0, shap 0.51.0.
- `requirements.txt` has the right entries but old version floors — fine for CI.
- **Jupyter gotcha (Python 3.14):** `nbconvert` occasionally writes a malformed stream output (missing `name` field) that then blocks re-execution with `nbformat.validator.NotebookValidationError: 'name' is a required property`. Fix: strip outputs and re-run:

  ```python
  import json, pathlib
  p = pathlib.Path('notebooks/<name>.ipynb')
  nb = json.loads(p.read_text(encoding='utf-8'))
  for c in nb['cells']:
      if c['cell_type'] == 'code':
          c['outputs'] = []; c['execution_count'] = None
  p.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding='utf-8')
  ```

  then `python -m jupyter nbconvert --to notebook --execute --inplace notebooks/<name>.ipynb`.

- **Windows cp1252 console cannot print Arabic or en-dashes.** When inspecting CSVs or notebooks from a one-liner, either drop `region_ar` in the print or write to a UTF-8 file (don't rely on stdout). Setting `PYTHONIOENCODING=utf-8` also works.
- Run notebook conversions with `python -m jupyter nbconvert ...` (plain `jupyter` isn't on PATH in this PowerShell setup).
- When scaffolding notebooks from scratch, a builder script that assembles cells as Python dicts and writes JSON via `Path.write_text(json.dumps(...), encoding='utf-8')` is the cleanest pattern — avoids hand-escaping JSON and works around PowerShell quoting issues. Used for both `04_anomaly.ipynb` and `05_clustering.ipynb` in the previous session.

## Conventions the project uses

- Bilingual labels (EN + AR) live in the dataframes (`region_ar` column, bilingual markdown headers). Chart axes stay English for matplotlib rendering stability; Power BI handles Arabic typography at the presentation layer.
- Every notebook ends with a "Findings & next steps" markdown cell that maps findings to the next stage, not just summarizes.
- Every ML notebook writes a `data/processed/<stage>.csv` artifact in flat long format for Power BI + API consumption.
- Code cells prefer: small helpers (`score()`, `logo_predict()`, etc.), explicit leakage/exclusion lists as Python constants with comments, no boilerplate comments that narrate obvious lines.
- **Sample-size honesty is a house style** — n = 10 annual / n = 13 regional / n = 65 panel / n = 156 monthly are called out, not hidden. Every model notebook includes an up-front constraint section (e.g., n = 12 per region makes STL degenerate; n = 13 is descriptive not inferential).
- When a validation metric disagrees with a prior hypothesis, **report the disagreement** rather than silently adjusting the prior. Example: notebook 05's ARI = 0.22 between K-Means and Ward is surfaced in findings rather than buried, and the empirical three-archetype split (which contradicted the original "Tabuk/Jazan/Al-Baha together" prior) is documented as a more informative finding.

## Uncommitted local changes

None — the repo is clean at session handoff. Latest commits:

```
3ef4e4c 05_clustering.ipynb implemented
1d1ec6d 04_anomaly.ipynb implemented
cd2ed9c 03_regional_risk.ipynb implemented
1f361a0 02_forecasting.ipynb implemented
1b92f10 01_eda.ipynb implemented
```

## Next step: `src/models/` refactor + MLflow

The four ML notebooks (02, 03, 04, 05) all write artifacts to `data/processed/`, so the natural next stage is lifting each into a scripted, reproducible training job with experiment tracking.

**Proposed layout:**

```
src/models/
├── __init__.py
├── forecasting/
│   ├── __init__.py
│   └── train.py       rebuilds national_forecast.csv from national_trend.csv
├── regional_risk/
│   ├── __init__.py
│   └── train.py       rebuilds regional_risk.csv + persists LightGBM model + SHAP explainer
├── anomaly/
│   ├── __init__.py
│   └── train.py       rebuilds traffic_anomalies.csv
└── clustering/
    ├── __init__.py
    └── train.py       rebuilds regional_clusters.csv
```

**Each `train.py` should:**

- Expose a `main()` entry point + a CLI via `if __name__ == "__main__":` that accepts at minimum `--input-path`, `--output-path`, `--seed`.
- Log parameters (feature lists, hyperparameters, seeds) and metrics (MAE / RMSE / R² for regression, silhouette + ARI for clustering, flag counts for anomaly) to **MLflow** (local file-backed tracking URI is fine for now — `mlruns/` under the repo root, gitignored).
- Emit the same CSV artifact the notebook produces — ideally byte-identical when run with the same seed, so the notebook and script are substitutable.
- Persist model binaries where it makes sense: `models/regional_risk/lightgbm_final.pkl` + `shap_explainer.pkl`. Anomaly and clustering can skip binary persistence since they're cheap to refit, but should still log fitted parameters (IForest decision boundaries, cluster centers + scaler).
- Be importable — so later the FastAPI service can call `from src.models.regional_risk.train import load_model, predict_with_shap` without re-running training.

**Makefile targets:**

```makefile
train-forecasting:
    python -m src.models.forecasting.train

train-regional-risk:
    python -m src.models.regional_risk.train

train-anomaly:
    python -m src.models.anomaly.train

train-clustering:
    python -m src.models.clustering.train

train-all: train-forecasting train-regional-risk train-anomaly train-clustering

mlflow-ui:
    mlflow ui --backend-store-uri ./mlruns
```

**Tests:**

Add `tests/test_models.py` with:

- Smoke tests for each `train.py` (run on a tiny fixture, assert artifact shape + required columns + no NaN in key fields).
- A byte-equivalence check between the notebook-produced CSV and the script-produced CSV at the same seed. If this can't be byte-equal (Prophet, LightGBM may have platform-dependent numeric drift), assert close-enough via `pd.testing.assert_frame_equal(..., check_exact=False, atol=1e-4)`.

**CI expansion:**

- Add an `mlflow` install step to the workflow.
- Run `make train-all` as a CI job, then upload the produced CSVs as artifacts. Green build = all four models retrain cleanly.

## Roadmap after the `src/models` refactor

1. **`src/api/` — FastAPI service:**
   - `GET /forecast/national` → returns ensemble + per-model 2024–2030 with CIs
   - `GET /risk/region/{region}/{year}` → prediction + top-3 SHAP drivers
   - `GET /anomaly/region/{region}` → flagged months with context (is_hajj_month / is_ramadan_month)
   - `GET /cluster/region/{region}` → cluster assignment, archetype label, cluster-mates, PCA coords
   - OpenAPI docs at `/docs`, bilingual response field descriptions.
   - Data access pattern: API reads the CSV artifacts from `data/processed/` at startup (they're small, fit in memory). Re-training regenerates them; API hot-reload is a later concern.

2. **Docker + compose:** multi-stage Dockerfile for the API, `docker compose up` boots API + MLflow UI. Separate compose profile for dev (volume-mounted source) vs prod (COPY'd binaries).

3. **Power BI dashboard:** 5 pages:
   - **Vision 2030 KPI Tracker** — national forecast, COVID step annotation, 2030 target line, P(rate < 10)
   - **Regional Risk Heatmap** — SHAP-driven tooltip from `regional_risk.csv`
   - **Temporal Patterns** — monthly heatmap from `traffic_anomalies.csv`, tooltip branches on `is_hajj_month` / `is_ramadan_month` so expected spikes don't read as anomalies
   - **Regional Archetypes** — PC1×PC2 scatter from `regional_clusters.csv`, colored by `cluster_label`, radar tooltip on z-profile
   - **Causes & Demographics** — from `causes_trend.csv` + EDA findings
   - Bilingual labels driven by `region_ar` column already in every CSV.

4. **Schema contracts:** add Pandera or Great Expectations validation for all nine processed CSVs. Wire into CI so a rebuilt panel that silently loses a column breaks the build instead of the dashboard. Especially important once the 2025 panel lands.

5. **Data-extension follow-up (long-term):** once 2025 annual + monthly data arrives, `04_anomaly` becomes a real seasonal-anomaly detector (24+ observations per region enables STL), and `05_clustering` can track **archetype drift** — does Tabuk migrate from "Sparse High-Severity" toward "Urban Core" as vehicle stock grows? That trajectory is itself the Vision 2030 policy KPI this project was built to surface.

## About me

Senior CS student at IMSIU, ~6 months out from internship (targeting Elm, SITE, Wakeb). Transitioning into AI/ML Engineering with an MLOps focus. Comfortable with Python, pandas, Git. Prefer honest code over impressive-looking code, engineering judgment over model zoo.

## Now

Start with the `src/models/` refactor. Propose an order that mirrors code reuse (forecasting is simplest and self-contained, so lift it first; regional_risk needs the LightGBM + SHAP pipeline, lift it second; anomaly + clustering share the standardization + region-normalization utility patterns, do them together last). Keep the house style:

- Bilingual section headers where they make sense in docstrings
- Formal sample-size honesty in each script's module docstring
- MLflow logging at every meaningful fork (feature set, seeds, chosen k, chosen CV strategy)
- Every script produces a byte-reproducible CSV at fixed seed, so the notebook remains a valid way to re-derive the same artifact
- End with a `tests/test_models.py` test per script
