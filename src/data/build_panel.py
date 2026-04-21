"""
Build the Saudi Road Safety regional panel (2020-2024).

Inputs:
    - Land_Transport_Statistics_table_2022-EN.xlsx  (GASTAT yearbook)
    - Land_Transport_Statistics_table_2023-EN.xlsx  (GASTAT yearbook)
    - Rroad_Transport_Statistics_2024_EN__1_.xlsx   (GASTAT yearbook)
    - injuries_and_Deaths__from_Road_Traffic_Accident.csv  (national 10-yr trend)

Outputs:
    - data/processed/regional_panel.csv     (region x year, wide)
    - data/processed/regional_panel_long.csv (tidy long format)
    - data/processed/national_trend.csv     (year, national totals)
    - data/processed/traffic_monthly.csv    (region x year x month, vehicle counts)
    - data/processed/causes_trend.csv       (cause x year, national counts)
"""

import pandas as pd
from pathlib import Path

UPLOADS = Path('/mnt/user-data/uploads')
OUT = Path('/home/claude/project/data/processed')
OUT.mkdir(parents=True, exist_ok=True)

F22 = UPLOADS / 'Land_Transport_Statistics_table_2022-EN.xlsx'
F23 = UPLOADS / 'Land_Transport_Statistics_table_2023-EN.xlsx'
F24 = UPLOADS / 'Rroad_Transport_Statistics_2024_EN__1_.xlsx'
NATIONAL_CSV = UPLOADS / 'injuries_and_Deaths__from_Road_Traffic_Accident.csv'

# -------------------------------------------------------------------
# Region canonicalization
# -------------------------------------------------------------------
REGION_MAP = {
    'Riyadh': 'Riyadh',
    'Makkah': 'Makkah',
    'Madinah': 'Madinah',
    'Qassim': 'Qassim',
    'Qassim Region': 'Qassim',
    'Eastern Province': 'Eastern',
    'Eastern Region': 'Eastern',
    'Aseer': 'Aseer',
    'Aseer Region': 'Aseer',
    'Tabuk': 'Tabuk',
    'Tabuk Region': 'Tabuk',
    'Hail': 'Hail',
    'Hail Region': 'Hail',
    'Northern Borders': 'Northern Borders',
    'Jazan': 'Jazan',
    'Jazan Region': 'Jazan',
    'Najran': 'Najran',
    'Najran Region': 'Najran',
    'Al Baha': 'Al-Baha',
    'Al-Baha': 'Al-Baha',
    'Al-Baha Region': 'Al-Baha',
    'Al-Jouf': 'Al-Jouf',
    'Al-Jouf Region': 'Al-Jouf',
}

REGION_AR = {
    'Riyadh': 'الرياض',
    'Makkah': 'مكة المكرمة',
    'Madinah': 'المدينة المنورة',
    'Qassim': 'القصيم',
    'Eastern': 'المنطقة الشرقية',
    'Aseer': 'عسير',
    'Tabuk': 'تبوك',
    'Hail': 'حائل',
    'Northern Borders': 'الحدود الشمالية',
    'Jazan': 'جازان',
    'Najran': 'نجران',
    'Al-Baha': 'الباحة',
    'Al-Jouf': 'الجوف',
}

CANONICAL_REGIONS = list(REGION_AR.keys())


def canon(name):
    """Map any region variant to its canonical name, or None if not a region."""
    if pd.isna(name):
        return None
    s = str(name).strip()
    return REGION_MAP.get(s)


# -------------------------------------------------------------------
# Extractors — one per logical table, returns tidy long DataFrame
# -------------------------------------------------------------------

def extract_accidents_2024():
    """Sheet 5-1 of 2024 yearbook: deaths + injuries by region, 2024."""
    df = pd.read_excel(F24, sheet_name='5-1', header=None, skiprows=5)
    df.columns = ['region_raw', 'injuries', 'deaths']
    df['region'] = df['region_raw'].apply(canon)
    df = df.dropna(subset=['region'])
    df['year'] = 2024
    return df[['region', 'year', 'deaths', 'injuries']]


def extract_accidents_2023():
    """Sheet 34 of 2023 yearbook: deaths + injuries by region, 2023."""
    df = pd.read_excel(F23, sheet_name='34', header=None, skiprows=5)
    df.columns = ['region_raw', 'injuries', 'deaths']
    df['region'] = df['region_raw'].apply(canon)
    df = df.dropna(subset=['region'])
    df['year'] = 2023
    return df[['region', 'year', 'deaths', 'injuries']]


