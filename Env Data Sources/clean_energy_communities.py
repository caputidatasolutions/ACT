"""
Clean Energy Communities — ACT Environmental Data Pipeline
============================================================
Reads NYSERDA Clean Energy Communities data and produces interactive
Plotly HTML dashboards matching the ACT pipeline visual style.

Charts produced:
  1. Bar: Count of communities by CEC Designation Status per county
     + toggle to show % of communities designated
  2. Bar: Stacked bar of Advanced (v3.0) Designation by county
     + toggle to show % breakdown
  3. Map: % of communities with "Designated CEC" status per county

Usage:
    python clean_energy_communities.py

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
import glob
_candidates = glob.glob(os.path.join(BASE_DIR, "Clean*Energy*Communit*.*"))
if _candidates:
    INPUT_FILE = _candidates[0]
else:
    INPUT_FILE = os.path.join(BASE_DIR, "Clean Energy Communities.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "Output_Clean_Energy_Communities")
ACT_BASE   = r"C:\Users\camer\Desktop\ACT"

# ── Import shared utils ─────────────────────────────────────────────
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

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

SOURCE_TEXT = "Source: NYSERDA, Clean Energy Communities Program"

# Colors for CEC Designation Status
COLOR_DESIGNATED    = "#16A34A"   # Green
COLOR_NOT_DESIGNATED = COLOR_GRID  # Light gray

# Colors for Advanced star levels
STAR_ORDER  = ["Not Designated", "1-Star", "2-Star", "3-Star", "4-Star", "5-Star"]
STAR_COLORS = {
    "Not Designated": "#D1D5DB",  # Gray
    "1-Star":  "#93C5FD",         # Light blue
    "2-Star":  "#3B8FCC",         # Medium blue
    "3-Star":  COLOR_PRIMARY,     # Primary blue
    "4-Star":  "#1A2744",         # Dark navy
    "5-Star":  COLOR_ACCENT,      # Gold/orange
}


# =====================================================================
# 1.  READ & CLEAN
# =====================================================================
print(f"\n── Reading {INPUT_FILE}")
if not os.path.exists(INPUT_FILE):
    sys.exit(f"[ERROR] File not found: {INPUT_FILE}")

raw = pd.read_csv(INPUT_FILE) if INPUT_FILE.endswith('.csv') else pd.read_excel(INPUT_FILE, engine="openpyxl")
df = raw[raw['County'].isin(ACT_COUNTIES)].copy()
print(f"   {len(df)} communities across {df['County'].nunique()} counties")

# Fill NaN in Advanced designation as "Not Designated"
df['Advanced (v3.0) Designation'] = df['Advanced (v3.0) Designation'].fillna("Not Designated")

# Build county-level summary
county_summary = []
for county in sorted(df['County'].unique()):
    sub = df[df['County'] == county]
    total = len(sub)
    designated = (sub['CEC Designation Status'] == 'Designated CEC').sum()
    not_desig = total - designated
    pct_designated = round(designated / total * 100, 1) if total > 0 else 0

    # Advanced breakdown
    adv_counts = sub['Advanced (v3.0) Designation'].value_counts().to_dict()

    county_summary.append({
        'County': county,
        'total': total,
        'designated': designated,
        'not_designated': not_desig,
        'pct_designated': pct_designated,
        **{f"adv_{s}": adv_counts.get(s, 0) for s in STAR_ORDER},
    })

cs = pd.DataFrame(county_summary).sort_values('designated', ascending=False).reset_index(drop=True)
cs['County_upper'] = cs['County'].str.upper()
cs['GEOID'] = cs['County_upper'].map(COUNTY_GEOID)

print(cs[['County', 'total', 'designated', 'pct_designated']].to_string(index=False))

# Create output directories
charts_dir = os.path.join(OUTPUT_DIR, "charts")
maps_dir   = os.path.join(OUTPUT_DIR, "maps")
os.makedirs(charts_dir, exist_ok=True)
os.makedirs(maps_dir, exist_ok=True)


# =====================================================================
# 2.  BAR CHART — CEC Designation Status (count + % toggle)
# =====================================================================
print("\n── Building CEC Designation bar charts")

# --- Count version ---
fig_count = go.Figure()
fig_count.add_trace(go.Bar(
    x=cs['County'], y=cs['designated'], name='Designated CEC',
    marker=dict(color=COLOR_DESIGNATED, cornerradius=3, line=dict(width=0)),
    hovertemplate="<b>%{x}</b><br>Designated: %{y}<br>Total: %{customdata[0]}<extra></extra>",
    customdata=cs[['total']].values,
))
fig_count.add_trace(go.Bar(
    x=cs['County'], y=cs['not_designated'], name='Not Designated',
    marker=dict(color=COLOR_NOT_DESIGNATED, cornerradius=3, line=dict(width=0)),
    hovertemplate="<b>%{x}</b><br>Not Designated: %{y}<br>Total: %{customdata[0]}<extra></extra>",
    customdata=cs[['total']].values,
))

fig_count.update_layout(COMMON_LAYOUT)
fig_count.update_layout(
    barmode='stack',
    xaxis_title="", yaxis_title="Number of Communities",
    margin=dict(t=20, b=80, l=55, r=20),
    yaxis=dict(showgrid=True, gridcolor=COLOR_GRID, gridwidth=1, griddash='dot',
               zeroline=False, fixedrange=True),
    bargap=0.25,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                font=dict(family="DM Sans, sans-serif", size=11)),
)

write_chart_html(fig_count, os.path.join(charts_dir, "bar_cec_status_count.html"), SOURCE_TEXT)
print(f"   Saved → charts/bar_cec_status_count.html")

# --- Percent version ---
fig_pct = go.Figure()
fig_pct.add_trace(go.Bar(
    x=cs['County'], y=cs['pct_designated'], name='Designated CEC',
    marker=dict(color=COLOR_DESIGNATED, cornerradius=3, line=dict(width=0)),
    hovertemplate="<b>%{x}</b><br>Designated: %{y:.1f}%<br>(%{customdata[0]} of %{customdata[1]})<extra></extra>",
    customdata=cs[['designated', 'total']].values,
))
fig_pct.add_trace(go.Bar(
    x=cs['County'], y=100 - cs['pct_designated'], name='Not Designated',
    marker=dict(color=COLOR_NOT_DESIGNATED, cornerradius=3, line=dict(width=0)),
    hovertemplate="<b>%{x}</b><br>Not Designated: %{customdata[0]:.1f}%<extra></extra>",
    customdata=(100 - cs['pct_designated']).values.reshape(-1, 1),
))

fig_pct.update_layout(COMMON_LAYOUT)
fig_pct.update_layout(
    barmode='stack',
    xaxis_title="", yaxis_title="% of Communities",
    margin=dict(t=20, b=80, l=55, r=20),
    yaxis=dict(showgrid=True, gridcolor=COLOR_GRID, gridwidth=1, griddash='dot',
               zeroline=False, range=[0, 105], fixedrange=True),
    bargap=0.25,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                font=dict(family="DM Sans, sans-serif", size=11)),
)

write_chart_html(fig_pct, os.path.join(charts_dir, "bar_cec_status_pct.html"), SOURCE_TEXT)
print(f"   Saved → charts/bar_cec_status_pct.html")

# --- Dashboard wrapper with count/% toggle ---
bar_cec_dash = f"""<!DOCTYPE html>
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
        <h2>CEC Designation Status by County</h2>
        <div class="controls-row">
            <select id="viewSelector" onchange="switchView()">
                <option value="bar_cec_status_count.html">Count</option>
                <option value="bar_cec_status_pct.html">Percent (%)</option>
            </select>
        </div>
    </div>
    <iframe id="chartFrame" src="charts/bar_cec_status_count.html"></iframe>
