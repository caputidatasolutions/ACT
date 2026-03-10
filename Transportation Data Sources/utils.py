"""
ACT Dashboard Pipeline v2 — Shared Utilities
==============================================
Branding, layout, axis calculators, source annotations,
hover templates, and polished HTML dashboard wrappers.

v2 improvements:
  - Refined chart styling (rounded bars, gradient fills, cleaner grids)
  - Source + year annotations on every chart
  - Polished dashboard wrappers with modern header design
  - All output folders use _v2 suffix
"""

import numpy as np
import pandas as pd

# =====================================================================
# BRANDING v2  (refreshed palette — same brand DNA, more polish)
# =====================================================================
COLOR_PRIMARY    = '#0062A3'   # Deeper, richer blue
COLOR_PRIMARY_LT = '#3B8FCC'   # Lighter accent
COLOR_DARK       = '#1A2744'   # Near-black navy for text
COLOR_ACCENT     = '#E8913A'   # Warm accent for highlights
COLOR_ERROR_BAR  = '#B0BEC5'   # Softer gray for MOE whiskers
COLOR_MUTED      = '#94A3B8'   # Muted label text

COLOR_PAGE_BG    = '#F0F2F5'
COLOR_CHART_BG   = '#FFFFFF'
COLOR_GRID       = '#E8ECF0'
COLOR_TEXT_MAIN  = '#1A2744'

BRAND_COLOR_SCALE = [
    [0.0, '#B3D4E8'],
    [0.35, '#3B8FCC'],
    [0.65, '#0062A3'],
    [1.0, '#1A2744'],
]

FONT_HEADINGS = "Freight Macro Pro, serif"
FONT_BODY     = "Proxima Nova, sans-serif"

# =====================================================================
# PLOTLY LAYOUT  (v2 — cleaner, more refined)
# =====================================================================
COMMON_LAYOUT = dict(
    font_family=FONT_BODY,
    font_color=COLOR_TEXT_MAIN,
    paper_bgcolor=COLOR_CHART_BG,
    plot_bgcolor=COLOR_CHART_BG,
    margin=dict(t=30, b=100, l=50, r=30),
    xaxis=dict(
        showgrid=False, zeroline=False, showline=False,
        tickfont=dict(family=FONT_BODY, size=11, color=COLOR_MUTED),
        title_font=dict(family=FONT_BODY, size=12, color=COLOR_MUTED),
    ),
    yaxis=dict(
        showgrid=True, gridcolor=COLOR_GRID, gridwidth=1, griddash='dot',
        zeroline=False, showline=False,
        tickfont=dict(family=FONT_BODY, size=11, color=COLOR_MUTED),
        title_font=dict(family=FONT_BODY, size=12, color=COLOR_MUTED),
    ),
    hoverlabel=dict(
        bgcolor="white", bordercolor=COLOR_PRIMARY,
        font_size=13, font_family=FONT_BODY, font_color=COLOR_DARK,
    ),
)

MOBILE_CONFIG = {'displayModeBar': False, 'responsive': True, 'scrollZoom': False}


# =====================================================================
# SOURCE ANNOTATION BUILDER
# =====================================================================
def build_source_annotation(acs_table, years, single_year=None):
    """
    Build source citation text.
      years      — list of all years in the data (for line charts)
      single_year — if set, used for snapshot bar charts/maps
    """
    if single_year:
        year_str = str(single_year)
    elif years is not None and len(years) > 0:
        yr_sorted = sorted(years)
        year_str = f"{yr_sorted[0]}\u2013{yr_sorted[-1]}"
    else:
        year_str = ""

    table_part = f", Table {acs_table}" if acs_table else ""
    return f"Source: U.S. Census Bureau, American Community Survey 5-Year Estimates{table_part} ({year_str})"


def add_source_annotation(fig, source_text):
    """No-op: source is now rendered in the HTML wrapper, not inside the Plotly chart.
    Kept for backward compatibility so pipeline calls don't break."""
    pass