def extract_accidents_2020_2022():
    """Sheet 17 of 2022 yearbook: 3-yr panel 2020-2022, deaths & injuries by region."""
    # Header is split across rows 5-6; we parse manually
    raw = pd.read_excel(F22, sheet_name='17', header=None)
    # Row 7 onward is data; columns: region, inj2020, inj2021, inj2022, d2020, d2021, d2022
    data = raw.iloc[7:].copy()
    data.columns = ['region_raw', 'inj_2020', 'inj_2021', 'inj_2022',
                    'd_2020', 'd_2021', 'd_2022']
    data['region'] = data['region_raw'].apply(canon)
    data = data.dropna(subset=['region'])

    rows = []
    for _, r in data.iterrows():
        for yr in (2020, 2021, 2022):
            rows.append({
                'region': r['region'],
                'year': yr,
                'injuries': r[f'inj_{yr}'],
                'deaths': r[f'd_{yr}'],
            })
    return pd.DataFrame(rows)


def extract_severe_2024():
    """Sheet 5-5 of 2024 yearbook: severe accidents by region, within/outside city, 2024."""
    df = pd.read_excel(F24, sheet_name='5-5', header=None, skiprows=5)
    df.columns = ['region_raw', 'severe_in_city', 'severe_out_city', 'severe_total']
    df['region'] = df['region_raw'].apply(canon)
    df = df.dropna(subset=['region'])
    df['year'] = 2024
    return df[['region', 'year', 'severe_in_city', 'severe_out_city', 'severe_total']]


def extract_severe_2023():
    """Sheet 37 of 2023 yearbook: severe accidents by region, 2023 (no in/out split)."""
    df = pd.read_excel(F23, sheet_name='37', header=None, skiprows=5)
    df.columns = ['region_raw', 'severe_total']
    df['region'] = df['region_raw'].apply(canon)
    df = df.dropna(subset=['region'])
    df['year'] = 2023
    df['severe_in_city'] = pd.NA
    df['severe_out_city'] = pd.NA
    return df[['region', 'year', 'severe_in_city', 'severe_out_city', 'severe_total']]


def extract_severe_2021_2022():
    """Sheet 20 of 2022 yearbook: severe accidents by region, 2021+2022."""
    raw = pd.read_excel(F22, sheet_name='20', header=None)
    data = raw.iloc[7:].copy()
    data.columns = ['region_raw', 'sev_2021', 'sev_2022']
    data['region'] = data['region_raw'].apply(canon)
    data = data.dropna(subset=['region'])

    rows = []
    for _, r in data.iterrows():
        for yr in (2021, 2022):
            rows.append({
                'region': r['region'],
                'year': yr,
                'severe_in_city': pd.NA,
                'severe_out_city': pd.NA,
                'severe_total': r[f'sev_{yr}'],
            })
    return pd.DataFrame(rows)


def extract_vehicles_2020_2024():
    """Sheet 4-3 of 2024 yearbook: vehicles registered by region, 5-yr panel."""
    raw = pd.read_excel(F24, sheet_name='4-3', header=None)
    # Layout: row 4 has years, row 5 has New/Renewal subheaders, row 6 onward is data
    data = raw.iloc[6:].copy()
    data.columns = [
        'region_raw',
        'new_2020', 'ren_2020',
        'new_2021', 'ren_2021',
        'new_2022', 'ren_2022',
        'new_2023', 'ren_2023',
        'new_2024', 'ren_2024',
    ]
    data['region'] = data['region_raw'].apply(canon)
    data = data.dropna(subset=['region'])

    rows = []
    for _, r in data.iterrows():
        for yr in range(2020, 2025):
            rows.append({
                'region': r['region'],
                'year': yr,
                'vehicles_new': r[f'new_{yr}'],
                'vehicles_renewal': r[f'ren_{yr}'],
            })
    return pd.DataFrame(rows)