</div></body></html>"""

with open(os.path.join(OUTPUT_DIR, "bar_final_cec_status.html"), "w", encoding="utf-8") as f:
    f.write(bar_cec_dash)
print(f"   Saved → bar_final_cec_status.html")


# =====================================================================
# 3.  BAR CHART — Advanced (v3.0) Designation (stacked + % toggle)
# =====================================================================
print("\n── Building Advanced Designation stacked bar charts")

# Sort counties by total designated for this chart
cs_adv = cs.sort_values('designated', ascending=False).reset_index(drop=True)

# Compute percentages for each star level
for s in STAR_ORDER:
    cs_adv[f"adv_pct_{s}"] = (cs_adv[f"adv_{s}"] / cs_adv['total'] * 100).round(1)

# --- Count version (stacked) ---
fig_adv_count = go.Figure()
for star in STAR_ORDER:
    col = f"adv_{star}"
    fig_adv_count.add_trace(go.Bar(
        x=cs_adv['County'], y=cs_adv[col], name=star,
        marker=dict(color=STAR_COLORS[star], cornerradius=3, line=dict(width=0)),
        hovertemplate=f"<b>%{{x}}</b><br>{star}: %{{y}}<br>Total: %{{customdata[0]}}<extra></extra>",
        customdata=cs_adv[['total']].values,
    ))

fig_adv_count.update_layout(COMMON_LAYOUT)
fig_adv_count.update_layout(
    barmode='stack',
    xaxis_title="", yaxis_title="Number of Communities",
    margin=dict(t=20, b=80, l=55, r=20),
    yaxis=dict(showgrid=True, gridcolor=COLOR_GRID, gridwidth=1, griddash='dot',
               zeroline=False, fixedrange=True),
    bargap=0.25,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                font=dict(family="DM Sans, sans-serif", size=11),
                traceorder="normal"),
)

write_chart_html(fig_adv_count, os.path.join(charts_dir, "bar_advanced_count.html"), SOURCE_TEXT)
print(f"   Saved → charts/bar_advanced_count.html")

# --- Percent version (stacked to 100%) ---
fig_adv_pct = go.Figure()
for star in STAR_ORDER:
    col = f"adv_pct_{star}"
    count_col = f"adv_{star}"
    fig_adv_pct.add_trace(go.Bar(
        x=cs_adv['County'], y=cs_adv[col], name=star,
        marker=dict(color=STAR_COLORS[star], cornerradius=3, line=dict(width=0)),
        hovertemplate=f"<b>%{{x}}</b><br>{star}: %{{y:.1f}}%<br>(%{{customdata[0]}} communities)<extra></extra>",
        customdata=cs_adv[[count_col]].values,
    ))

fig_adv_pct.update_layout(COMMON_LAYOUT)
fig_adv_pct.update_layout(
    barmode='stack',
    xaxis_title="", yaxis_title="% of Communities",
    margin=dict(t=20, b=80, l=55, r=20),
    yaxis=dict(showgrid=True, gridcolor=COLOR_GRID, gridwidth=1, griddash='dot',
               zeroline=False, range=[0, 105], fixedrange=True),
    bargap=0.25,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                font=dict(family="DM Sans, sans-serif", size=11),
                traceorder="normal"),
)

write_chart_html(fig_adv_pct, os.path.join(charts_dir, "bar_advanced_pct.html"), SOURCE_TEXT)
print(f"   Saved → charts/bar_advanced_pct.html")

# --- Dashboard wrapper ---
bar_adv_dash = f"""<!DOCTYPE html>
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
        <h2>Advanced (v3.0) Designation by County</h2>
        <div class="controls-row">
            <select id="viewSelector" onchange="switchView()">
                <option value="bar_advanced_count.html">Count</option>
                <option value="bar_advanced_pct.html">Percent (%)</option>
            </select>
        </div>
    </div>
    <iframe id="chartFrame" src="charts/bar_advanced_count.html"></iframe>
