"""
Energy Burden & Cost — ACT Environmental Data Pipeline
=======================================================
Reads LEAD Tool 2022 data and produces bar charts + maps
for Energy Burden and Energy Cost by county.

Usage:
    python energy_burden.py

Requires: pandas, plotly, geopandas, numpy
"""

import os, sys, glob, warnings
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ── Paths ────────────────────────────────────────────────────────────
BASE_DIR   = r"C:\Users\camer\Desktop\ACT\Env Data Sources"
ACT_BASE   = r"C:\Users\camer\Desktop\ACT"
OUTPUT_DIR = os.path.join(BASE_DIR, "Output_Energy_Burden")

_candidates = glob.glob(os.path.join(BASE_DIR, "lead*tool*.*"))
INPUT_FILE = _candidates[0] if _candidates else os.path.join(BASE_DIR, "lead_tool_2022.xlsx")

# ── Import utils ─────────────────────────────────────────────────────
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from utils import (
        COLOR_PRIMARY, COLOR_PRIMARY_LT, COLOR_DARK, COLOR_ACCENT,
        COLOR_ERROR_BAR, COLOR_MUTED, COLOR_CHART_BG, COLOR_GRID,
        COLOR_PAGE_BG, COLOR_TEXT_MAIN, FONT_BODY, FONT_HEADINGS,
        COMMON_LAYOUT, MOBILE_CONFIG, write_chart_html,
    )
    print("[OK] Imported branding from utils.py")
    try:
        from utils import BRAND_COLOR_SCALE
    except ImportError:
        BRAND_COLOR_SCALE = [[0.0,'#B3D4E8'],[0.35,'#3B8FCC'],[0.65,'#0062A3'],[1.0,'#1A2744']]
    try:
        from utils import _css_base
    except ImportError:
        pass
except Exception as e:
    print(f"[WARN] utils.py import failed: {e}\n       Using inline fallbacks.")
    COLOR_PRIMARY='#0062A3'; COLOR_PRIMARY_LT='#3B8FCC'; COLOR_DARK='#1A2744'
    COLOR_ACCENT='#E8913A'; COLOR_ERROR_BAR='#B0BEC5'; COLOR_MUTED='#94A3B8'
    COLOR_CHART_BG='#FFFFFF'; COLOR_GRID='#E8ECF0'; COLOR_PAGE_BG='#F0F2F5'
    COLOR_TEXT_MAIN='#1A2744'; FONT_BODY="Proxima Nova, sans-serif"
    FONT_HEADINGS="Freight Macro Pro, serif"
    BRAND_COLOR_SCALE=[[0.0,'#B3D4E8'],[0.35,'#3B8FCC'],[0.65,'#0062A3'],[1.0,'#1A2744']]
    COMMON_LAYOUT = dict(
        font_family=FONT_BODY, font_color=COLOR_TEXT_MAIN,
        paper_bgcolor=COLOR_CHART_BG, plot_bgcolor=COLOR_CHART_BG,
        margin=dict(t=30,b=100,l=50,r=30),
        xaxis=dict(showgrid=False,zeroline=False,showline=False,
                   tickfont=dict(family=FONT_BODY,size=11,color=COLOR_MUTED),
                   title_font=dict(family=FONT_BODY,size=12,color=COLOR_MUTED)),
        yaxis=dict(showgrid=True,gridcolor=COLOR_GRID,gridwidth=1,griddash='dot',
                   zeroline=False,showline=False,
                   tickfont=dict(family=FONT_BODY,size=11,color=COLOR_MUTED),
                   title_font=dict(family=FONT_BODY,size=12,color=COLOR_MUTED)),
        hoverlabel=dict(bgcolor="white",bordercolor=COLOR_PRIMARY,
                        font_size=13,font_family=FONT_BODY,font_color=COLOR_DARK),
    )
    MOBILE_CONFIG = {'displayModeBar':False,'responsive':True,'scrollZoom':False}
    def write_chart_html(fig, filepath, source_text, config=None):
        if config is None: config = MOBILE_CONFIG
        html = fig.to_html(include_plotlyjs='cdn', config=config, full_html=True)
        footer = f"""
<style>
  html,body{{margin:0;padding:0;width:100%;height:100%;overflow:hidden;display:flex;flex-direction:column}}
  .plotly-graph-div{{width:100%!important;flex:1 1 auto!important}}
  .source-footer{{flex:0 0 auto;padding:4px 12px 6px;font-family:'DM Sans','{FONT_BODY}',sans-serif;
    font-size:9px;color:{COLOR_MUTED};background:#fff;border-top:1px solid {COLOR_GRID};
    white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
</style>
<script>
  window.addEventListener('load',function(){{window.dispatchEvent(new Event('resize'))}});
  window.addEventListener('resize',function(){{
    var g=document.querySelector('.plotly-graph-div');
    if(g){{var f=document.querySelector('.source-footer');
      Plotly.relayout(g,{{height:window.innerHeight-(f?f.offsetHeight:0)}})}}
  }});
</script>
<div class="source-footer">{source_text}</div>"""
        html = html.replace('</body>', footer + '</body>')
        with open(filepath, 'w', encoding='utf-8') as f: f.write(html)