def extract_licenses_2020_2024():
    """Sheet 6-1 of 2024 yearbook: driving licenses issued by region, 5-yr panel."""
    raw = pd.read_excel(F24, sheet_name='6-1', header=None)
    data = raw.iloc[7:].copy()
    data.columns = [
        'region_raw',
        'new_2020', 'ren_2020',
        'new_2021', 'ren_2021',
        'new_2022', 'ren_2022',
        'new_2023', 'ren_2023',
        'new_2024', 'ren_2024',
    ]
    data['region'] = data['region_raw'].apply(canon)
    data = data.dropna(subset=['region'])

    rows = []
    for _, r in data.iterrows():
        for yr in range(2020, 2025):
            rows.append({
                'region': r['region'],
                'year': yr,
                'licenses_new': r[f'new_{yr}'],
                'licenses_renewal': r[f'ren_{yr}'],
            })
    return pd.DataFrame(rows)


def extract_traffic_monthly_2024():
    """Sheet 3-5 of 2024 yearbook: monthly intercity vehicle traffic by region."""
    raw = pd.read_excel(F24, sheet_name='3-5', header=None)
    data = raw.iloc[7:].copy()
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    data.columns = ['region_raw', 'count_points'] + months
    data['region'] = data['region_raw'].apply(canon)
    data = data.dropna(subset=['region'])

    rows = []
    for _, r in data.iterrows():
        for i, m in enumerate(months, start=1):
            rows.append({
                'region': r['region'],
                'year': 2024,
                'month': i,
                'traffic_count': r[m],
                'count_points': r['count_points'],
            })
    return pd.DataFrame(rows)


def extract_road_density_2024():
    """Sheet 7-5 of 2024 yearbook: road network density by region."""
    df = pd.read_excel(F24, sheet_name='7-5', header=None, skiprows=5)
    df.columns = ['region_raw', 'road_density_per_capita', 'road_density_per_area']
    df['region'] = df['region_raw'].apply(canon)
    df = df.dropna(subset=['region'])
    df['year'] = 2024
    return df[['region', 'year', 'road_density_per_capita', 'road_density_per_area']]


def extract_national_trend():
    """National deaths+injuries 2014-2023 from GASTAT open data."""
    df = pd.read_csv(NATIONAL_CSV, skiprows=1)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={
        'Year': 'year',
        'No. of Injuries': 'national_injuries',
        'No. of Deaths': 'national_deaths',
        'Injuries per 100,000 Population': 'injury_rate_per_100k',
        'Deaths per 100,000 Population': 'death_rate_per_100k',
    })
    df = df.dropna(subset=['year'])
    for c in ['national_injuries', 'national_deaths']:
        df[c] = df[c].astype(str).str.replace(',', '').astype(float)
    df['year'] = df['year'].astype(int)
    return df


def extract_causes():
    """National accident causes, 2020-2024 stitched across yearbooks."""
    # 2022 yearbook sheet 27: 2020, 2021, 2022
    r22 = pd.read_excel(F22, sheet_name='27', header=None).iloc[6:].copy()
    r22.columns = ['cause', '2020', '2021', '2022']
    r22 = r22[r22['cause'].notna() & ~r22['cause'].astype(str).str.contains('Total|source', case=False, na=False)]

    # 2023 yearbook sheet 42: 2023
    r23 = pd.read_excel(F23, sheet_name='42', header=None).iloc[6:].copy()
    r23.columns = ['cause', '2023']
    r23 = r23[r23['cause'].notna() & ~r23['cause'].astype(str).str.contains('Total|source|Index', case=False, na=False)]

    # Normalize cause names (different wording across years)
    CAUSE_NORM = {
        'Not leaving a safe distance': 'Unsafe distance',
        'Do not leave a safe distance': 'Unsafe distance',
        'Suddenly swerving': 'Sudden deviation',
        'Sudden deviation': 'Sudden deviation',
        'Distraction from driving': 'Distraction',
        'Right of Way Violation': 'Right-of-way violation',
        'Violation of Right of Way': 'Right-of-way violation',
        'opposite direction to traffic': 'Wrong direction',
        'Reverse the direction of the walk': 'Wrong direction',
    }
    r22['cause_norm'] = r22['cause'].str.strip().map(CAUSE_NORM)
    r23['cause_norm'] = r23['cause'].str.strip().map(CAUSE_NORM)

    rows = []
    for _, r in r22.iterrows():
        if pd.isna(r['cause_norm']):
            continue
        for yr in ['2020', '2021', '2022']:
            rows.append({'year': int(yr), 'cause': r['cause_norm'], 'accidents': r[yr]})
    for _, r in r23.iterrows():
        if pd.isna(r['cause_norm']):
            continue
        rows.append({'year': 2023, 'cause': r['cause_norm'], 'accidents': r['2023']})
    return pd.DataFrame(rows)


