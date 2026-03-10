"""
AADT Traffic Counts Dashboard Builder
=======================================
Reads NYS DOT annualized traffic statistics CSV for the 8-county
Rochester region, aggregates by county, and produces interactive
Plotly HTML dashboards matching the ACT pipeline v2 visual style.

Outputs:
  Output/charts/bar_median_aadt_by_county.html      – Median AADT by county
  Output/charts/bar_urban_rural_stations.html        – Urban vs Rural station mix
  Output/charts/bar_truck_aadt_by_county.html        – Avg truck AADT by county
  Output/aadt_traffic_dashboard.html                 – Dashboard wrapper

Run:  python aadt_traffic.py
"""

import os
import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from utils import (
    COLOR_PRIMARY, COLOR_PRIMARY_LT, COLOR_DARK, COLOR_ACCENT,
    COLOR_MUTED, COLOR_CHART_BG, COLOR_GRID, COLOR_TEXT_MAIN,
    MOBILE_CONFIG, COMMON_LAYOUT, write_chart_html, _css_base,
)

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
BASE_DIR   = r"C:\Users\camer\Desktop\ACT\Transportation Data Sources"
INPUT_FILE = os.path.join(BASE_DIR, "annualized_statistics.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "Output")
CHARTS_DIR = os.path.join(OUTPUT_DIR, "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
SOURCE_TEXT = (
    "Source: NYS DOT, Traffic Data Viewer — "
    "Annualized Average Daily Traffic (AADT), 2024 "
    "(dot.ny.gov/tdv)"
)

# Sort order: population-descending to match other ACT dashboards
COUNTY_ORDER = [
    "Monroe", "Ontario", "Wayne", "Livingston",
    "Genesee", "Orleans", "Seneca", "Yates",
]


# =====================================================================
# 1.  LOAD & CLEAN
# =====================================================================
def load_aadt(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df.columns = [c.strip() for c in df.columns]

    df["County"] = df["County"].str.strip()
    df["AADT"]   = pd.to_numeric(df["AADT"], errors="coerce")
    df["Functional Class"] = df["Functional Class"].str.strip()

    # Parse truck volumes
    df["SU_Truck"] = pd.to_numeric(df["Single-Unit Truck AADT"], errors="coerce")
    df["CO_Truck"] = pd.to_numeric(df["Combo-Unit Truck AADT"], errors="coerce")
    df["Truck_AADT"] = df["SU_Truck"].fillna(0) + df["CO_Truck"].fillna(0)
    df["Has_Truck"] = df["SU_Truck"].notna() | df["CO_Truck"].notna()

    # Urban / Rural classification
    df["Setting"] = df["Functional Class"].apply(
        lambda x: "Urban" if str(x).startswith("Urban")
        else ("Rural" if str(x).startswith("Rural") else "Other")
    )

    # Keep only rows with valid AADT and in our 8 counties
    df = df[df["AADT"].notna() & df["County"].isin(COUNTY_ORDER)].copy()

    return df


# =====================================================================
# 2.  CHART BUILDERS
# =====================================================================

def _base_layout(**overrides):
    layout = {}
    for k, v in COMMON_LAYOUT.items():
        layout[k] = dict(v) if isinstance(v, dict) else v
    layout["font_family"] = "'DM Sans', system-ui, sans-serif"
    layout.update(overrides)
    return layout


def chart_median_aadt(df: pd.DataFrame) -> go.Figure:
    """Bar chart: median AADT per county, sorted descending."""
    med = (
        df.groupby("County")["AADT"]
        .median()
        .reindex(COUNTY_ORDER)
        .reset_index()
        .rename(columns={"AADT": "Median_AADT"})
        .sort_values("Median_AADT", ascending=False)
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=med["County"],
        y=med["Median_AADT"],
        marker=dict(color=COLOR_PRIMARY, cornerradius=4),
        text=[f"{v:,.0f}" for v in med["Median_AADT"]],
        textposition="outside",
        textfont=dict(family="'DM Sans', sans-serif", size=11, color=COLOR_MUTED),
        hovertemplate="<b>%{x} County</b><br>Median AADT: %{y:,.0f}<extra></extra>",
    ))

    # Also show station count as context
    station_counts = df.groupby("County").size().reindex(COUNTY_ORDER)
    note = " | ".join(f"{c}: {station_counts[c]:,} stations" for c in med["County"])

    layout_kw = _base_layout(
        title=dict(
            text="Median Annual Average Daily Traffic (AADT) by County",
            font=dict(family="'DM Sans', system-ui, sans-serif", size=16,
                      color=COLOR_DARK, weight="bold"),
            x=0.01, xanchor="left", y=0.97,
        ),
        yaxis_title="Median AADT (vehicles/day)",
        yaxis_tickformat=",",
        yaxis_range=[0, med["Median_AADT"].max() * 1.2],
        annotations=[dict(
            text=f"Station counts — {note}",
            xref="paper", yref="paper", x=0.0, y=-0.18,
            showarrow=False,
            font=dict(size=9, color=COLOR_MUTED, family="'DM Sans', sans-serif"),
        )],
        margin=dict(t=30, b=120, l=60, r=30),
    )
    fig.update_layout(**layout_kw)
    return fig


def chart_urban_rural(df: pd.DataFrame) -> go.Figure:
    """Stacked bar: Urban vs Rural station share by county."""
    cross = (
        df.groupby(["County", "Setting"]).size()
        .unstack(fill_value=0)
        .reindex(COUNTY_ORDER)
    )

    # Compute percentages for a 100% stacked bar
    totals = cross.sum(axis=1)
    pct = cross.div(totals, axis=0) * 100

    fig = go.Figure()

    setting_colors = {
        "Urban": COLOR_PRIMARY,
        "Rural": COLOR_PRIMARY_LT,
        "Other": COLOR_MUTED,
    }

    for setting in ["Urban", "Rural", "Other"]:
        if setting not in pct.columns:
            continue
        fig.add_trace(go.Bar(
            x=pct.index,
            y=pct[setting],
            name=setting,
            marker=dict(color=setting_colors[setting], cornerradius=2),
            customdata=cross[setting].values if setting in cross.columns else [0]*len(pct),
            hovertemplate=(
                "<b>%{x} County</b><br>"
                f"{setting}: %{{y:.1f}}% (%{{customdata}} stations)"
                "<extra></extra>"
            ),
        ))

    layout_kw = _base_layout(
        title=dict(
            text="Federal Road Classification: Urban vs. Rural by County",
            font=dict(family="'DM Sans', system-ui, sans-serif", size=16,
                      color=COLOR_DARK, weight="bold"),
            x=0.01, xanchor="left", y=0.97,
        ),
        yaxis_title="% of Counting Stations",
        yaxis_range=[0, 105],
        yaxis_ticksuffix="%",
        barmode="stack",
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.18, xanchor="center", x=0.5,
            font=dict(size=12, family="'DM Sans', sans-serif"),
        ),
        margin=dict(t=30, b=110, l=50, r=30),
    )
    fig.update_layout(**layout_kw)
    return fig


def chart_truck_aadt(df: pd.DataFrame) -> go.Figure:
    """Bar chart: average truck AADT for stations that report truck data."""
    truck = df[df["Has_Truck"]].copy()

    agg = (
        truck.groupby("County")
        .agg(
            Avg_Truck=("Truck_AADT", "mean"),
            Stations=("Truck_AADT", "count"),
        )
        .reindex(COUNTY_ORDER)
        .dropna()
        .sort_values("Avg_Truck", ascending=False)
        .reset_index()
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=agg["County"],
        y=agg["Avg_Truck"],
        marker=dict(color=COLOR_DARK, cornerradius=4),
        customdata=agg["Stations"],
        text=[f"{v:,.0f}" for v in agg["Avg_Truck"]],
        textposition="outside",
        textfont=dict(family="'DM Sans', sans-serif", size=11, color=COLOR_MUTED),
        hovertemplate=(
            "<b>%{x} County</b><br>"
            "Avg Truck AADT: %{y:,.0f}<br>"
            "Reporting Stations: %{customdata}"
            "<extra></extra>"
        ),
    ))

    layout_kw = _base_layout(
        title=dict(
            text="Average Truck Traffic (AADT) by County",
            font=dict(family="'DM Sans', system-ui, sans-serif", size=16,
                      color=COLOR_DARK, weight="bold"),
            x=0.01, xanchor="left", y=0.97,
        ),
        yaxis_title="Avg Truck AADT (vehicles/day)",
        yaxis_tickformat=",",
        yaxis_range=[0, agg["Avg_Truck"].max() * 1.2],
    )
    fig.update_layout(**layout_kw)
    return fig