if '_css_base' not in dir():
    def _css_base():
        return f"""
            @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap');
            *,*::before,*::after{{box-sizing:border-box}}
            html,body{{margin:0;padding:0;height:100%;width:100%;
              font-family:'DM Sans','{FONT_BODY}',system-ui,sans-serif;
              background-color:{COLOR_PAGE_BG};overflow:hidden;color:{COLOR_DARK}}}
            .card{{display:flex;flex-direction:column;height:100dvh;width:100%;background:{COLOR_CHART_BG}}}
            .header{{flex:0 0 auto;padding:12px 20px;border-bottom:2px solid {COLOR_GRID};
              display:flex;flex-wrap:wrap;gap:12px;justify-content:space-between;align-items:center;
              background:#fff;z-index:10}}
            .controls-row{{display:flex;gap:8px;align-items:center;flex-wrap:wrap}}
            iframe{{flex:1 1 auto;width:100%;border:none;display:block}}
            h2{{margin:0;color:{COLOR_DARK};font-family:'DM Sans','{FONT_HEADINGS}',serif;
              font-size:1.05rem;font-weight:600;letter-spacing:-0.01em}}
            select{{padding:7px 12px;font-size:13px;font-family:'DM Sans',sans-serif;font-weight:500;
              border-radius:6px;border:1.5px solid {COLOR_GRID};color:{COLOR_DARK};
              background-color:#FAFBFC;cursor:pointer;transition:border-color .15s,box-shadow .15s;outline:none}}
            select:hover{{border-color:{COLOR_PRIMARY_LT}}}
            select:focus{{border-color:{COLOR_PRIMARY};box-shadow:0 0 0 3px rgba(0,98,163,.10)}}
            .toggle-container{{display:flex;align-items:center;font-size:12px;
              border:1.5px solid {COLOR_GRID};border-radius:6px;overflow:hidden}}
            .toggle-btn{{padding:7px 14px;cursor:pointer;background:#FAFBFC;border:none;outline:none;
              font-family:'DM Sans',sans-serif;font-weight:500;font-size:12px;color:{COLOR_MUTED};
              transition:all .15s}}
            .toggle-btn:hover{{background:#F0F2F5}}
            .toggle-btn.active{{background:{COLOR_PRIMARY};color:white}}
        """

# =====================================================================
COUNTY_GEOID = {
    "GENESEE":"36037","LIVINGSTON":"36051","MONROE":"36055","ONTARIO":"36069",
    "ORLEANS":"36073","SENECA":"36099","WAYNE":"36117","YATES":"36123",
}
SOURCE_TEXT = "Source: DOE LEAD Tool, 2022"

# =====================================================================
# 1. READ
# =====================================================================
print(f"\n── Reading {INPUT_FILE}")
if not os.path.exists(INPUT_FILE):
    sys.exit(f"[ERROR] File not found: {INPUT_FILE}")