def write_chart_html(fig, filepath, source_text, config=None):
    """Write a Plotly figure to HTML with a source citation rendered as a fixed
    footer div OUTSIDE the chart — guaranteed no overlap with axes."""
    if config is None:
        config = MOBILE_CONFIG

    # Get the raw Plotly HTML
    chart_html = fig.to_html(
        include_plotlyjs='cdn',
        config=config,
        full_html=True,
    )

    # Inject CSS + source footer that makes the chart fill all available space
    source_footer = f"""
<style>
  html, body {{
    margin: 0; padding: 0; width: 100%; height: 100%;
    overflow: hidden; display: flex; flex-direction: column;
  }}
  /* The Plotly chart wrapper — fill all remaining space */
  .plotly-graph-div {{
    width: 100% !important;
    flex: 1 1 auto !important;
  }}
  /* Source footer — fixed strip at bottom */
  .source-footer {{
    flex: 0 0 auto;
    padding: 4px 12px 6px 12px;
    font-family: 'DM Sans', '{FONT_BODY}', sans-serif;
    font-size: 9px;
    color: {COLOR_MUTED};
    background: #fff;
    border-top: 1px solid {COLOR_GRID};
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
</style>
<script>
  // After Plotly renders, force the chart to fill available height
  window.addEventListener('load', function() {{
    window.dispatchEvent(new Event('resize'));
  }});
  window.addEventListener('resize', function() {{
    var gd = document.querySelector('.plotly-graph-div');
    if (gd) {{
      var footer = document.querySelector('.source-footer');
      var footerH = footer ? footer.offsetHeight : 0;
      var newH = window.innerHeight - footerH;
      Plotly.relayout(gd, {{ height: newH }});
    }}
  }});
</script>
<div class="source-footer">{source_text}</div>
"""
    chart_html = chart_html.replace('</body>', source_footer + '</body>')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(chart_html)


# =====================================================================
# ZOOM CALCULATOR
# =====================================================================
def get_zoom(gdf, mode='desktop'):
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


# =====================================================================
# AXIS RANGE CALCULATORS
# =====================================================================
def get_bar_range(df, data_type):
    if df.empty:
        return _default_range(data_type)
    max_val = (df['estimate'].fillna(0) + df['moe'].fillna(0)).max()
    target_top = max_val * 1.15  # 15% headroom so bars aren't jammed to the top
    if data_type == 'percent':
        return [0, min(100, max(5, target_top))]
    elif data_type in ('currency', 'count'):
        # No hardcoded minimum — let the data drive the axis
        if target_top <= 0:
            target_top = 100
        return [0, target_top]
    return [0, max(5, target_top)]


def get_line_range(df, data_type):
    if df.empty:
        return _default_range(data_type)
    vals = df['estimate'].fillna(0)
    moes = df['moe'].fillna(0)
    raw_min = (vals - moes).min()
    raw_max = (vals + moes).max()
    span = raw_max - raw_min
    if span == 0:
        span = _default_span(data_type)
    padding = span * 0.12
    target_min = raw_min - padding
    target_max = raw_max + padding
    if data_type == 'percent':
        final_min = max(0, target_min)
        final_max = min(100, target_max)
        if final_max <= final_min:
            final_max = min(100, final_min + 10)
        return [final_min, final_max]
    return [max(0, target_min), target_max]


def _default_range(dt):
    return {'percent': [0, 100], 'currency': [0, 100000], 'count': [0, 10000]}.get(dt, [0, 100])


def _default_span(dt):
    return {'currency': 5000, 'count': 1000}.get(dt, 10)


# =====================================================================
# ERROR BAR CLAMPING
# =====================================================================
def calculate_clamped_errors(y_values, moe_values, data_type='percent'):
    cap = 100 if data_type == 'percent' else float('inf')
    minus, plus = [], []
    for y, m in zip(y_values, moe_values):
        if pd.notnull(y) and pd.notnull(m):
            minus.append(min(m, y))
            plus.append(min(m, cap - y))
        else:
            minus.append(0)
            plus.append(0)
    return minus, plus


# =====================================================================
# HOVER TEMPLATES
# =====================================================================
def bar_hover(var_cfg):
    d = "$" if var_cfg.get("hover_dollar") else ""
    s = var_cfg.get("hover_suffix", "")
    f = var_cfg["hover_format"]
    mf = var_cfg["hover_moe_fmt"]
    # Uses customdata[0] = real MOE, not clamped error_y.array
    return (f"<b>%{{x}}</b><br>{var_cfg['hover_prefix']}: {d}%{{y:{f}}}{s}<br>"
            f"MOE: \u00b1{d}%{{customdata[0]:{mf}}}{s}<extra></extra>")


def line_hover(var_cfg):
    d = "$" if var_cfg.get("hover_dollar") else ""
    s = var_cfg.get("hover_suffix", "")
    f = var_cfg["hover_format"]
    mf = var_cfg["hover_moe_fmt"]
    # Uses customdata[0] = real MOE, not clamped error_y.array
    return (f"<b>{var_cfg['hover_prefix']}: {d}%{{y:{f}}}{s}</b><br>"
            f"MOE: \u00b1{d}%{{customdata[0]:{mf}}}{s}<extra></extra>")