# =====================================================================
# 3.  DASHBOARD WRAPPER
# =====================================================================
def build_dashboard_html() -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Traffic Counts (AADT) — 9-County Rochester Region</title>
<style>{_css_base()}</style>
<script>
function switchChart() {{
    document.getElementById('chartFrame').src = 'charts/' + document.getElementById('chartSelector').value;
}}
</script>
</head><body>
<div class="card">
    <div class="header">
        <h2>Traffic Counts (AADT) — 8-County Rochester Region (2024)</h2>
        <div class="controls-row">
            <select id="chartSelector" onchange="switchChart()">
                <option value="bar_median_aadt_by_county.html">Median AADT by County</option>
                <option value="bar_urban_rural_stations.html">Federal Road Classification: Urban vs. Rural</option>
                <option value="bar_truck_aadt_by_county.html">Average Truck Traffic by County</option>
            </select>
        </div>
    </div>
    <iframe id="chartFrame" src="charts/bar_median_aadt_by_county.html"></iframe>
</div>
</body></html>"""


# =====================================================================
# 4.  MAIN
# =====================================================================
def main():
    print("=" * 60)
    print("AADT Traffic Counts Dashboard Builder")
    print("=" * 60)

    print(f"\n📂  Reading {INPUT_FILE} ...")
    df = load_aadt(INPUT_FILE)
    print(f"    ✓ {len(df):,} stations across {df['County'].nunique()} counties")
    print(f"    AADT range: {df['AADT'].min():,.0f} – {df['AADT'].max():,.0f}")
    print(f"    Stations with truck data: {df['Has_Truck'].sum():,}")

    # ── Chart 1: Median AADT ────────────────────────────────────────
    fig1 = chart_median_aadt(df)
    p1 = os.path.join(CHARTS_DIR, "bar_median_aadt_by_county.html")
    write_chart_html(fig1, p1, SOURCE_TEXT)
    print(f"  ✓  {p1}")

    # ── Chart 2: Urban vs Rural ─────────────────────────────────────
    fig2 = chart_urban_rural(df)
    p2 = os.path.join(CHARTS_DIR, "bar_urban_rural_stations.html")
    write_chart_html(fig2, p2, SOURCE_TEXT)
    print(f"  ✓  {p2}")

    # ── Chart 3: Truck AADT ─────────────────────────────────────────
    fig3 = chart_truck_aadt(df)
    p3 = os.path.join(CHARTS_DIR, "bar_truck_aadt_by_county.html")
    write_chart_html(fig3, p3, SOURCE_TEXT)
    print(f"  ✓  {p3}")

    # ── Dashboard wrapper ───────────────────────────────────────────
    dp = os.path.join(OUTPUT_DIR, "aadt_traffic_dashboard.html")
    with open(dp, "w", encoding="utf-8") as f:
        f.write(build_dashboard_html())
    print(f"  ✓  {dp}")

    print(f"\n{'=' * 60}")
    print(f"Done — open {dp} in your browser.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()