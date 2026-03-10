"""
Asthma Dashboard — ACT Environmental Data Pipeline
====================================================
Reads NYSDOH Asthma Dashboard county data (snapshot + trend) and produces
interactive Plotly HTML dashboards matching the ACT Census/ACS pipeline
visual style (pipeline_simple.py patterns).

Usage:
    python asthma_dashboard.py

Input:
    AD-CountyMostRecentYearData.xlsx  — most recent snapshot by county
    AD-CountyTrendData.xlsx           — longitudinal trend data

Output (all written to OUTPUT_DIR):
    Per indicator:
      bar_final_<name>.html / charts/bar_county_<name>.html
      line_final_<name>.html / charts/line_county_<name>.html
      map_final_<name>.html / maps/map_county_<name>_{desktop,mobile}.html

Requires: pandas, plotly, openpyxl, geopandas, numpy
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ── Resolve paths ────────────────────────────────────────────────────
BASE_DIR   = r"C:\Users\camer\Desktop\ACT\Env Data Sources"
ACT_BASE   = r"C:\Users\camer\Desktop\ACT"
OUTPUT_DIR = os.path.join(BASE_DIR, "Output_Asthma")

FILE_SNAPSHOT = os.path.join(BASE_DIR, "AD-CountyMostRecentYearData.xlsx")
FILE_TREND    = os.path.join(BASE_DIR, "AD-CountyTrendData.xlsx")

# ── Import shared utils ─────────────────────────────────────────────
UTILS_DIR = BASE_DIR
if UTILS_DIR not in sys.path:
    sys.path.insert(0, UTILS_DIR)

try:
    from utils import (
        COLOR_PRIMARY, COLOR_PRIMARY_LT, COLOR_DARK, COLOR_ACCENT,
        COLOR_ERROR_BAR, COLOR_MUTED, COLOR_CHART_BG, COLOR_GRID,
        COLOR_PAGE_BG, COLOR_TEXT_MAIN,
        BRAND_COLOR_SCALE,
        FONT_BODY, FONT_HEADINGS,
        COMMON_LAYOUT, MOBILE_CONFIG,
        write_chart_html, _css_base,
    )
    print("[OK] Imported branding from utils.py")
except ImportError:
    warnings.warn("Could not import utils.py — using inline fallbacks.", stacklevel=2)
    COLOR_PRIMARY    = '#0062A3'
    COLOR_PRIMARY_LT = '#3B8FCC'
    COLOR_DARK       = '#1A2744'
    COLOR_ACCENT     = '#E8913A'
    COLOR_ERROR_BAR  = '#B0BEC5'
    COLOR_MUTED      = '#94A3B8'
    COLOR_CHART_BG   = '#FFFFFF'
    COLOR_GRID       = '#E8ECF0'
    COLOR_PAGE_BG    = '#F0F2F5'
    COLOR_TEXT_MAIN  = '#1A2744'
    FONT_BODY        = "Proxima Nova, sans-serif"
    FONT_HEADINGS    = "Freight Macro Pro, serif"
    BRAND_COLOR_SCALE = [
        [0.0, '#B3D4E8'], [0.35, '#3B8FCC'],
        [0.65, '#0062A3'], [1.0, '#1A2744'],
    ]
    COMMON_LAYOUT = dict(
        font_family=FONT_BODY, font_color=COLOR_TEXT_MAIN,
        paper_bgcolor=COLOR_CHART_BG, plot_bgcolor=COLOR_CHART_BG,
        margin=dict(t=30, b=100, l=50, r=30),
        xaxis=dict(showgrid=False, zeroline=False, showline=False,
                   tickfont=dict(family=FONT_BODY, size=11, color=COLOR_MUTED),
                   title_font=dict(family=FONT_BODY, size=12, color=COLOR_MUTED)),
        yaxis=dict(showgrid=True, gridcolor=COLOR_GRID, gridwidth=1, griddash='dot',
                   zeroline=False, showline=False,
                   tickfont=dict(family=FONT_BODY, size=11, color=COLOR_MUTED),
                   title_font=dict(family=FONT_BODY, size=12, color=COLOR_MUTED)),
        hoverlabel=dict(bgcolor="white", bordercolor=COLOR_PRIMARY,
                        font_size=13, font_family=FONT_BODY, font_color=COLOR_DARK),
    )
    MOBILE_CONFIG = {'displayModeBar': False, 'responsive': True, 'scrollZoom': False}

    def write_chart_html(fig, filepath, source_text, config=None):
        if config is None:
            config = MOBILE_CONFIG
        chart_html = fig.to_html(include_plotlyjs='cdn', config=config, full_html=True)
        source_footer = f"""
