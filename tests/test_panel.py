"""Smoke tests for the regional panel — verify it reconciles to known source totals."""
from pathlib import Path

import pandas as pd
import pytest

PANEL_PATH = Path(__file__).parent.parent / "data" / "processed" / "regional_panel.csv"


@pytest.fixture(scope="module")
def panel():
    assert PANEL_PATH.exists(), (
        f"Panel not found at {PANEL_PATH}. Run `make panel` first."
    )
    return pd.read_csv(PANEL_PATH)


def test_panel_shape(panel):
    """13 regions x 5 years = 65 rows."""
    assert len(panel) == 65
    assert panel["region"].nunique() == 13
    assert set(panel["year"].unique()) == {2020, 2021, 2022, 2023, 2024}


def test_no_null_outcomes(panel):
    """Core outcome columns must be complete."""
    for col in ["deaths", "injuries", "vehicles_total", "licenses_total"]:
        assert panel[col].notna().all(), f"Null values in {col}"


def test_deaths_total_2024(panel):
    """Sum of regional deaths in 2024 should match GASTAT sheet 5-1 total (4282)."""
    total = panel[panel["year"] == 2024]["deaths"].sum()
    assert total == 4282, f"Expected 4282, got {total}"


def test_deaths_total_2023(panel):
    """Sum of regional deaths in 2023 should match GASTAT sheet 34 total (4423)."""
    total = panel[panel["year"] == 2023]["deaths"].sum()
    assert total == 4423, f"Expected 4423, got {total}"


def test_severe_total_2024(panel):
    """Sum of severe accidents in 2024 should match GASTAT sheet 5-5 total (17231)."""
    total = panel[panel["year"] == 2024]["severe_total"].sum()
    assert total == 17231, f"Expected 17231, got {total}"


def test_riyadh_2024_exact_values(panel):
    """Spot-check Riyadh 2024 against source."""
    r = panel[(panel["region"] == "Riyadh") & (panel["year"] == 2024)].iloc[0]
    assert r["injuries"] == 5503
    assert r["deaths"] == 953
    assert r["vehicles_new"] == 266936
    assert r["licenses_new"] == 471526


def test_arabic_names_present(panel):
    """Every row must have an Arabic region name for the bilingual dashboard."""
    assert panel["region_ar"].notna().all()
    assert panel["region_ar"].nunique() == 13


def test_derived_ratios_sane(panel):
    """Fatality ratio must be between 0 and 1; risk metrics must be positive."""
    assert panel["fatality_ratio"].between(0, 1).all()
    assert (panel["deaths_per_1k_vehicles"] >= 0).all()
