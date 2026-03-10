"""
RGRTA Ridership Dashboard Builder
===================================
Reads RGRTA rider volumes CSV, cleans subsidiary name changes,
and produces interactive Plotly HTML dashboards matching the
ACT pipeline v2 visual style.

Charts come in pairs — RTS Main (Monroe) and County Services —
so no data is lost to scale compression.

Outputs:
  Output/charts/line_rts_main_ridership.html     – RTS Main (Monroe) trend
  Output/charts/line_county_ridership.html        – 7 outer-county services trend
  Output/charts/bar_county_ridership.html          – County services bar
  Output/charts/bar_all_ridership.html             – All subsidiaries
  Output/rgrta_ridership_dashboard.html            – Dashboard wrapper

Run:  python rgrta_ridership.py
"""

import os
import sys
import pandas as pd
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
INPUT_FILE = os.path.join(BASE_DIR,
    "Rochester-Genesee_Regional_Transportation_Authority_(RGRTA)_"
    "Rider_Volumes___Beginning_2006_20260302.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "Output")
CHARTS_DIR = os.path.join(OUTPUT_DIR, "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# SOURCE CITATION
# ---------------------------------------------------------------------------
SOURCE_TEXT = (
    "Source: RGRTA via NY Open Data, Rider Volumes — Beginning 2006 "
    "(data.ny.gov/d/tyap-tf2m) · "
    "Supplementary data: FTA National Transit Database (transit.dot.gov/ntd/ntd-data)"
)

# ---------------------------------------------------------------------------
# SUBSIDIARY MAPPING  (pre-2015 names -> post-2015 RTS names)
# ---------------------------------------------------------------------------
SUB_RENAME = {
    "Batavia Bus Service":                    "RTS Genesee",
    "Livingston Area Transportation Service":  "RTS Livingston",
    "Orleans Transit Service":                 "RTS Orleans",
    "Seneca Transit Service":                  "RTS Seneca",
    "Wayne Area Transportation Service":       "RTS Wayne",
    "Wayne Area Transit Service":              "RTS Wayne",
    "Wyoming Transportation Service":          "RTS Wyoming",
    "Wyoming Transit Service":                 "RTS Wyoming",
    "Lift Line":                               "RTS Access",
}

# Color palette — consistent across all charts
SUB_COLORS = {
    "Regional Transit Service": COLOR_PRIMARY,
    "RTS Access":     "#94A3B8",
    "RTS Genesee":    "#E8913A",
    "RTS Livingston": "#3B8FCC",
    "RTS Ontario":    "#0062A3",
    "RTS Orleans":    "#6A994E",
    "RTS Seneca":     "#9B5DE5",
    "RTS Wayne":      "#F15BB5",
    "RTS Wyoming":    "#00BBF9",
}

# County services = everything except RTS Main and RTS Access (paratransit)
COUNTY_SUBS = [
    "RTS Ontario", "RTS Wayne", "RTS Livingston", "RTS Genesee",
    "RTS Orleans", "RTS Seneca", "RTS Wyoming",
]


# =====================================================================
# 1.  LOAD & CLEAN
# =====================================================================
def load_ridership(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df.columns = [c.strip().strip('"') for c in df.columns]

    df["Subsidiary"] = df["Subsidiary"].str.strip().str.strip('"')
    df["Year"]  = df["Year"].astype(int)
    df["Month"] = df["Month"].astype(int)
    df["Ridership"] = (
        df["Ridership"].astype(str).str.strip().str.strip('"')
        .str.replace(",", "", regex=False)
    )
    df["Ridership"] = pd.to_numeric(df["Ridership"], errors="coerce")
    df.dropna(subset=["Ridership"], inplace=True)
    df["Ridership"] = df["Ridership"].astype(int)

    # Unify subsidiary names
    df["Subsidiary"] = df["Subsidiary"].replace(SUB_RENAME)

    # Drop 2006: only Apr-Dec partial year skews annual totals
    df = df[df["Year"] >= 2007].copy()

    return df


def annualize(df: pd.DataFrame) -> pd.DataFrame:
    """Sum monthly ridership to annual totals by subsidiary."""
    return (
        df.groupby(["Subsidiary", "Year"])["Ridership"]
        .sum()
        .reset_index()
    )


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


# -- LINE CHARTS ------------------------------------------------------

def chart_line_rts_main(annual: pd.DataFrame) -> go.Figure:
    """Line chart: RTS Main (Monroe) annual ridership."""
    rts = annual[annual["Subsidiary"] == "Regional Transit Service"].sort_values("Year")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=rts["Year"],
        y=rts["Ridership"],
        mode="lines+markers",
        name="RTS Main (Monroe)",
        line=dict(color=COLOR_PRIMARY, width=2.5),
        marker=dict(size=7, color=COLOR_PRIMARY,
                    line=dict(width=2, color="white")),
        hovertemplate=(
            "<b>RTS Main (Monroe)</b><br>"
            "Year: %{x}<br>"
            "Unlinked Trips: %{y:,.0f}<extra></extra>"
        ),
    ))

    # COVID annotation
    covid_val = rts.loc[rts["Year"] == 2020, "Ridership"].values
    if len(covid_val):
        fig.add_annotation(
            x=2020, y=covid_val[0],
            text="COVID-19", showarrow=True, arrowhead=2,
            ax=40, ay=-40,
            font=dict(size=11, color=COLOR_ACCENT, family="'DM Sans', sans-serif"),
            arrowcolor=COLOR_ACCENT,
        )

    # Pre-COVID peak
    pre = rts[rts["Year"] <= 2019]
    if not pre.empty:
        peak_idx = pre["Ridership"].idxmax()
        peak_row = rts.loc[peak_idx]
        fig.add_annotation(
            x=peak_row["Year"], y=peak_row["Ridership"],
            text=f"Peak: {peak_row['Ridership']:,.0f}",
            showarrow=True, arrowhead=2, ax=0, ay=-35,
            font=dict(size=10, color=COLOR_MUTED, family="'DM Sans', sans-serif"),
            arrowcolor=COLOR_MUTED,
        )

    layout_kw = _base_layout(
        title=dict(
            text="RTS Main — Monroe County Ridership (2007–2024)",
            font=dict(family="'DM Sans', system-ui, sans-serif", size=16,
                      color=COLOR_DARK, weight="bold"),
            x=0.01, xanchor="left", y=0.97,
        ),
        xaxis_title="Year",
        yaxis_title="Annual Unlinked Trips",
        yaxis_tickformat=",",
        xaxis_dtick=1,
    )
    fig.update_layout(**layout_kw)
    return fig


def chart_line_county(annual: pd.DataFrame) -> go.Figure:
    """Line chart: each county subsidiary's annual ridership."""
    fig = go.Figure()
    for sub in COUNTY_SUBS:
        sub_df = annual[annual["Subsidiary"] == sub].sort_values("Year")
        if sub_df.empty:
            continue
        color = SUB_COLORS.get(sub, COLOR_MUTED)
        label = sub.replace("RTS ", "")
        fig.add_trace(go.Scatter(
            x=sub_df["Year"],
            y=sub_df["Ridership"],
            mode="lines+markers",
            name=label,
            line=dict(color=color, width=2),
            marker=dict(size=6, color=color,
                        line=dict(width=1.5, color="white")),
            hovertemplate=(
                f"<b>{label} County</b><br>"
                "Year: %{x}<br>"
                "Unlinked Trips: %{y:,.0f}<extra></extra>"
            ),
        ))

    layout_kw = _base_layout(
        title=dict(
            text="Outer-County Transit Ridership Trends (2007–2024)",
            font=dict(family="'DM Sans', system-ui, sans-serif", size=16,
                      color=COLOR_DARK, weight="bold"),
            x=0.01, xanchor="left", y=0.97,
        ),
        xaxis_title="Year",
        yaxis_title="Annual Unlinked Trips",
        yaxis_tickformat=",",
        xaxis_dtick=2,
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5,
            font=dict(size=11, family="'DM Sans', sans-serif"),
        ),
        margin=dict(t=30, b=130, l=60, r=30),
    )
    fig.update_layout(**layout_kw)
    return fig


