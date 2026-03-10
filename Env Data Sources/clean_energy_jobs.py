"""
Clean Energy Jobs — ACT Dashboard Pipeline
============================================
Reads NYSERDA clean energy employment data and produces interactive
Plotly HTML dashboards that exactly match the ACT Census/ACS pipeline
visual style (pipeline_simple.py patterns).

Usage:
    python clean_energy_jobs.py

Output (all written to OUTPUT_DIR):
    bar_final_clean_energy_jobs.html  — bar dashboard wrapper
    map_final_clean_energy_jobs.html  — map dashboard wrapper
    charts/bar_county_clean_energy_jobs.html
    maps/map_county_clean_energy_jobs_desktop.html
    maps/map_county_clean_energy_jobs_mobile.html

Requires: pandas, plotly, openpyxl, geopandas
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ── Resolve paths ────────────────────────────────────────────────────
BASE_DIR   = r"C:\Users\camer\Desktop\ACT\Env Data Sources"
INPUT_FILE = os.path.join(BASE_DIR, "Clean Energy Jobs 2024.xlsx")
OUTPUT_DIR = os.path.join(BASE_DIR, "Output_Clean_Energy_Jobs")

# ── Import shared utils ─────────────────────────────────────────────
UTILS_DIR = os.path.join(BASE_DIR)
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
    warnings.warn(
        "Could not import utils.py — using inline fallback constants.",
        stacklevel=2,
    )
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
        [0.0, '#B3D4E8'],
        [0.35, '#3B8FCC'],
        [0.65, '#0062A3'],
        [1.0, '#1A2744'],
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
# CONSTANTS
# =====================================================================
VAR_NAME    = "clean_energy_jobs"
TITLE       = "Clean Energy Jobs (2024)"
SOURCE_TEXT = (
    "Source: NYSERDA, New York Clean Energy Industry Report — "
    "Employment Data Tables, Figure 9 (2024)"
)

# NY FIPS codes for Finger Lakes counties
COUNTY_FIPS = {
    "Monroe": "36055", "Orleans": "36073", "Genesee": "36037",
    "Livingston": "36051", "Ontario": "36069", "Wayne": "36117",
    "Yates": "36123", "Seneca": "36099",
}


# =====================================================================
# 1.  READ & CLEAN
# =====================================================================
print(f"\n── Reading {INPUT_FILE}")
if not os.path.exists(INPUT_FILE):
    sys.exit(f"[ERROR] File not found: {INPUT_FILE}")

raw = pd.read_excel(INPUT_FILE, sheet_name="Data", engine="openpyxl")
print(f"   Raw shape: {raw.shape}")
print(f"   Columns:   {list(raw.columns)}")

raw.columns = [c.strip() for c in raw.columns]
df = raw.rename(columns={raw.columns[0]: "County", raw.columns[1]: "estimate"}).copy()
df["County"] = df["County"].astype(str).str.strip().str.upper()
df["estimate"] = pd.to_numeric(df["estimate"], errors="coerce")
df = df.dropna(subset=["County", "estimate"])
df["estimate"] = df["estimate"].astype(int)
df["moe"] = 0  # NYSERDA data has no MOE

# Sort descending — matches pipeline_simple pattern
df = df.sort_values("estimate", ascending=False).reset_index(drop=True)
total_jobs = df["estimate"].sum()

print(f"\n── Cleaned: {len(df)} counties, {total_jobs:,} total clean energy jobs")
print(df[["County", "estimate"]].to_string(index=False))

# Create output directories (matches pipeline folder structure)
charts_dir = os.path.join(OUTPUT_DIR, "charts")
maps_dir   = os.path.join(OUTPUT_DIR, "maps")
os.makedirs(charts_dir, exist_ok=True)
os.makedirs(maps_dir, exist_ok=True)


# =====================================================================
# 2.  BAR CHART  (matches pipeline_simple.py exactly)
# =====================================================================
print("\n── Building bar chart: jobs by county")

file_bar_county = f"bar_county_{VAR_NAME}.html"

# get_bar_range equivalent for count data
max_val = df["estimate"].max() * 1.15
bar_range = [0, max_val]

fig = go.Figure(go.Bar(
    x=df["County"],
    y=df["estimate"],
    marker=dict(color=COLOR_PRIMARY, cornerradius=3, line=dict(width=0)),
    hovertemplate=(
        "<b>%{x}</b><br>"
        "Clean Energy Jobs: %{y:,.0f}"
        "<extra></extra>"
    ),
))

fig.update_layout(COMMON_LAYOUT)
fig.update_layout(
    xaxis_title="",
    yaxis_title="Clean Energy Jobs",
    margin=dict(t=20, b=80, l=55, r=20),
    yaxis=dict(showgrid=True, gridcolor=COLOR_GRID, gridwidth=1, griddash='dot',
               zeroline=False, range=bar_range, fixedrange=True),
    bargap=0.25,
)

write_chart_html(fig, os.path.join(charts_dir, file_bar_county), SOURCE_TEXT)
print(f"   Saved → charts/{file_bar_county}")


# ── Bar dashboard wrapper (simple_bar_html pattern) ──────────────────
bar_dashboard = f"""<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>{_css_base()}</style>
</head><body>
<div class="card">
    <div class="header">
        <h2>{TITLE}</h2>
    </div>
    <iframe id="chartFrame" src="charts/{file_bar_county}"></iframe>
