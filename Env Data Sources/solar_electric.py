"""
Solar Electric Programs — ACT Environmental Data Pipeline
==========================================================
Reads NYSERDA Solar Electric Programs data and produces interactive
Plotly HTML dashboards matching the ACT pipeline visual style.

Charts produced:
  1. Stacked bar: Project count by county, stacked by Project Status (+ % toggle)
  2. Stacked bar: Total kW DC by county, stacked by Project Status (+ % toggle)
  3. Map: Completed project count by county
  4. Map: Completed solar capacity (kW DC) by county

Usage:
    python solar_electric.py

Requires: pandas, plotly, geopandas, numpy
"""

import os
import sys
import warnings
import glob
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ── Resolve paths ────────────────────────────────────────────────────
BASE_DIR   = r"C:\Users\camer\Desktop\ACT\Env Data Sources"
ACT_BASE   = r"C:\Users\camer\Desktop\ACT"
OUTPUT_DIR = os.path.join(BASE_DIR, "Output_Solar_Electric")

_candidates = glob.glob(os.path.join(BASE_DIR, "Solar*Electric*Program*.*"))
if _candidates:
    INPUT_FILE = _candidates[0]
else:
    INPUT_FILE = os.path.join(BASE_DIR, "Solar_Electric_Programs_Reported_by_NYSERDA__Beginning.csv")

# ── Import shared utils ─────────────────────────────────────────────
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

_UTILS_LOADED = False
try:
    from utils import (
        COLOR_PRIMARY, COLOR_PRIMARY_LT, COLOR_DARK, COLOR_ACCENT,
        COLOR_ERROR_BAR, COLOR_MUTED, COLOR_CHART_BG, COLOR_GRID,
        COLOR_PAGE_BG, COLOR_TEXT_MAIN,
        FONT_BODY, FONT_HEADINGS,
        COMMON_LAYOUT, MOBILE_CONFIG,
        write_chart_html,
    )
    _UTILS_LOADED = True
    print("[OK] Imported branding from utils.py")
    try:
        from utils import BRAND_COLOR_SCALE
    except ImportError:
        BRAND_COLOR_SCALE = [
            [0.0, '#B3D4E8'], [0.35, '#3B8FCC'],
            [0.65, '#0062A3'], [1.0, '#1A2744'],
        ]
    try:
        from utils import _css_base
    except ImportError:
        pass  # Defined below
except Exception as e:
    print(f"[WARN] utils.py import failed: {e}")
    print("       Using inline fallback constants.")
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

# Always define _css_base if not already imported
if '_css_base' not in dir():
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
ACT_COUNTIES = [
    "Genesee", "Livingston", "Monroe", "Ontario",
    "Orleans", "Seneca", "Wayne", "Yates",
]

COUNTY_GEOID = {
    "GENESEE": "36037", "LIVINGSTON": "36051", "MONROE": "36055",
    "ONTARIO": "36069", "ORLEANS": "36073", "SENECA": "36099",
    "WAYNE": "36117", "YATES": "36123",
}

SOURCE_TEXT = "Source: NYSERDA, Solar Electric Programs Reported by NYSERDA"

# Colors for Project Status
STATUS_ORDER  = ["Complete", "Pipeline"]
STATUS_COLORS = {
    "Complete": COLOR_PRIMARY,   # Branded blue
    "Pipeline": "#93C5FD",       # Light blue
}


# =====================================================================
# 1.  READ & CLEAN
# =====================================================================
print(f"\n── Reading {INPUT_FILE}")
if not os.path.exists(INPUT_FILE):
    sys.exit(f"[ERROR] File not found: {INPUT_FILE}")

raw = pd.read_csv(INPUT_FILE, low_memory=False)
df = raw[raw['County'].isin(ACT_COUNTIES)].copy()
df['kw'] = pd.to_numeric(df['Total Nameplate kW DC'], errors='coerce').fillna(0)
print(f"   {len(df)} projects across {df['County'].nunique()} counties")

# Build county-level summary
county_rows = []
for county in sorted(df['County'].unique()):
    sub = df[df['County'] == county]
    total_n = len(sub)
    total_kw = sub['kw'].sum()

    row = {'County': county, 'total_n': total_n, 'total_kw': total_kw}

    for status in STATUS_ORDER:
        s = sub[sub['Project Status'] == status]
        row[f"n_{status}"] = len(s)
        row[f"kw_{status}"] = s['kw'].sum()
        row[f"pct_n_{status}"] = round(len(s) / total_n * 100, 1) if total_n else 0
        row[f"pct_kw_{status}"] = round(s['kw'].sum() / total_kw * 100, 1) if total_kw else 0

    county_rows.append(row)

cs = pd.DataFrame(county_rows)
cs = cs.sort_values('total_n', ascending=False).reset_index(drop=True)
cs['County_upper'] = cs['County'].str.upper()
cs['GEOID'] = cs['County_upper'].map(COUNTY_GEOID)