# -- BAR CHARTS -------------------------------------------------------

def chart_bar_county(annual: pd.DataFrame) -> go.Figure:
    """Bar chart: county subsidiaries + RTS Access, latest year."""
    latest_year = annual["Year"].max()
    subs = COUNTY_SUBS + ["RTS Access"]
    latest = annual[
        (annual["Year"] == latest_year) &
        (annual["Subsidiary"].isin(subs))
    ].copy()
    latest.sort_values("Ridership", ascending=False, inplace=True)

    labels = latest["Subsidiary"].str.replace("RTS ", "", regex=False)
    colors = [SUB_COLORS.get(s, COLOR_MUTED) for s in latest["Subsidiary"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels,
        y=latest["Ridership"],
        marker=dict(color=colors, cornerradius=4),
        text=[f"{v:,.0f}" for v in latest["Ridership"]],
        textposition="outside",
        textfont=dict(family="'DM Sans', sans-serif", size=11, color=COLOR_MUTED),
        hovertemplate="<b>%{x}</b><br>Unlinked Trips: %{y:,.0f}<extra></extra>",
    ))

    layout_kw = _base_layout(
        title=dict(
            text=f"Outer-County & Paratransit Ridership ({latest_year})",
            font=dict(family="'DM Sans', system-ui, sans-serif", size=16,
                      color=COLOR_DARK, weight="bold"),
            x=0.01, xanchor="left", y=0.97,
        ),
        yaxis_title="Annual Unlinked Trips",
        yaxis_tickformat=",",
        yaxis_range=[0, latest["Ridership"].max() * 1.2],
    )
    fig.update_layout(**layout_kw)
    return fig