def map_hover(var_cfg):
    d = "$" if var_cfg.get("hover_dollar") else ""
    s = var_cfg.get("hover_suffix", "")
    f = var_cfg["hover_format"]
    mf = var_cfg["hover_moe_fmt"]
    return (f"<b>%{{hovertext}}</b><br>{var_cfg['hover_prefix']}: {d}%{{z:{f}}}{s}<br>"
            f"MOE: \u00b1{d}%{{customdata[0]:{mf}}}{s}<extra></extra>")


def multi_line_hover(var_cfg, geo_name, cat_name):
    d = "$" if var_cfg.get("hover_dollar") else ""
    s = var_cfg.get("hover_suffix", "")
    f = var_cfg["hover_format"]
    return (f"<b>{geo_name}</b><br>{cat_name}<br>Year: %{{x}}<br>"
            f"{var_cfg['hover_prefix']}: {d}%{{y:{f}}}{s}<br>"
            f"MOE: \u00b1{d}%{{customdata[0]:{f}}}{s}<extra></extra>")


# =====================================================================
# SAFE FILENAME HELPER
# =====================================================================
def _safe(name):
    return name.replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '')


# =====================================================================
# HTML DASHBOARD TEMPLATES  (v2 — polished modern design)
# =====================================================================
def _css_base():
    """Shared CSS for all dashboard wrappers — modern, clean header."""
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


# ─── Simple Bar Dashboard ────────────────────────────────────────────
def simple_bar_html(title, file_bar_county, bar_county_opts):
    return f"""<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>{_css_base()} #subdivSelect {{ display: none; }}</style>
<script>
function updateView() {{
    var mode = document.getElementById('viewMode').value;
    var subSel = document.getElementById('subdivSelect');
    var frame = document.getElementById('chartFrame');
    if (mode === 'county') {{ subSel.style.display = 'none'; frame.src = "charts/{file_bar_county}"; }}
    else {{ subSel.style.display = 'inline-block'; frame.src = subSel.value; }}
}}
function loadSubChart() {{ document.getElementById('chartFrame').src = document.getElementById('subdivSelect').value; }}
</script>
</head><body>
<div class="card">
    <div class="header">
        <h2>{title}</h2>
        <div class="controls-row">
            <select id="viewMode" onchange="updateView()">
                <option value="county">By County</option>
                <option value="subdiv">By Subdivision</option>
            </select>
            <select id="subdivSelect" onchange="loadSubChart()">
                {bar_county_opts}
            </select>
        </div>
    </div>
    <iframe id="chartFrame" src="charts/{file_bar_county}"></iframe>
</div></body></html>"""


# ─── Simple Line Dashboard ───────────────────────────────────────────
def simple_line_html(title, file_line_county, line_county_opts):
    return f"""<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>{_css_base()} #subdivSelect {{ display: none; }}</style>
<script>
function updateView() {{
    var mode = document.getElementById('viewMode').value;
    var subSel = document.getElementById('subdivSelect');
    var frame = document.getElementById('chartFrame');
    if (mode === 'county') {{ subSel.style.display = 'none'; frame.src = "charts/{file_line_county}"; }}
    else {{ subSel.style.display = 'inline-block'; frame.src = subSel.value; }}
}}
function loadSubChart() {{ document.getElementById('chartFrame').src = document.getElementById('subdivSelect').value; }}
</script>
</head><body>
<div class="card">
    <div class="header">
        <h2>{title} — Trends</h2>
        <div class="controls-row">
            <select id="viewMode" onchange="updateView()">
                <option value="county">By County</option>
                <option value="subdiv">By Subdivision</option>
            </select>
            <select id="subdivSelect" onchange="loadSubChart()">
                {line_county_opts}
            </select>
        </div>
    </div>
    <iframe id="chartFrame" src="charts/{file_line_county}"></iframe>
</div></body></html>"""