print(cs[['County', 'total_n', 'n_Complete', 'n_Pipeline', 'total_kw']].to_string(index=False))

# Create output directories
charts_dir = os.path.join(OUTPUT_DIR, "charts")
maps_dir   = os.path.join(OUTPUT_DIR, "maps")
os.makedirs(charts_dir, exist_ok=True)
os.makedirs(maps_dir, exist_ok=True)


# =====================================================================
# HELPER: Build a stacked bar pair (count + %) and dashboard wrapper
# =====================================================================
def build_stacked_bar(cs_df, value_col_prefix, y_label_count, y_label_pct,
                      file_count, file_pct, file_dash, dash_title):
    """Build count + pct stacked bars and dashboard wrapper."""

    # --- Count version ---
    fig_count = go.Figure()
    for status in STATUS_ORDER:
        col = f"{value_col_prefix}_{status}"
        fig_count.add_trace(go.Bar(
            x=cs_df['County'], y=cs_df[col], name=status,
            marker=dict(color=STATUS_COLORS[status], cornerradius=3, line=dict(width=0)),
            hovertemplate=(
                f"<b>%{{x}}</b><br>{status}: %{{y:,.0f}}<br>"
                f"Total: %{{customdata[0]:,.0f}}<extra></extra>"
            ),
            customdata=cs_df[[f"total_{value_col_prefix.split('_')[-1]}".replace('_n', '_n').replace('_kw', '_kw')]].values
            if False else cs_df[['total_n' if 'n' in value_col_prefix else 'total_kw']].values,
        ))

    fig_count.update_layout(COMMON_LAYOUT)
    fig_count.update_layout(
        barmode='stack',
        xaxis_title="", yaxis_title=y_label_count,
        margin=dict(t=20, b=80, l=65, r=20),
        yaxis=dict(showgrid=True, gridcolor=COLOR_GRID, gridwidth=1, griddash='dot',
                   zeroline=False, fixedrange=True),
        bargap=0.25,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(family="DM Sans, sans-serif", size=11)),
    )
    write_chart_html(fig_count, os.path.join(charts_dir, file_count), SOURCE_TEXT)
    print(f"   Saved → charts/{file_count}")

    # --- Percent version ---
    fig_pct = go.Figure()
    for status in STATUS_ORDER:
        col = f"pct_{value_col_prefix}_{status}"
        count_col = f"{value_col_prefix}_{status}"
        fig_pct.add_trace(go.Bar(
            x=cs_df['County'], y=cs_df[col], name=status,
            marker=dict(color=STATUS_COLORS[status], cornerradius=3, line=dict(width=0)),
            hovertemplate=(
                f"<b>%{{x}}</b><br>{status}: %{{y:.1f}}%<br>"
                f"(%{{customdata[0]:,.0f}})<extra></extra>"
            ),
            customdata=cs_df[[count_col]].values,
        ))

    fig_pct.update_layout(COMMON_LAYOUT)
    fig_pct.update_layout(
        barmode='stack',
        xaxis_title="", yaxis_title=y_label_pct,
        margin=dict(t=20, b=80, l=55, r=20),
        yaxis=dict(showgrid=True, gridcolor=COLOR_GRID, gridwidth=1, griddash='dot',
                   zeroline=False, range=[0, 105], fixedrange=True),
        bargap=0.25,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(family="DM Sans, sans-serif", size=11)),
    )
    write_chart_html(fig_pct, os.path.join(charts_dir, file_pct), SOURCE_TEXT)
    print(f"   Saved → charts/{file_pct}")

    # --- Dashboard wrapper ---
    dash_html = f"""<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>{_css_base()}</style>
<script>
function switchView() {{
    document.getElementById('chartFrame').src = "charts/" + document.getElementById('viewSelector').value;
}}
</script>
</head><body>
<div class="card">
    <div class="header">
        <h2>{dash_title}</h2>
        <div class="controls-row">
            <select id="viewSelector" onchange="switchView()">
                <option value="{file_count}">Count</option>
                <option value="{file_pct}">Percent (%)</option>
            </select>
        </div>
    </div>
    <iframe id="chartFrame" src="charts/{file_count}"></iframe>
</div></body></html>"""

    with open(os.path.join(OUTPUT_DIR, file_dash), "w", encoding="utf-8") as f:
        f.write(dash_html)
    print(f"   Saved → {file_dash}")


# =====================================================================
# 2.  BAR: Project Count by County, stacked by status
# =====================================================================
print("\n── Building project count bar charts")

build_stacked_bar(
    cs, "n", "Number of Projects", "% of Projects",
    "bar_project_count.html", "bar_project_count_pct.html",
    "bar_final_project_count.html",
    "Solar Projects by County & Status",
)


# =====================================================================
# 3.  BAR: Solar Capacity (kW DC) by County, stacked by status
# =====================================================================
print("\n── Building solar capacity bar charts")

