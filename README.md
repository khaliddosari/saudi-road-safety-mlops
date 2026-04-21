# Saudi Road Safety Analytics Platform

![CI](https://github.com/khaliddosari/saudi-road-safety-mlops/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**Multi-source risk intelligence and Vision 2030 forecasting for Saudi road traffic safety.**

[العربية](docs/README.ar.md) • [Architecture](docs/ARCHITECTURE.md) • [API Docs](docs/API.md)

---

## Project Overview

Most road safety analyses in the region report raw accident counts. This project integrates official GASTAT Ministry of Transport data — vehicle registrations, driving licenses, road infrastructure, and intercity traffic — with accident and fatality statistics to compute **exposure-adjusted** risk metrics across all 13 Saudi administrative regions.

The platform:
- Forecasts national fatality trajectories against Vision 2030 road safety targets
- Identifies high-risk regions by deaths-per-vehicle (not just raw counts)
- Detects anomalies in monthly traffic and accident patterns
- Clusters regions by risk profile for policy targeting
- Serves all outputs via a production-ready MLOps stack and a bilingual Power BI dashboard

## Data Sources

All data is from official public Saudi government sources:

| Source | Coverage | Granularity |
|---|---|---|
| GASTAT Land/Road Transport Statistics 2022–2024 | 5 years | Regional annual, monthly traffic |
| GASTAT Open Data Portal | 10-year national trend | Annual |
| Ministry of Transport Open Data | Traffic sensors, road specs | Point-level / regional |

**Published outputs use only aggregated, regional-level data.** No row-level or personally identifiable data is included.

## Project Structure

```
saudi-road-safety-mlops/
├── .github/workflows/     CI/CD pipelines
├── data/
│   ├── raw/              Original downloads (gitignored)
│   ├── interim/          Intermediate cleaned files (gitignored)
│   └── processed/        ML-ready outputs
├── notebooks/            EDA and analysis
├── src/
│   ├── data/             Ingestion, cleaning, panel construction
│   ├── features/         Feature engineering
│   ├── models/           Training, evaluation, prediction
│   ├── api/              FastAPI inference service
│   └── utils/            Shared helpers (Arabic text, plotting)
├── tests/                Unit tests
├── powerbi/              .pbix files and data model docs
├── docker/               Dockerfiles and compose
├── configs/              Model and data configs
└── docs/                 Architecture, API, Arabic README
```

## Quick Start

### Install
```bash
git clone https://github.com/khaliddosari/saudi-road-safety-mlops.git
cd saudi-road-safety-mlops
pip install -r requirements.txt
```

### Build the data panel
```bash
python src/data/build_panel.py
```

This produces:
- `data/processed/regional_panel.csv` — 65 rows × 20 columns (13 regions × 5 years)
- `data/processed/national_trend.csv` — 10-year national fatality series
- `data/processed/traffic_monthly.csv` — 156 rows of monthly traffic exposure
- `data/processed/causes_trend.csv` — normalized accident causes 2020–2023

### Run the API locally
```bash
docker compose up
```

API docs available at `http://localhost:8000/docs`.

## Modeling Approach

| Component | Method | Data |
|---|---|---|
| National fatality forecasting | Prophet + SARIMA ensemble | national_trend.csv |
| Regional risk regression | LightGBM + SHAP | regional_panel.csv |
| Monthly anomaly detection | STL decomposition + Isolation Forest | traffic_monthly.csv |
| Regional clustering | K-Means + silhouette validation | regional_panel.csv |
| Demographic risk profiling | Chi-square + disparity index | demographic breakdowns |

All experiments are tracked in MLflow. See `notebooks/` for the full analysis.

## MLOps Stack

- **Experiment tracking:** MLflow
- **Model serving:** FastAPI + Uvicorn
- **Containerization:** Docker + docker-compose
- **CI/CD:** GitHub Actions (lint, test, build, deploy)
- **Data validation:** Pandera / Great Expectations

## Dashboard

A bilingual (Arabic / English) Power BI dashboard visualizes:
1. Vision 2030 KPI Tracker — fatalities per 100k against target trajectory
2. Regional Risk Heatmap — exposure-adjusted, not raw counts
3. Temporal Patterns — monthly traffic vs. accident rates
4. Forecasts & Anomalies — model outputs with confidence intervals
5. Cause & Demographic Profiles

See `powerbi/` for the `.pbix` file and data model documentation.

## Data Disclosure

This project uses only publicly available aggregated statistics. Regional and national totals are sourced from published GASTAT yearbooks and the Saudi Open Data Portal. No row-level accident records, personal identifiers, or protected information appear in this repository.

## Citation

If you use this project, please cite the underlying GASTAT sources:
- General Authority for Statistics (GASTAT), *Road Transport Statistics 2024*
- Ministerial Committee for Traffic Safety, Annual Reports 2022–2024

## Author

**Khalid Al-Dosari**
Senior Computer Science Student, Imam Mohammad Ibn Saud Islamic University (IMSIU)
GitHub: [@khaliddosari](https://github.com/khaliddosari) • LinkedIn: [khalid-al-dosari](https://linkedin.com/in/khalid-al-dosari)

## License

MIT (code) • Data sources retain their original licenses and terms of use.