df = pd.read_excel(INPUT_FILE, engine="openpyxl")
df['County'] = df['County'].astype(str).str.strip()
df['County_upper'] = df['County'].str.upper()
df['GEOID'] = df['County_upper'].map(COUNTY_GEOID)
# Energy Burden is a decimal (0.02 = 2%) — convert to percentage
df['burden_pct'] = (df['Energy Burden'] * 100).round(1)
print(df[['County', 'burden_pct', 'Energy Cost']].to_string(index=False))

charts_dir = os.path.join(OUTPUT_DIR, "charts")
maps_dir   = os.path.join(OUTPUT_DIR, "maps")
os.makedirs(charts_dir, exist_ok=True)
os.makedirs(maps_dir, exist_ok=True)

# =====================================================================
# 2. VARIABLES — each gets a bar chart + map
# =====================================================================
VARIABLES = [
    {
        "col": "burden_pct",
        "title": "Energy Burden",
        "y_label": "Energy Burden (%)",
        "hover_fmt": ":,.1f",
        "hover_suffix": "%",
        "tick_suffix": "%",
        "tick_fmt": "",
        "slug": "energy_burden",
    },
    {
        "col": "Energy Cost",
        "title": "Average Annual Energy Cost",
        "y_label": "Energy Cost ($)",
        "hover_fmt": ":,.0f",
        "hover_suffix": "",
        "hover_prefix": "$",
        "tick_suffix": "",
        "tick_fmt": "$,",
        "slug": "energy_cost",
    },
]

import geopandas as gpd
import plotly.express as px

# Load shapes once
shp_cty = os.path.join(ACT_BASE, "shapes", "most_recent_county_shapes.geojson")
cache_cty = shp_cty.replace(".geojson", "_simplified.geojson")
gdf_cty = None
try:
    if os.path.exists(cache_cty):
        gdf_cty = gpd.read_file(cache_cty)
        print("[OK] Loaded cached county shapes")
    elif os.path.exists(shp_cty):
        gdf_cty = gpd.read_file(shp_cty)
        gdf_cty['geometry'] = gdf_cty['geometry'].simplify(tolerance=0.001, preserve_topology=True)
        print("[OK] Loaded & simplified county shapes")
except Exception as e:
    print(f"[WARN] Shapes: {e}")

if gdf_cty is not None:
    gdf_cty['GEOID'] = gdf_cty['GEOID'].astype(str)

def get_zoom(gdf, mode='desktop'):
    bounds = gdf.total_bounds
    s = max(bounds[2]-bounds[0], bounds[3]-bounds[1])
    if s == 0: return 10
    if mode == 'mobile': return max(4.5, min(12.0, 7.1-np.log2(s)))
    return max(5.5, min(13.0, 8.1-np.log2(s)))