# -------------------------------------------------------------------
# Build panel
# -------------------------------------------------------------------

def main():
    print("Extracting accidents...")
    acc = pd.concat([
        extract_accidents_2020_2022(),
        extract_accidents_2023(),
        extract_accidents_2024(),
    ], ignore_index=True)
    print(f"  accidents: {len(acc)} rows")

    print("Extracting severe accidents...")
    sev = pd.concat([
        extract_severe_2021_2022(),
        extract_severe_2023(),
        extract_severe_2024(),
    ], ignore_index=True)
    print(f"  severe: {len(sev)} rows")

    print("Extracting vehicles...")
    veh = extract_vehicles_2020_2024()
    print(f"  vehicles: {len(veh)} rows")

    print("Extracting licenses...")
    lic = extract_licenses_2020_2024()
    print(f"  licenses: {len(lic)} rows")

    print("Extracting road density (2024 only)...")
    rd = extract_road_density_2024()
    print(f"  road density: {len(rd)} rows")

    print("Extracting monthly traffic (2024 only)...")
    tm = extract_traffic_monthly_2024()
    print(f"  monthly traffic: {len(tm)} rows")

    print("Extracting national trend...")
    nat = extract_national_trend()
    print(f"  national trend: {len(nat)} rows")

    print("Extracting causes...")
    causes = extract_causes()
    print(f"  causes: {len(causes)} rows")

    # Build panel: outer-join everything on (region, year)
    print("\nBuilding regional panel...")
    panel = acc.merge(sev, on=['region', 'year'], how='outer')
    panel = panel.merge(veh, on=['region', 'year'], how='outer')
    panel = panel.merge(lic, on=['region', 'year'], how='outer')
    panel = panel.merge(rd, on=['region', 'year'], how='outer')

    # Derived metrics
    panel['vehicles_total'] = panel['vehicles_new'].fillna(0) + panel['vehicles_renewal'].fillna(0)
    panel['licenses_total'] = panel['licenses_new'].fillna(0) + panel['licenses_renewal'].fillna(0)
    panel['deaths_per_1k_vehicles'] = panel['deaths'] / panel['vehicles_total'] * 1000
    panel['injuries_per_1k_vehicles'] = panel['injuries'] / panel['vehicles_total'] * 1000
    panel['severe_per_1k_vehicles'] = panel['severe_total'] / panel['vehicles_total'] * 1000
    panel['fatality_ratio'] = panel['deaths'] / (panel['deaths'] + panel['injuries'])

    # Add Arabic names
    panel['region_ar'] = panel['region'].map(REGION_AR)

    # Sort
    panel = panel.sort_values(['region', 'year']).reset_index(drop=True)

    # Save outputs
    panel.to_csv(OUT / 'regional_panel.csv', index=False)
    print(f"\n  -> regional_panel.csv  ({len(panel)} rows)")

    # Tidy long format for Power BI / plotting
    id_cols = ['region', 'region_ar', 'year']
    val_cols = [c for c in panel.columns if c not in id_cols]
    panel_long = panel.melt(id_vars=id_cols, value_vars=val_cols,
                             var_name='metric', value_name='value')
    panel_long.to_csv(OUT / 'regional_panel_long.csv', index=False)
    print(f"  -> regional_panel_long.csv  ({len(panel_long)} rows)")

    nat.to_csv(OUT / 'national_trend.csv', index=False)
    print(f"  -> national_trend.csv  ({len(nat)} rows)")

    tm.to_csv(OUT / 'traffic_monthly.csv', index=False)
    print(f"  -> traffic_monthly.csv  ({len(tm)} rows)")

    causes.to_csv(OUT / 'causes_trend.csv', index=False)
    print(f"  -> causes_trend.csv  ({len(causes)} rows)")

    return panel, nat, tm, causes


if __name__ == '__main__':
    panel, nat, tm, causes = main()
    print("\n" + "=" * 72)
    print("PANEL PREVIEW (first 10 rows):")
    print("=" * 72)
    print(panel.head(10).to_string())
    print("\n" + "=" * 72)
    print("PANEL SCHEMA:")
    print("=" * 72)
    print(panel.dtypes)
    print(f"\nPanel shape: {panel.shape}")
    print(f"Unique regions: {panel['region'].nunique()}")
    print(f"Year range: {panel['year'].min()}–{panel['year'].max()}")
