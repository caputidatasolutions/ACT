"""
RGRTA On-Time Performance Dashboard Builder
=============================================
Reads RGRTA on-time percentage CSV, cleans and aggregates,
and produces interactive Plotly HTML dashboards matching the
ACT pipeline v2 visual style.

Charts come in pairs — RTS Main (Monroe) and County Services.

Outputs:
  Output/charts/line_rts_main_ontime.html          – RTS Main on-time trend
  Output/charts/line_county_ontime.html             – County services on-time trends
  Output/charts/bar_rts_main_ontime.html            – RTS Main bar (latest year)
  Output/charts/bar_county_ontime.html              – County services bar (latest year)
  Output/charts/bar_all_ontime.html                 – All subsidiaries bar
  Output/rgrta_ontime_dashboard.html                – Dashboard wrapper

Run:  python rgrta_ontime.py
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
    "Percentage_of_Buses_Running_On_Time___Beginning_2009_20260302.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "Output")
CHARTS_DIR = os.path.join(OUTPUT_DIR, "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
SOURCE_TEXT = (
    "Source: RGRTA via NY Open Data, Percentage of Buses Running On Time — Beginning 2009 "
    "(data.ny.gov/d/q8n5-wxz3) · "
    "Supplementary data: FTA National Transit Database (transit.dot.gov/ntd/ntd-data)"
)

# ---------------------------------------------------------------------------
# SUBSIDIARY MAPPING
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

COUNTY_SUBS = [
    "RTS Ontario", "RTS Wayne", "RTS Livingston", "RTS Genesee",
    "RTS Orleans", "RTS Seneca", "RTS Wyoming",
]


# =====================================================================
# 1.  LOAD & CLEAN
# =====================================================================
def load_ontime(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df.columns = [c.strip().strip('"') for c in df.columns]

    df["Subsidiary"] = df["Subsidiary"].str.strip().str.strip('"')
    df["Year"]  = df["Year"].astype(int)
    df["Month"] = df["Month"].astype(int)

    df["Pct"] = (
        df["Percent On-Time"].astype(str).str.strip().str.strip('"')
        .str.replace("%", "", regex=False)
    )
    df["Pct"] = pd.to_numeric(df["Pct"], errors="coerce")
    df.dropna(subset=["Pct"], inplace=True)

    df["Subsidiary"] = df["Subsidiary"].replace(SUB_RENAME)
    return df


def annual_avg(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["Subsidiary", "Year"])["Pct"]
        .mean()
        .round(1)
        .reset_index()
        .rename(columns={"Pct": "OnTimePct"})
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


def _ontime_line_layout(title_text, y_min=None):
    """Common layout elements for on-time line charts."""
    if y_min is None:
        y_min = 70
    return _base_layout(
        title=dict(
            text=title_text,
            font=dict(family="'DM Sans', system-ui, sans-serif", size=16,
                      color=COLOR_DARK, weight="bold"),
            x=0.01, xanchor="left", y=0.97,
        ),
        xaxis_title="Year",
        yaxis_title="% Buses On Time (Annual Avg)",
        yaxis_range=[y_min, 101],
        yaxis_ticksuffix="%",
        xaxis_dtick=1,
        margin=dict(t=50, b=100, l=50, r=30),
    )


# -- LINE CHARTS ------------------------------------------------------

def chart_line_rts_main(annual: pd.DataFrame) -> go.Figure:
    """Line chart: RTS Main on-time % trend."""
    rts = annual[annual["Subsidiary"] == "Regional Transit Service"].sort_values("Year")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=rts["Year"],
        y=rts["OnTimePct"],
        mode="lines+markers",
        name="RTS Main (Monroe)",
        line=dict(color=COLOR_PRIMARY, width=2.5),
        marker=dict(size=7, color=COLOR_PRIMARY,
                    line=dict(width=2, color="white")),
        hovertemplate=(
            "<b>RTS Main (Monroe)</b><br>"
            "Year: %{x}<br>"
            "On-Time: %{y:.1f}%<extra></extra>"
        ),
    ))

    y_min = max(70, rts["OnTimePct"].min() - 5)
    fig.update_layout(**_ontime_line_layout(
        "RTS Main — Monroe County On-Time Performance (2009–2024)", y_min
    ))
    return fig


def chart_line_county(annual: pd.DataFrame) -> go.Figure:
    """Line chart: each county subsidiary's on-time % trend."""
    fig = go.Figure()

    for sub in COUNTY_SUBS:
        sub_df = annual[annual["Subsidiary"] == sub].sort_values("Year")
        if sub_df.empty:
            continue
        color = SUB_COLORS.get(sub, COLOR_MUTED)
        label = sub.replace("RTS ", "")
        fig.add_trace(go.Scatter(
            x=sub_df["Year"],
            y=sub_df["OnTimePct"],
            mode="lines+markers",
            name=label,
            line=dict(color=color, width=2),
            marker=dict(size=6, color=color,
                        line=dict(width=1.5, color="white")),
            hovertemplate=(
                f"<b>{label} County</b><br>"
                "Year: %{x}<br>"
                "On-Time: %{y:.1f}%<extra></extra>"
            ),
        ))

    layout_kw = _ontime_line_layout(
        "Outer-County Transit On-Time Performance (2009–2024)", y_min=70
    )
    layout_kw.update(
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

def _make_ontime_bar(data: pd.DataFrame, title_text: str,
                     label_map=None) -> go.Figure:
    """Reusable bar chart builder for on-time snapshots."""
    data = data.sort_values("OnTimePct", ascending=False).copy()

    if label_map:
        labels = data["Subsidiary"].replace(label_map, regex=False)
    else:
        labels = data["Subsidiary"]
    labels = labels.str.replace("RTS ", "", regex=False)

    colors = [SUB_COLORS.get(s, COLOR_MUTED) for s in data["Subsidiary"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels,
        y=data["OnTimePct"],
        marker=dict(color=colors, cornerradius=4),
        text=[f"{v:.1f}%" for v in data["OnTimePct"]],
        textposition="outside",
        textfont=dict(family="'DM Sans', sans-serif", size=11, color=COLOR_MUTED),
        hovertemplate="<b>%{x}</b><br>On-Time: %{y:.1f}%<extra></extra>",
    ))

    layout_kw = _base_layout(
        title=dict(
            text=title_text,
            font=dict(family="'DM Sans', system-ui, sans-serif", size=16,
                      color=COLOR_DARK, weight="bold"),
            x=0.01, xanchor="left", y=0.97,
        ),
        yaxis_title="% Buses On Time",
        yaxis_range=[80, 102],
        yaxis_ticksuffix="%",
        margin=dict(t=50, b=100, l=50, r=30),
    )
    fig.update_layout(**layout_kw)
    return fig


def chart_bar_county(annual: pd.DataFrame) -> go.Figure:
    latest_year = annual["Year"].max()
    subs = COUNTY_SUBS + ["RTS Access"]
    data = annual[
        (annual["Year"] == latest_year) &
        (annual["Subsidiary"].isin(subs))
    ]
    return _make_ontime_bar(
        data, f"Outer-County & Paratransit On-Time ({latest_year})"
    )


def chart_bar_all(annual: pd.DataFrame) -> go.Figure:
    latest_year = annual["Year"].max()
    data = annual[annual["Year"] == latest_year]
    return _make_ontime_bar(
        data, f"All RGRTA On-Time Performance ({latest_year})",
        label_map={"Regional Transit Service": "RTS Main (Monroe)"},
    )


# =====================================================================
# 3.  DASHBOARD WRAPPER
# =====================================================================
def build_dashboard_html() -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>RGRTA On-Time Performance — Rochester Region</title>
<style>{_css_base()}</style>
<script>
function switchChart() {{
    document.getElementById('chartFrame').src = 'charts/' + document.getElementById('chartSelector').value;
}}
</script>
</head><body>
<div class="card">
    <div class="header">
        <h2>RGRTA On-Time Performance — Rochester Region</h2>
        <div class="controls-row">
            <select id="chartSelector" onchange="switchChart()">
                <optgroup label="Trends (2009-2024)">
                    <option value="line_rts_main_ontime.html">RTS Main (Monroe) — Trend</option>
                    <option value="line_county_ontime.html">Outer-County Services — Trends</option>
                </optgroup>
                <optgroup label="Latest Year Snapshot">
                    <option value="bar_all_ontime.html">All Subsidiaries</option>
                    <option value="bar_county_ontime.html">Outer-County & Paratransit</option>
                </optgroup>
            </select>
        </div>
    </div>
    <iframe id="chartFrame" src="charts/line_rts_main_ontime.html"></iframe>
</div>
</body></html>"""


# =====================================================================
# 4.  MAIN
# =====================================================================
def main():
    print("=" * 60)
    print("RGRTA On-Time Performance Dashboard Builder")
    print("=" * 60)

    print(f"\n📂  Reading {INPUT_FILE} ...")
    df = load_ontime(INPUT_FILE)
    annual = annual_avg(df)
    latest_year = annual["Year"].max()
    print(f"    ✓ {len(df):,} monthly records, {annual['Year'].nunique()} years")

    rts_latest = annual.loc[
        (annual["Subsidiary"] == "Regional Transit Service") &
        (annual["Year"] == latest_year), "OnTimePct"
    ].values[0]
    print(f"    RTS Main {latest_year} avg on-time: {rts_latest:.1f}%")

    charts = [
        ("line_rts_main_ontime.html",  chart_line_rts_main),
        ("line_county_ontime.html",    chart_line_county),
        ("bar_county_ontime.html",     chart_bar_county),
        ("bar_all_ontime.html",        chart_bar_all),
    ]

    for fname, builder in charts:
        fig = builder(annual)
        p = os.path.join(CHARTS_DIR, fname)
        write_chart_html(fig, p, SOURCE_TEXT)
        print(f"  ✓  {p}")

    dp = os.path.join(OUTPUT_DIR, "rgrta_ontime_dashboard.html")
    with open(dp, "w", encoding="utf-8") as f:
        f.write(build_dashboard_html())
    print(f"  ✓  {dp}")

    print(f"\n{'=' * 60}")
    print(f"Done — open {dp} in your browser.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()