</div></body></html>"""

with open(os.path.join(OUTPUT_DIR, "bar_final_advanced_designation.html"), "w", encoding="utf-8") as f:
    f.write(bar_adv_dash)
print(f"   Saved → bar_final_advanced_designation.html")


# =====================================================================
# 4.  MAP — % Designated CEC by county
# =====================================================================
print("\n── Building map: % Designated CEC by county")

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
        print(f"   [WARN] Shapes not found — skipping map")
except Exception as e:
    print(f"   [WARN] Could not load shapes: {e}")

if gdf_cty is not None:
    gdf_cty['GEOID'] = gdf_cty['GEOID'].astype(str)

    map_data = cs.copy()
    map_data['estimate'] = map_data['pct_designated']
    map_data['moe'] = 0

    filtered_cty = gdf_cty.merge(map_data, on="GEOID")

    if not filtered_cty.empty:
        reg_center = {
            "lat": filtered_cty.geometry.centroid.y.mean(),
            "lon": filtered_cty.geometry.centroid.x.mean(),
        }

        def get_zoom(gdf, mode='desktop'):
            bounds = gdf.total_bounds
            max_span = max(bounds[2] - bounds[0], bounds[3] - bounds[1])
            if max_span == 0:
                return 10
            if mode == 'mobile':
                return max(4.5, min(12.0, 7.1 - np.log2(max_span)))
            return max(5.5, min(13.0, 8.1 - np.log2(max_span)))

        # Compute color range from actual data — start at lowest value
        pct_min = filtered_cty['estimate'].min()
        pct_max = filtered_cty['estimate'].max()
        # Add small padding so extremes aren't washed out
        color_floor = max(0, pct_min - (pct_max - pct_min) * 0.1)
        color_ceil  = min(100, pct_max + (pct_max - pct_min) * 0.1)

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
                    "Designated CEC: %{z:.1f}%<br>"
                    "(%{customdata[0]} of %{customdata[1]} communities)"
                    "<extra></extra>"
                ),
                customdata=gdf[['designated', 'total']].values,
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
                    ticksuffix="%",
                    tickfont=dict(size=10, color=COLOR_MUTED),
                ),
            )
            write_chart_html(fig_m, filepath, SOURCE_TEXT)

        for mode in ('desktop', 'mobile'):
            map_path = os.path.join(maps_dir, f"map_county_cec_pct_{mode}.html")
            save_map(filtered_cty, get_zoom(filtered_cty, mode),
                     reg_center, map_path, "County")
            print(f"   Saved → maps/map_county_cec_pct_{mode}.html")

        # --- Map dashboard wrapper ---
        map_dash = f"""<!DOCTYPE html>