def chart_bar_all(annual: pd.DataFrame) -> go.Figure:
    """Bar chart: ALL subsidiaries side by side, latest year."""
    latest_year = annual["Year"].max()
    latest = annual[annual["Year"] == latest_year].copy()
    latest.sort_values("Ridership", ascending=False, inplace=True)

    labels = latest["Subsidiary"].str.replace(
        "Regional Transit Service", "RTS Main (Monroe)", regex=False
    ).str.replace("RTS ", "", regex=False)
    colors = [SUB_COLORS.get(s, COLOR_MUTED) for s in latest["Subsidiary"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels,
        y=latest["Ridership"],
        marker=dict(color=colors, cornerradius=4),
        hovertemplate="<b>%{x}</b><br>Unlinked Trips: %{y:,.0f}<extra></extra>",
    ))

    layout_kw = _base_layout(
        title=dict(
            text=f"All RGRTA Ridership ({latest_year})",
            font=dict(family="'DM Sans', system-ui, sans-serif", size=16,
                      color=COLOR_DARK, weight="bold"),
            x=0.01, xanchor="left", y=0.97,
        ),
        yaxis_title="Annual Unlinked Trips",
        yaxis_tickformat=",",
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
<title>RGRTA Ridership — 8-County Rochester Region</title>
<style>{_css_base()}</style>
<script>
function switchChart() {{
    document.getElementById('chartFrame').src = 'charts/' + document.getElementById('chartSelector').value;
}}
</script>
</head><body>
<div class="card">
    <div class="header">
        <h2>RGRTA Ridership — Rochester Region</h2>
        <div class="controls-row">
            <select id="chartSelector" onchange="switchChart()">
                <optgroup label="Trends (2007-2024)">
                    <option value="line_rts_main_ridership.html">RTS Main (Monroe) — Trend</option>
                    <option value="line_county_ridership.html">Outer-County Services — Trends</option>
                </optgroup>
                <optgroup label="Latest Year Snapshot">
                    <option value="bar_all_ridership.html">All Subsidiaries</option>
                    <option value="bar_county_ridership.html">Outer-County & Paratransit</option>
                </optgroup>
            </select>
        </div>
    </div>
    <iframe id="chartFrame" src="charts/line_rts_main_ridership.html"></iframe>
</div>
</body></html>"""


# =====================================================================
# 4.  MAIN
# =====================================================================
def main():
    print("=" * 60)
    print("RGRTA Ridership Dashboard Builder")
    print("=" * 60)

    print(f"\n📂  Reading {INPUT_FILE} ...")
    df = load_ridership(INPUT_FILE)
    annual = annualize(df)
    latest_year = annual["Year"].max()
    print(f"    ✓ {len(df):,} monthly records, {annual['Year'].nunique()} years, "
          f"{annual['Subsidiary'].nunique()} subsidiaries (unified)")

    rts_latest = annual.loc[
        (annual["Subsidiary"] == "Regional Transit Service") &
        (annual["Year"] == latest_year), "Ridership"
    ].values[0]
    print(f"    RTS Main {latest_year}: {rts_latest:,} riders")

    # -- Line 1: RTS Main (Monroe) -----------------------------------
    fig = chart_line_rts_main(annual)
    p = os.path.join(CHARTS_DIR, "line_rts_main_ridership.html")
    write_chart_html(fig, p, SOURCE_TEXT)
    print(f"  ✓  {p}")

    # -- Line 2: County services -------------------------------------
    fig = chart_line_county(annual)
    p = os.path.join(CHARTS_DIR, "line_county_ridership.html")
    write_chart_html(fig, p, SOURCE_TEXT)
    print(f"  ✓  {p}")

    # -- Bar 1: County services --------------------------------------
    fig = chart_bar_county(annual)
    p = os.path.join(CHARTS_DIR, "bar_county_ridership.html")
    write_chart_html(fig, p, SOURCE_TEXT)
    print(f"  ✓  {p}")

    # -- Bar 2: All subsidiaries -------------------------------------
    fig = chart_bar_all(annual)
    p = os.path.join(CHARTS_DIR, "bar_all_ridership.html")
    write_chart_html(fig, p, SOURCE_TEXT)
    print(f"  ✓  {p}")

    # -- Dashboard wrapper -------------------------------------------
    dp = os.path.join(OUTPUT_DIR, "rgrta_ridership_dashboard.html")
    with open(dp, "w", encoding="utf-8") as f:
        f.write(build_dashboard_html())
    print(f"  ✓  {dp}")

    print(f"\n{'=' * 60}")
    print(f"Done — open {dp} in your browser.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()