for var in VARIABLES:
    col   = var["col"]
    title = var["title"]
    slug  = var["slug"]
    print(f"\n── [{slug}] {title}")

    sorted_df = df.sort_values('County').reset_index(drop=True)

    # --- BAR CHART ---
    dollar = var.get("hover_prefix", "")
    suffix = var["hover_suffix"]
    max_val = sorted_df[col].max() * 1.15

    fig = go.Figure(go.Bar(
        x=sorted_df['County'], y=sorted_df[col],
        marker=dict(color=COLOR_PRIMARY, cornerradius=3, line=dict(width=0)),
        hovertemplate=(
            f"<b>%{{x}}</b><br>"
            f"{title}: {dollar}%{{y{var['hover_fmt']}}}{suffix}"
            f"<extra></extra>"
        ),
    ))
    fig.update_layout(COMMON_LAYOUT)
    fig.update_layout(
        xaxis_title="", yaxis_title=var["y_label"],
        margin=dict(t=20, b=80, l=55, r=20),
        yaxis=dict(showgrid=True, gridcolor=COLOR_GRID, gridwidth=1, griddash='dot',
                   zeroline=False, range=[0, max_val], fixedrange=True),
        bargap=0.25,
    )
    write_chart_html(fig, os.path.join(charts_dir, f"bar_county_{slug}.html"), SOURCE_TEXT)
    print(f"   bar  → charts/bar_county_{slug}.html")

    # Bar wrapper
    bar_dash = f"""<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>{_css_base()}</style>
</head><body>
<div class="card">
    <div class="header"><h2>{title}</h2></div>
    <iframe id="chartFrame" src="charts/bar_county_{slug}.html"></iframe>
</div></body></html>"""
    with open(os.path.join(OUTPUT_DIR, f"bar_final_{slug}.html"), "w", encoding="utf-8") as f:
        f.write(bar_dash)

    # --- MAP ---
    if gdf_cty is not None:
        map_data = sorted_df.copy()
        map_data['estimate'] = map_data[col]
        map_data['moe'] = 0
        filtered = gdf_cty.merge(map_data, on="GEOID")

        if not filtered.empty:
            center = {
                "lat": filtered.geometry.centroid.y.mean(),
                "lon": filtered.geometry.centroid.x.mean(),
            }
            vmin, vmax = filtered['estimate'].min(), filtered['estimate'].max()
            span = vmax - vmin if vmax > vmin else 1
            cfloor = max(0, vmin - span * 0.1)
            cceil = vmax + span * 0.1

            for mode in ('desktop', 'mobile'):
                fig_m = px.choropleth_mapbox(
                    filtered, geojson=filtered.set_index("GEOID").geometry,
                    locations="GEOID", color="estimate", hover_name="County",
                    hover_data=["moe"], mapbox_style="carto-positron", opacity=0.85,
                    zoom=get_zoom(filtered, mode), center=center,
                    color_continuous_scale=BRAND_COLOR_SCALE,
                    range_color=[cfloor, cceil],
                )
                fig_m.update_traces(hovertemplate=(
                    f"<b>%{{hovertext}}</b><br>"
                    f"{title}: {dollar}%{{z{var['hover_fmt']}}}{suffix}"
                    f"<extra></extra>"
                ))
                fig_m.update_layout(COMMON_LAYOUT)
                fig_m.update_layout(
                    margin={"r":0,"t":0,"l":0,"b":0},
                    coloraxis_colorbar=dict(
                        title="", len=0.45, thickness=14,
                        yanchor="bottom", y=0.06, xanchor="right", x=0.96,
                        bgcolor="rgba(255,255,255,0.85)", outlinewidth=0,
                        tickformat=var["tick_fmt"],
                        ticksuffix=var["tick_suffix"],
                        tickfont=dict(size=10, color=COLOR_MUTED)),
                )
                path = os.path.join(maps_dir, f"map_county_{slug}_{mode}.html")
                write_chart_html(fig_m, path, SOURCE_TEXT)
                print(f"   map  → maps/map_county_{slug}_{mode}.html")

            map_dash = f"""<!DOCTYPE html>
<html><head>
<title>{title} Map</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>{_css_base()} iframe{{height:100%}} select{{max-width:160px}}</style>
<script>
var currentDeviceMode='desktop';
function setDeviceMode(mode){{
    currentDeviceMode=mode;
    document.getElementById('btn-desktop').classList.toggle('active',mode==='desktop');
    document.getElementById('btn-mobile').classList.toggle('active',mode==='mobile');
    document.getElementById('mainFrame').src="maps/map_county_{slug}_"+currentDeviceMode+".html";
}}
</script>
</head><body>
<div class="card">
    <div class="header">
        <h2>{title}</h2>
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

    print(f"   [{slug}] Done")

print(f"""
{'='*60}
  DONE — All outputs in: {OUTPUT_DIR}
{'='*60}
  bar_final_energy_burden.html   Energy Burden bar
  bar_final_energy_cost.html     Energy Cost bar
  map_final_energy_burden.html   Energy Burden map
  map_final_energy_cost.html     Energy Cost map
{'='*60}
""")