<style>
  html, body {{ margin:0; padding:0; width:100%; height:100%;
               overflow:hidden; display:flex; flex-direction:column; }}
  .plotly-graph-div {{ width:100% !important; flex:1 1 auto !important; }}
  .source-footer {{ flex:0 0 auto; padding:4px 12px 6px 12px;
      font-family:'DM Sans','{FONT_BODY}',sans-serif; font-size:9px;
      color:{COLOR_MUTED}; background:#fff;
      border-top:1px solid {COLOR_GRID};
      white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
</style>
<script>
  window.addEventListener('load',function(){{ window.dispatchEvent(new Event('resize')); }});
  window.addEventListener('resize',function(){{
    var gd=document.querySelector('.plotly-graph-div');
    if(gd){{ var f=document.querySelector('.source-footer');
      var fH=f?f.offsetHeight:0;
      Plotly.relayout(gd,{{ height:window.innerHeight-fH }}); }}
  }});
</script>
<div class="source-footer">{source_text}</div>
"""
        chart_html = chart_html.replace('</body>', source_footer + '</body>')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(chart_html)

    def _css_base():
        return f"""
            @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap');
            *, *::before, *::after {{ box-sizing: border-box; }}
            html, body {{ margin: 0; padding: 0; height: 100%; width: 100%;
                          font-family: 'DM Sans', '{FONT_BODY}', system-ui, sans-serif;
                          background-color: {COLOR_PAGE_BG}; overflow: hidden; color: {COLOR_DARK}; }}
            .card {{ display: flex; flex-direction: column; height: 100dvh; width: 100%;
                     background: {COLOR_CHART_BG}; }}
            .header {{ flex: 0 0 auto; padding: 12px 20px;
                       border-bottom: 2px solid {COLOR_GRID};
                       display: flex; flex-wrap: wrap; gap: 12px;
                       justify-content: space-between; align-items: center;
                       background: #fff; z-index: 10; }}
            .controls-row {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }}
            iframe {{ flex: 1 1 auto; width: 100%; border: none; display: block; }}
            h2 {{ margin: 0; color: {COLOR_DARK}; font-family: 'DM Sans', '{FONT_HEADINGS}', serif;
                  font-size: 1.05rem; font-weight: 600; letter-spacing: -0.01em; }}
            select {{ padding: 7px 12px; font-size: 13px; font-family: 'DM Sans', sans-serif;
                      font-weight: 500; border-radius: 6px; border: 1.5px solid {COLOR_GRID};
                      color: {COLOR_DARK}; background-color: #FAFBFC; cursor: pointer;
                      transition: border-color 0.15s, box-shadow 0.15s; outline: none; }}
            select:hover {{ border-color: {COLOR_PRIMARY_LT}; }}
            select:focus {{ border-color: {COLOR_PRIMARY}; box-shadow: 0 0 0 3px rgba(0,98,163,0.10); }}
            .toggle-container {{ display: flex; align-items: center; font-size: 12px;
                                 border: 1.5px solid {COLOR_GRID}; border-radius: 6px; overflow: hidden; }}
            .toggle-btn {{ padding: 7px 14px; cursor: pointer; background: #FAFBFC;
                           border: none; outline: none; font-family: 'DM Sans', sans-serif;
                           font-weight: 500; font-size: 12px; color: {COLOR_MUTED};
                           transition: all 0.15s; }}
            .toggle-btn:hover {{ background: #F0F2F5; }}
            .toggle-btn.active {{ background: {COLOR_PRIMARY}; color: white; }}
        """


# =====================================================================
# CONFIGURATION — Indicators to chart
# =====================================================================
# Each entry: (indicator_name_in_data, short_title, y_label, safe_filename_slug)
# We pick the most policy-relevant headline indicators.
INDICATORS = [
    (
        "Age-adjusted asthma emergency department visit rate per 10,000",
        "Age-Adjusted Asthma ED Visit Rate",
        "Rate per 10,000",
        "asthma_ed_age_adj",
    ),
    (
        "Age-adjusted asthma hospitalization rate per 10,000",
        "Age-Adjusted Asthma Hospitalization Rate",
        "Rate per 10,000",
        "asthma_hosp_age_adj",
    ),
    (
        "Age-adjusted asthma death rate per 1,000,000",
        "Age-Adjusted Asthma Death Rate",
        "Rate per 1,000,000",
        "asthma_death_age_adj",
    ),
    (
        "Asthma emergency department visit rate per 10,000 - aged 0-17 years",
        "Asthma ED Visit Rate (Children 0-17)",
        "Rate per 10,000",
        "asthma_ed_0_17",
    ),
    (
        "Asthma emergency department visit rate per 10,000 - aged 18-64 years",
        "Asthma ED Visit Rate (Adults 18-64)",
        "Rate per 10,000",
        "asthma_ed_18_64",
    ),
    (
        "Asthma emergency department visit rate per 10,000 - aged 65+ years",
        "Asthma ED Visit Rate (Seniors 65+)",
        "Rate per 10,000",
        "asthma_ed_65plus",
    ),
    (
        "Asthma hospitalization rate per 10,000 - aged 0-17 years",
        "Asthma Hospitalization Rate (Children 0-17)",
        "Rate per 10,000",
        "asthma_hosp_0_17",
    ),
    (
        "Total asthma hospitalization rate per 10,000",
        "Total Asthma Hospitalization Rate",
        "Rate per 10,000",
        "asthma_hosp_total",
    ),
]

# ACT region — 8 counties
FL_COUNTIES = [
    "Genesee", "Livingston", "Monroe", "Ontario",
    "Orleans", "Seneca", "Wayne", "Yates",
]

# County name → Census GEOID for shapefile joins
COUNTY_GEOID = {
    "GENESEE": "36037", "LIVINGSTON": "36051", "MONROE": "36055",
    "ONTARIO": "36069", "ORLEANS": "36073", "SENECA": "36099",
    "WAYNE": "36117", "YATES": "36123",
}

SOURCE_TEXT = "Source: NYSDOH Asthma Dashboard, SPARCS data as of July 2024"


def _safe(name):
    return name.replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '').replace(',', '')


def clean_rate(val):
    """Convert rate values to float, handling 's' (suppressed) and '*' (flagged)."""
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    if s.lower() == 's' or s == '.' or s == '':
        return np.nan
    s = s.replace('*', '')
    try:
        return float(s)
    except ValueError:
        return np.nan


# =====================================================================
# 1.  READ & CLEAN
# =====================================================================
print(f"\n── Reading data files...")
for f in [FILE_SNAPSHOT, FILE_TREND]:
    if not os.path.exists(f):
        sys.exit(f"[ERROR] File not found: {f}")

df_snap = pd.read_excel(FILE_SNAPSHOT, header=2, engine="openpyxl")
df_trend = pd.read_excel(FILE_TREND, header=2, engine="openpyxl")
print(f"   Snapshot: {df_snap.shape[0]:,} rows, Trend: {df_trend.shape[0]:,} rows")

def prep_df(raw, label):
    """Clean and filter to our 8 ACT counties."""
    d = raw.copy()
    # Filter by county name (not region — Genesee/Orleans are in 'Western NY')
    d = d[d['County'].isin(FL_COUNTIES)]

    # Clean rates
    d['rate'] = d['Percent or Rate'].apply(clean_rate)
    d['state_rate'] = d['State Rate'].apply(clean_rate)
    d['region_rate'] = d['Region Rate'].apply(clean_rate)

    # Uppercase county for shapefile join consistency
    d['County_upper'] = d['County'].str.upper()
    d['GEOID'] = d['County_upper'].map(COUNTY_GEOID)

    print(f"   {label}: {len(d)} Finger Lakes county rows, "
          f"{d['rate'].notna().sum()} with valid rates")
    return d

df_snap_fl = prep_df(df_snap, "Snapshot")
df_trend_fl = prep_df(df_trend, "Trend")

# Create output directories
charts_dir = os.path.join(OUTPUT_DIR, "charts")
maps_dir   = os.path.join(OUTPUT_DIR, "maps")
os.makedirs(charts_dir, exist_ok=True)
os.makedirs(maps_dir, exist_ok=True)


# =====================================================================
# 2.  LOAD SHAPES (for maps)
# =====================================================================
print("\n── Loading county shapes...")
import geopandas as gpd

shp_cty = os.path.join(ACT_BASE, "shapes", "most_recent_county_shapes.geojson")
cache_cty = shp_cty.replace(".geojson", "_simplified.geojson")

gdf_cty = None
try:
    if os.path.exists(cache_cty):
        gdf_cty = gpd.read_file(cache_cty)
        print("   [OK] Loaded cached county shapes")
    elif os.path.exists(shp_cty):
        gdf_cty = gpd.read_file(shp_cty)
        gdf_cty['geometry'] = gdf_cty['geometry'].simplify(tolerance=0.001, preserve_topology=True)
        print("   [OK] Loaded & simplified county shapes")
    else:
        print(f"   [WARN] Shapes not found — skipping maps")
except Exception as e:
    print(f"   [WARN] Could not load shapes: {e}")

if gdf_cty is not None:
    gdf_cty['GEOID'] = gdf_cty['GEOID'].astype(str)


def get_zoom(gdf, mode='desktop'):
    bounds = gdf.total_bounds
    max_span = max(bounds[2] - bounds[0], bounds[3] - bounds[1])
    if max_span == 0:
        return 10
    if mode == 'mobile':
        return max(4.5, min(12.0, 7.1 - np.log2(max_span)))
    return max(5.5, min(13.0, 8.1 - np.log2(max_span)))


# =====================================================================
# 3.  PROCESS EACH INDICATOR
# =====================================================================
import plotly.express as px

ok_count = 0

for indicator_name, title, y_label, slug in INDICATORS:
    print(f"\n{'─'*60}")
    print(f"  [{slug}] {title}")

    # ── Filter snapshot data for this indicator ──────────────────────
    # Some indicators have multiple data-year rows; pick the most recent
    # 3-year rolling window (contains '-') as the primary
    snap = df_snap_fl[df_snap_fl['Indicator'] == indicator_name].copy()

    if snap.empty:
        print(f"  SKIPPED — no snapshot data for this indicator")
        continue

    # Prefer 3-year rolling window rows; fall back to single-year
    rolling = snap[snap['Data Years'].astype(str).str.contains('-')]
    if not rolling.empty:
        # Pick the latest rolling window
        latest_window = sorted(rolling['Data Years'].astype(str).unique())[-1]
        snap = rolling[rolling['Data Years'].astype(str) == latest_window]
    else:
        snap = snap.drop_duplicates(subset=['County'], keep='last')

    snap = snap.dropna(subset=['rate'])
    data_years = snap['Data Years'].iloc[0] if len(snap) > 0 else ""

    if snap.empty:
        print(f"  SKIPPED — all rates suppressed/missing")
        continue

    snap = snap.sort_values('rate', ascending=False).reset_index(drop=True)
    src_text = f"{SOURCE_TEXT} ({data_years})"
    max_rate = snap['rate'].max() * 1.15

    print(f"  Snapshot: {len(snap)} counties, data years={data_years}")

    # ── BAR CHART (pipeline_simple.py pattern) ───────────────────────
    file_bar = f"bar_county_{slug}.html"

    fig_bar = go.Figure(go.Bar(
        x=snap['County'], y=snap['rate'],
        marker=dict(color=COLOR_PRIMARY, cornerradius=3, line=dict(width=0)),
        hovertemplate=(
            "<b>%{x}</b><br>"
            f"{y_label}: %{{y:,.1f}}<br>"
            "Concern: %{customdata[0]}<br>"
            f"State Rate: %{{customdata[1]:.1f}}"
            "<extra></extra>"
        ),
        customdata=snap[['Concern Level', 'state_rate']].values,
    ))

    fig_bar.update_layout(COMMON_LAYOUT)
    fig_bar.update_layout(
        xaxis_title="", yaxis_title=y_label,
        margin=dict(t=20, b=80, l=55, r=20),
        yaxis=dict(showgrid=True, gridcolor=COLOR_GRID, gridwidth=1, griddash='dot',
                   zeroline=False, range=[0, max_rate], fixedrange=True),
        bargap=0.25,
    )

    write_chart_html(fig_bar, os.path.join(charts_dir, file_bar), src_text)
    print(f"    bar  → charts/{file_bar}")

    # ── Bar dashboard wrapper ────────────────────────────────────────
    bar_dash = f"""<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>{_css_base()}</style>
</head><body>
<div class="card">
    <div class="header">
        <h2>{title} ({data_years})</h2>
    </div>
    <iframe id="chartFrame" src="charts/{file_bar}"></iframe>
</div></body></html>"""

    with open(os.path.join(OUTPUT_DIR, f"bar_final_{slug}.html"), "w", encoding="utf-8") as f:
        f.write(bar_dash)

    # ── LINE CHART (trend data — pipeline_simple.py pattern) ─────────
    trend = df_trend_fl[df_trend_fl['Indicator'] == indicator_name].copy()

    if not trend.empty:
        # Use only 3-year rolling windows for clean trend lines
        trend_rolling = trend[trend['Data Years'].astype(str).str.contains('-')].copy()
        if trend_rolling.empty:
            trend_rolling = trend.copy()

        trend_rolling = trend_rolling.dropna(subset=['rate'])

        # Extract the end year from the data period for X-axis ordering
        def end_year(dy):
            s = str(dy)
            if '-' in s:
                return int(s.split('-')[-1])
            try:
                return int(s)
            except ValueError:
                return 0

        trend_rolling['end_year'] = trend_rolling['Data Years'].apply(end_year)
        trend_rolling = trend_rolling.sort_values('end_year')

        unique_counties = sorted(trend_rolling['County'].unique())

        if unique_counties:
            file_line = f"line_county_{slug}.html"
            fig_line = go.Figure()

            # Compute initial Y range from first county
            first_data = trend_rolling[trend_rolling['County'] == unique_counties[0]]
            if not first_data.empty:
                rmin = first_data['rate'].min()
                rmax = first_data['rate'].max()
                span = rmax - rmin if rmax > rmin else 5
                init_range = [max(0, rmin - span * 0.12), rmax + span * 0.12]
            else:
                init_range = [0, 100]

            for i, county in enumerate(unique_counties):
                cdata = trend_rolling[trend_rolling['County'] == county]
                fig_line.add_trace(go.Scatter(
                    x=cdata['Data Years'].astype(str),
                    y=cdata['rate'],
                    mode='lines+markers',
                    name=county,
                    visible=(i == 0),
                    line=dict(color=COLOR_PRIMARY, width=2.5),
                    marker=dict(size=8, color=COLOR_PRIMARY,
                                line=dict(width=2, color='white')),
                    hovertemplate=(
                        f"<b>{y_label}: %{{y:,.1f}}</b><br>"
                        "Period: %{x}<br>"
                        "Concern: %{customdata[0]}"
                        "<extra></extra>"
                    ),
                    customdata=cdata[['Concern Level']].values,
                ))

            county_btns = []
            for i, county in enumerate(unique_counties):
                vis = [False] * len(unique_counties)
                vis[i] = True
                cdata = trend_rolling[trend_rolling['County'] == county]
                if not cdata.empty:
                    rmin = cdata['rate'].min()
                    rmax = cdata['rate'].max()
                    span = rmax - rmin if rmax > rmin else 5
                    r = [max(0, rmin - span * 0.12), rmax + span * 0.12]
                else:
                    r = [0, 100]
                county_btns.append(dict(
                    label=county, method="update",
                    args=[{"visible": vis}, {"yaxis.range": r}],
                ))

            fig_line.update_layout(COMMON_LAYOUT)
            fig_line.update_layout(
                xaxis_title="Data Period", yaxis_title=y_label,
                margin=dict(t=90, b=50, l=55, r=20),
                showlegend=False,
                updatemenus=[dict(
                    active=0, buttons=county_btns,
                    x=1.0, y=1.22, xanchor='right', yanchor='top',
                    bgcolor='white', bordercolor=COLOR_GRID, borderwidth=1.5,
                    font=dict(family="DM Sans, sans-serif", size=12),
                )],
                yaxis=dict(showgrid=True, gridcolor=COLOR_GRID, gridwidth=1,
                           griddash='dot', zeroline=False, range=init_range,
                           fixedrange=True),
            )

            src_trend = f"{SOURCE_TEXT} ({trend_rolling['Data Years'].iloc[0]}–{trend_rolling['Data Years'].iloc[-1]})"
            write_chart_html(fig_line, os.path.join(charts_dir, file_line), src_trend)
            print(f"    line → charts/{file_line}")

            # ── Line dashboard wrapper (simple_line_html pattern) ────
            line_dash = f"""<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>{_css_base()}</style>
</head><body>
<div class="card">
    <div class="header">
        <h2>{title} — Trends</h2>
    </div>
    <iframe id="chartFrame" src="charts/{file_line}"></iframe>
</div></body></html>"""

            with open(os.path.join(OUTPUT_DIR, f"line_final_{slug}.html"), "w", encoding="utf-8") as f:
                f.write(line_dash)

    # ── MAP (pipeline_simple.py choropleth_mapbox pattern) ───────────
    if gdf_cty is not None:
        map_data = snap.copy()
        map_data['estimate'] = map_data['rate']
        map_data['moe'] = 0

        filtered_cty = gdf_cty.merge(map_data, on="GEOID")

        if not filtered_cty.empty:
            reg_center = {
                "lat": filtered_cty.geometry.centroid.y.mean(),
                "lon": filtered_cty.geometry.centroid.x.mean(),
            }

            def save_map(gdf, zoom, center, filepath, label_col):
                clean = gdf[gdf['estimate'] > 0].copy()
                if clean.empty:
                    return
                fig_m = px.choropleth_mapbox(
                    clean,
                    geojson=clean.set_index("GEOID").geometry,
                    locations="GEOID",
                    color="estimate",
                    hover_name=label_col,
                    hover_data=["moe"],
                    mapbox_style="carto-positron",
                    opacity=0.85,
                    zoom=zoom,
                    center=center,
                    color_continuous_scale=BRAND_COLOR_SCALE,
                )
                fig_m.update_traces(
                    hovertemplate=(
                        "<b>%{hovertext}</b><br>"
                        f"{y_label}: %{{z:,.1f}}"
                        "<extra></extra>"
                    ),
                )
                fig_m.update_layout(COMMON_LAYOUT)
                fig_m.update_layout(
                    margin={"r": 0, "t": 0, "l": 0, "b": 0},
                    coloraxis_colorbar=dict(
                        title="", len=0.45, thickness=14,
                        yanchor="bottom", y=0.06,
                        xanchor="right", x=0.96,
                        bgcolor="rgba(255,255,255,0.85)",
                        outlinewidth=0,
                        tickfont=dict(size=10, color=COLOR_MUTED),
                    ),
                )
                write_chart_html(fig_m, filepath, src_text)

            for mode in ('desktop', 'mobile'):
                map_path = os.path.join(maps_dir, f"map_county_{slug}_{mode}.html")
                save_map(filtered_cty, get_zoom(filtered_cty, mode),
                         reg_center, map_path, "County")
                print(f"    map  → maps/map_county_{slug}_{mode}.html")

            # ── Map dashboard wrapper (simple_map_html pattern) ──────
            map_dash = f"""<!DOCTYPE html>
<html><head>
<title>{title} Map</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>{_css_base()} iframe {{ height: 100%; }}
select {{ max-width: 160px; }}</style>
<script>
var currentDeviceMode = 'desktop';
function setDeviceMode(mode) {{
    currentDeviceMode = mode;
    document.getElementById('btn-desktop').classList.toggle('active', mode === 'desktop');
    document.getElementById('btn-mobile').classList.toggle('active', mode === 'mobile');
    updateMapSource();
}}
function updateMapSource() {{
    document.getElementById('mainFrame').src = "maps/map_county_{slug}_" + currentDeviceMode + ".html";
}}
</script>
</head><body>
<div class="card">
    <div class="header">
        <h2>{title} ({data_years})</h2>
        <div class="controls-row">
            <div class="toggle-container">
                <button id="btn-desktop" class="toggle-btn active" onclick="setDeviceMode('desktop')">Desktop</button>
                <button id="btn-mobile" class="toggle-btn" onclick="setDeviceMode('mobile')">Mobile</button>
            </div>
        </div>
    </div>
    <iframe id="mainFrame" src="maps/map_county_{slug}_desktop.html"></iframe>
</div></body></html>"""

            with open(os.path.join(OUTPUT_DIR, f"map_final_{slug}.html"), "w", encoding="utf-8") as f:
                f.write(map_dash)

            # ── CONCERN LEVEL MAP (categorical choropleth) ───────────
            concern_data = filtered_cty.copy()
            concern_data = concern_data[concern_data['Concern Level'] != 'Suppressed']

            if not concern_data.empty:
                # Map concern levels to numeric values for choropleth coloring
                CONCERN_ORDER = {"Low Concern": 0, "Moderate Concern": 1, "High Concern": 2}
                CONCERN_COLORS = {
                    "Low Concern": "#16A34A",       # Green
                    "Moderate Concern": "#F59E0B",   # Amber
                    "High Concern": "#DC2626",       # Red
                }
                # Discrete colorscale: green → amber → red
                concern_colorscale = [
                    [0.0,  "#16A34A"],
                    [0.5,  "#F59E0B"],
                    [1.0,  "#DC2626"],
                ]

                concern_data['concern_num'] = concern_data['Concern Level'].map(CONCERN_ORDER)
                concern_data = concern_data.dropna(subset=['concern_num'])

                def save_concern_map(gdf, zoom, center, filepath, label_col):
                    fig_cm = px.choropleth_mapbox(
                        gdf,
                        geojson=gdf.set_index("GEOID").geometry,
                        locations="GEOID",
                        color="concern_num",
                        hover_name=label_col,
                        mapbox_style="carto-positron",
                        opacity=0.85,
                        zoom=zoom,
                        center=center,
                        color_continuous_scale=concern_colorscale,
                        range_color=[0, 2],
                    )
                    fig_cm.update_traces(
                        hovertemplate=(
                            "<b>%{hovertext}</b><br>"
                            "Concern: %{customdata[0]}<br>"
                            f"{y_label}: %{{customdata[1]:.1f}}"
                            "<extra></extra>"
                        ),
                        customdata=gdf[['Concern Level', 'rate']].values,
                    )
                    fig_cm.update_layout(COMMON_LAYOUT)
                    fig_cm.update_layout(
                        margin={"r": 0, "t": 0, "l": 0, "b": 0},
                        coloraxis_colorbar=dict(
                            title="", len=0.35, thickness=14,
                            yanchor="bottom", y=0.06,
                            xanchor="right", x=0.96,
                            bgcolor="rgba(255,255,255,0.85)",
                            outlinewidth=0,
                            tickvals=[0, 1, 2],
                            ticktext=["Low", "Moderate", "High"],
                            tickfont=dict(size=10, color=COLOR_MUTED),
                        ),
                    )
                    write_chart_html(fig_cm, filepath, src_text)

                for mode in ('desktop', 'mobile'):
                    cmap_path = os.path.join(maps_dir, f"map_concern_{slug}_{mode}.html")
                    save_concern_map(concern_data, get_zoom(concern_data, mode),
                                     reg_center, cmap_path, "County")
                    print(f"    cmap → maps/map_concern_{slug}_{mode}.html")

                # ── Concern map dashboard wrapper ────────────────────
                concern_dash = f"""<!DOCTYPE html>
<html><head>
<title>{title} — Concern Level Map</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>{_css_base()} iframe {{ height: 100%; }}
select {{ max-width: 160px; }}</style>
<script>
var currentDeviceMode = 'desktop';
function setDeviceMode(mode) {{
    currentDeviceMode = mode;
    document.getElementById('btn-desktop').classList.toggle('active', mode === 'desktop');
    document.getElementById('btn-mobile').classList.toggle('active', mode === 'mobile');
    updateMapSource();
}}
function updateMapSource() {{
    document.getElementById('mainFrame').src = "maps/map_concern_{slug}_" + currentDeviceMode + ".html";
}}
</script>
</head><body>
<div class="card">
    <div class="header">
        <h2>{title} — Concern Level ({data_years})</h2>
        <div class="controls-row">
            <div class="toggle-container">
                <button id="btn-desktop" class="toggle-btn active" onclick="setDeviceMode('desktop')">Desktop</button>
                <button id="btn-mobile" class="toggle-btn" onclick="setDeviceMode('mobile')">Mobile</button>
            </div>
        </div>
    </div>
    <iframe id="mainFrame" src="maps/map_concern_{slug}_desktop.html"></iframe>
</div></body></html>"""

                with open(os.path.join(OUTPUT_DIR, f"concern_map_final_{slug}.html"), "w", encoding="utf-8") as f:
                    f.write(concern_dash)

    ok_count += 1
    print(f"  [{slug}] Done")


# =====================================================================
# 4.  SUMMARY
# =====================================================================
print(f"""
{'='*60}
  DONE — {ok_count} indicators processed
  All outputs in: {OUTPUT_DIR}
{'='*60}
  Each indicator has:
    bar_final_<name>.html   → Bar chart dashboard
    line_final_<name>.html  → Trend line dashboard
    map_final_<name>.html   → Choropleth map dashboard
{'='*60}
""")