<html><head>
<title>CEC Designation Map</title>
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
    document.getElementById('mainFrame').src = "maps/map_county_cec_pct_" + currentDeviceMode + ".html";
}}
</script>
</head><body>
<div class="card">
    <div class="header">
        <h2>% Communities with CEC Designation</h2>
        <div class="controls-row">
            <div class="toggle-container">
                <button id="btn-desktop" class="toggle-btn active" onclick="setDeviceMode('desktop')">Desktop</button>
                <button id="btn-mobile" class="toggle-btn" onclick="setDeviceMode('mobile')">Mobile</button>
            </div>
        </div>
    </div>
    <iframe id="mainFrame" src="maps/map_county_cec_pct_desktop.html"></iframe>
</div></body></html>"""

        with open(os.path.join(OUTPUT_DIR, "map_final_cec_designation.html"), "w", encoding="utf-8") as f:
            f.write(map_dash)
        print(f"   Saved → map_final_cec_designation.html")


# =====================================================================
# 5.  SUMMARY
# =====================================================================
print(f"""
{'='*60}
  DONE — All outputs in: {OUTPUT_DIR}
{'='*60}
  bar_final_cec_status.html             CEC status (count/%)
  bar_final_advanced_designation.html    Advanced star level (count/%)
  map_final_cec_designation.html         % Designated CEC map
{'='*60}
""")