# ─── Simple Map Dashboard ────────────────────────────────────────────
def simple_map_html(title, var_name, county_options):
    return f"""<!DOCTYPE html>
<html><head>
<title>{title} Maps</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>{_css_base()} #countySelect {{ display: none; }} iframe {{ height: 100%; }}
select {{ max-width: 160px; }}</style>
<script>
var currentDeviceMode = 'desktop';
function setDeviceMode(mode) {{
    currentDeviceMode = mode;
    document.getElementById('btn-desktop').classList.toggle('active', mode === 'desktop');
    document.getElementById('btn-mobile').classList.toggle('active', mode === 'mobile');
    updateMapSource();
}}
function updateViewType() {{
    document.getElementById('countySelect').style.display =
        (document.getElementById('viewMode').value === 'county') ? 'none' : 'inline-block';
    updateMapSource();
}}
function updateMapSource() {{
    var type = document.getElementById('viewMode').value;
    if (type === 'county') {{
        document.getElementById('mainFrame').src = "maps/map_county_{var_name}_" + currentDeviceMode + ".html";
    }} else {{
        document.getElementById('mainFrame').src = document.getElementById('countySelect').value + "_" + currentDeviceMode + ".html";
    }}
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
            <select id="viewMode" onchange="updateViewType()">
                <option value="county">By County</option>
                <option value="subdiv">By Subdivision</option>
            </select>
            <select id="countySelect" onchange="updateMapSource()">
                <option value="maps/Region_map">All Subdivisions</option>
                {county_options}
            </select>
        </div>
    </div>
    <iframe id="mainFrame" src="maps/map_county_{var_name}_desktop.html"></iframe>
</div></body></html>"""


# ─── Multi-Category Bar Dashboard ────────────────────────────────────
def multi_bar_html(title, file_bar_county, file_bar_subdiv, latest_year):
    return f"""<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>{_css_base()}</style>
<script>
function switchView() {{ document.getElementById('chartFrame').src = "charts/" + document.getElementById('viewSelector').value; }}
</script>
</head><body>
<div class="card">
    <div class="header">
        <h2>{title} ({latest_year})</h2>
        <select id="viewSelector" onchange="switchView()">
            <option value="{file_bar_county}">By County</option>
            <option value="{file_bar_subdiv}">By Subdivision</option>
        </select>
    </div>
    <iframe id="chartFrame" src="charts/{file_bar_county}"></iframe>
</div></body></html>"""


# ─── Multi-Category Line Dashboard ──────────────────────────────────
def multi_line_html(title, order_list, first_safe_race, *_):
    race_options = "\n".join(f'<option value="{_safe(r)}">{r}</option>' for r in order_list)
    return f"""<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>{_css_base()}</style>
<script>
function updateChart() {{
    var level = document.getElementById('levelSelector').value;
    var variable = document.getElementById('varSelector').value;
    document.getElementById('chartFrame').src = "charts/line_" + level + "_" + variable + ".html";
}}
</script>
</head><body>
<div class="card">
    <div class="header">
        <h2>{title} — Trends</h2>
        <div class="controls-row">
            <select id="levelSelector" onchange="updateChart()">
                <option value="county">By County</option>
                <option value="subdiv">By Subdivision</option>
            </select>
            <select id="varSelector" onchange="updateChart()">
                {race_options}
            </select>
        </div>
    </div>
    <iframe id="chartFrame" src="charts/line_county_{first_safe_race}.html"></iframe>
</div></body></html>"""


# ─── Multi-Category Map Dashboard ───────────────────────────────────
def multi_map_html(title, order_list, first_safe_race):
    race_map_opts = "\n".join(f'<option value="{_safe(r)}">{r}</option>' for r in order_list)
    return f"""<!DOCTYPE html>
<html><head>
<title>{title} Maps</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>{_css_base()} select {{ max-width: 160px; }} iframe {{ height: 100%; }}</style>
<script>
var currentDeviceMode = 'desktop';
function setDeviceMode(mode) {{
    currentDeviceMode = mode;
    document.getElementById('btn-desktop').classList.toggle('active', mode === 'desktop');
    document.getElementById('btn-mobile').classList.toggle('active', mode === 'mobile');
    updateMapSource();
}}
function updateMapSource() {{
    var level = document.getElementById('levelSelector').value;
    var race = document.getElementById('raceSelector').value;
    document.getElementById('mainFrame').src = "maps/map_" + level + "_" + race + "_" + currentDeviceMode + ".html";
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
            <select id="levelSelector" onchange="updateMapSource()">
                <option value="county">By County</option>
                <option value="subdiv">By Subdivision</option>
            </select>
            <select id="raceSelector" onchange="updateMapSource()">
                {race_map_opts}
            </select>
        </div>
    </div>
    <iframe id="mainFrame" src="maps/map_county_{first_safe_race}_desktop.html"></iframe>
</div></body></html>"""