build_stacked_bar(
    cs, "kw", "Total Nameplate kW DC", "% of kW DC",
    "bar_solar_capacity.html", "bar_solar_capacity_pct.html",
    "bar_final_solar_capacity.html",
    "Solar Capacity (kW DC) by County & Status",
)


# =====================================================================
# 4.  MAPS — Completed projects only
# =====================================================================
print("\n── Building maps: completed projects by county")

import geopandas as gpd
import plotly.express as px

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

    def build_map(cs_df, value_col, hover_label, hover_fmt, tick_fmt,
                  file_slug, dash_title):
        """Build desktop + mobile maps and dashboard wrapper."""

        map_data = cs_df.copy()
        map_data['estimate'] = map_data[value_col]
        map_data['moe'] = 0

        filtered = gdf_cty.merge(map_data, on="GEOID")
        if filtered.empty:
            print(f"   [WARN] No data for map — skipping {file_slug}")
            return

        reg_center = {
            "lat": filtered.geometry.centroid.y.mean(),
            "lon": filtered.geometry.centroid.x.mean(),
        }

        # Data-driven color range
        vmin = filtered['estimate'].min()
        vmax = filtered['estimate'].max()
        span = vmax - vmin if vmax > vmin else 1
        color_floor = max(0, vmin - span * 0.1)
        color_ceil = vmax + span * 0.1

        def save_map(gdf, zoom, center, filepath, label_col):
            fig_m = px.choropleth_mapbox(
                gdf,
                geojson=gdf.set_index("GEOID").geometry,
                locations="GEOID",
                color="estimate",
                hover_name=label_col,
                hover_data=["moe"],
                mapbox_style="carto-positron",
                opacity=0.85,
                zoom=zoom,
                center=center,
                color_continuous_scale=BRAND_COLOR_SCALE,
                range_color=[color_floor, color_ceil],
            )
            fig_m.update_traces(
                hovertemplate=(
                    "<b>%{hovertext}</b><br>"
                    f"{hover_label}: %{{z:{hover_fmt}}}"
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
                    tickformat=tick_fmt,
                    tickfont=dict(size=10, color=COLOR_MUTED),
                ),
            )
            write_chart_html(fig_m, filepath, SOURCE_TEXT + " (Completed Projects)")

        for mode in ('desktop', 'mobile'):
            path = os.path.join(maps_dir, f"map_county_{file_slug}_{mode}.html")
            save_map(filtered, get_zoom(filtered, mode), reg_center, path, "County")
            print(f"   Saved → maps/map_county_{file_slug}_{mode}.html")

        # Dashboard wrapper
        map_dash = f"""<!DOCTYPE html>
<html><head>
<title>{dash_title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>{_css_base()} iframe {{ height: 100%; }}
select {{ max-width: 160px; }}</style>
<script>
var currentDeviceMode = 'desktop';
function setDeviceMode(mode) {{
    currentDeviceMode = mode;
    document.getElementById('btn-desktop').classList.toggle('active', mode === 'desktop');
    document.getElementById('btn-mobile').classList.toggle('active', mode === 'mobile');
    document.getElementById('mainFrame').src = "maps/map_county_{file_slug}_" + currentDeviceMode + ".html";
}}
</script>
</head><body>
<div class="card">
    <div class="header">
        <h2>{dash_title}</h2>
        <div class="controls-row">
            <div class="toggle-container">
                <button id="btn-desktop" class="toggle-btn active" onclick="setDeviceMode('desktop')">Desktop</button>
                <button id="btn-mobile" class="toggle-btn" onclick="setDeviceMode('mobile')">Mobile</button>
            </div>
        </div>
    </div>
    <iframe id="mainFrame" src="maps/map_county_{file_slug}_desktop.html"></iframe>
</div></body></html>"""

        with open(os.path.join(OUTPUT_DIR, f"map_final_{file_slug}.html"), "w", encoding="utf-8") as f:
            f.write(map_dash)
        print(f"   Saved → map_final_{file_slug}.html")

    # --- Map 1: Completed project count ---
    build_map(
        cs, "n_Complete", "Completed Projects", ",.0f", ",",
        "completed_count", "Completed Solar Projects by County",
    )

    # --- Map 2: Completed solar capacity ---
    build_map(
        cs, "kw_Complete", "Completed kW DC", ",.0f", ",",
        "completed_capacity", "Completed Solar Capacity (kW DC) by County",
    )


# =====================================================================
# 5.  SUMMARY
# =====================================================================
print(f"""
{'='*60}
  DONE — All outputs in: {OUTPUT_DIR}
{'='*60}
  bar_final_project_count.html      Projects by status (count/%)
  bar_final_solar_capacity.html     kW DC by status (count/%)
  map_final_completed_count.html    Completed project count map
  map_final_completed_capacity.html Completed kW DC capacity map
{'='*60}
""")