</div></body></html>"""

bar_dash_path = os.path.join(OUTPUT_DIR, f"bar_final_{VAR_NAME}.html")
with open(bar_dash_path, "w", encoding="utf-8") as f:
    f.write(bar_dashboard)
print(f"   Saved → bar_final_{VAR_NAME}.html")


# =====================================================================
# 3.  MAP  (matches pipeline_simple.py — local shapefiles + geopandas)
# =====================================================================
print("\n── Building choropleth map: jobs by county")

import geopandas as gpd

# Map county names → GEOID (Census 5-digit FIPS) for shapefile join
COUNTY_GEOID = {
    "MONROE": "36055", "ORLEANS": "36073", "GENESEE": "36037",
    "LIVINGSTON": "36051", "ONTARIO": "36069", "WAYNE": "36117",
    "YATES": "36123", "SENECA": "36099",
}
df["GEOID"] = df["County"].map(COUNTY_GEOID)

# Load county shapes — same files the main pipeline uses
ACT_BASE = r"C:\Users\camer\Desktop\ACT"
shp_cty = os.path.join(ACT_BASE, "shapes", "most_recent_county_shapes.geojson")
cache_cty = shp_cty.replace(".geojson", "_simplified.geojson")

geo_loaded = False
try:
    if os.path.exists(cache_cty):
        gdf_cty = gpd.read_file(cache_cty)
        print(f"   [OK] Loaded cached county shapes")
    elif os.path.exists(shp_cty):
        gdf_cty = gpd.read_file(shp_cty)
        gdf_cty['geometry'] = gdf_cty['geometry'].simplify(tolerance=0.001, preserve_topology=True)
        print(f"   [OK] Loaded & simplified county shapes")
    else:
        print(f"   [WARN] County shapes not found at: {shp_cty}")
        print(f"   Skipping map generation.")
        gdf_cty = None

    if gdf_cty is not None:
        gdf_cty['GEOID'] = gdf_cty['GEOID'].astype(str)
        geo_loaded = True
except Exception as e:
    print(f"   [WARN] Could not load shapes: {e}")
    print(f"   Skipping map generation.")

if geo_loaded:
    import plotly.express as px

    # Merge data onto shapes — identical to pipeline_simple.py
    filtered_cty = gdf_cty.merge(df, on="GEOID")
    reg_center = {
        "lat": filtered_cty.geometry.centroid.y.mean(),
        "lon": filtered_cty.geometry.centroid.x.mean(),
    }

    def get_zoom(gdf, mode='desktop'):
        """Zoom calculator matching utils.py get_zoom()."""
        bounds = gdf.total_bounds
        max_span = max(bounds[2] - bounds[0], bounds[3] - bounds[1])
        if max_span == 0:
            return 10
        if mode == 'mobile':
            zoom = 7.1 - np.log2(max_span)
            return max(4.5, min(12.0, zoom))
        else:
            zoom = 8.1 - np.log2(max_span)
            return max(5.5, min(13.0, zoom))

    def save_map(gdf, zoom, center, filepath, label_col):
        """Build map — identical to pipeline_simple.py save_map()."""
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
                "Clean Energy Jobs: %{z:,.0f}"
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
                tickformat=",",
            ),
        )

        write_chart_html(fig_m, filepath, SOURCE_TEXT)

    # Desktop + mobile variants — matches pipeline pattern
    for mode in ('desktop', 'mobile'):
        map_path = os.path.join(maps_dir, f"map_county_{VAR_NAME}_{mode}.html")
        save_map(filtered_cty, get_zoom(filtered_cty, mode), reg_center,
                 map_path, "County")
        print(f"   Saved → maps/map_county_{VAR_NAME}_{mode}.html")

    # ── Map dashboard wrapper (simple_map_html pattern) ──────────────
    map_dashboard = f"""<!DOCTYPE html>
<html><head>
<title>{TITLE} Map</title>
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
    document.getElementById('mainFrame').src = "maps/map_county_{VAR_NAME}_" + currentDeviceMode + ".html";
}}
</script>
</head><body>
<div class="card">
    <div class="header">
        <h2>{TITLE}</h2>
        <div class="controls-row">
            <div class="toggle-container">
                <button id="btn-desktop" class="toggle-btn active" onclick="setDeviceMode('desktop')">Desktop</button>
                <button id="btn-mobile" class="toggle-btn" onclick="setDeviceMode('mobile')">Mobile</button>
            </div>
        </div>
    </div>
    <iframe id="mainFrame" src="maps/map_county_{VAR_NAME}_desktop.html"></iframe>
</div></body></html>"""

    map_dash_path = os.path.join(OUTPUT_DIR, f"map_final_{VAR_NAME}.html")
    with open(map_dash_path, "w", encoding="utf-8") as f:
        f.write(map_dashboard)
    print(f"   Saved → map_final_{VAR_NAME}.html")
    MAP_BUILT = True
else:
    MAP_BUILT = False


# =====================================================================
# 4.  SUMMARY
# =====================================================================
map_lines = ""
if MAP_BUILT:
    map_lines = (
        f"  maps/map_county_{VAR_NAME}_desktop.html  Choropleth (desktop)\n"
        f"  maps/map_county_{VAR_NAME}_mobile.html   Choropleth (mobile)\n"
        f"  map_final_{VAR_NAME}.html                Map dashboard wrapper\n"
    )

print(f"""
{'='*60}
  DONE — All outputs in: {OUTPUT_DIR}
{'='*60}
  charts/bar_county_{VAR_NAME}.html   Vertical bar chart
  bar_final_{VAR_NAME}.html           Bar dashboard wrapper
{map_lines}{'='*60}
  Open bar_final_{VAR_NAME}.html or map_final_{VAR_NAME}.html
  in a browser to view.
""")