"""
ACT Dashboard Pipeline v2 — Simple Variable Pipeline
======================================================
v2: improved chart visuals, source as HTML footer, _v2 output folders.
"""

import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils import (
    COLOR_PRIMARY, COLOR_PRIMARY_LT, COLOR_DARK, COLOR_ERROR_BAR, COLOR_GRID, COLOR_MUTED,
    BRAND_COLOR_SCALE, COMMON_LAYOUT, MOBILE_CONFIG,
    get_zoom, get_bar_range, get_line_range, calculate_clamped_errors,
    bar_hover, line_hover, map_hover,
    build_source_annotation, write_chart_html,
    simple_bar_html, simple_line_html, simple_map_html,
)


def run(var_cfg, df, df_counties, recent_df, recent_counties_df,
        gdf_sub, gdf_cty, output_dir, charts_dir, maps_dir):

    var_name  = var_cfg["name"]
    title     = var_cfg["title"]
    dtype     = var_cfg["data_type"]
    y_label   = var_cfg["y_label"]
    acs_table = var_cfg.get("acs_table", "")
    var_lower = var_name.lower()

    all_years = sorted(df['year'].dropna().unique())
    latest_year = df['year'].max()

    # ==================================================================
    # A. BAR CHARTS  (snapshot — single year)
    # ==================================================================
    print(f"  [{var_name}] Bar charts...")

    src_bar = build_source_annotation(acs_table, None, single_year=int(latest_year))
    file_bar_county = f"bar_county_{var_lower}.html"

    # --- County Bar ---
    sorted_cty = recent_counties_df.sort_values(by='estimate', ascending=False)
    y_val  = sorted_cty['estimate'].tolist()
    moe_val = sorted_cty['moe'].fillna(0).tolist()
    e_minus, e_plus = calculate_clamped_errors(y_val, moe_val, dtype)

    fig = go.Figure(go.Bar(
        x=sorted_cty['County'], y=sorted_cty['estimate'],
        marker=dict(color=COLOR_PRIMARY, cornerradius=3, line=dict(width=0)),
        error_y=dict(type='data', symmetric=False, array=e_plus, arrayminus=e_minus,
                     color=COLOR_ERROR_BAR, thickness=1.5, width=4),
        customdata=sorted_cty[['moe']].fillna(0).values,
        hovertemplate=bar_hover(var_cfg),
    ))
    fig.update_layout(COMMON_LAYOUT)
    fig.update_layout(
        xaxis_title="", yaxis_title=y_label,
        margin=dict(t=20, b=80, l=55, r=20),
        yaxis=dict(showgrid=True, gridcolor=COLOR_GRID, gridwidth=1, griddash='dot',
                   zeroline=False, range=get_bar_range(sorted_cty, dtype), fixedrange=True),
        bargap=0.25,
    )
    write_chart_html(fig, os.path.join(charts_dir, file_bar_county), src_bar)

    # --- Subdivision Bars ---
    clean_sub = recent_df[
        (recent_df['Geography'] != 'COUNTY SUBDIVISIONS NOT DEFINED') &
        (recent_df['estimate'].notnull()) & (recent_df['estimate'] > 0)
    ].copy().sort_values(by='Geography')
    counties = sorted(clean_sub['County'].unique())
    bar_file_dict = {}

    for c in counties:
        df_f = clean_sub[clean_sub['County'] == c]
        y_v = df_f['estimate'].tolist()
        m_v = df_f['moe'].fillna(0).tolist()
        em, ep = calculate_clamped_errors(y_v, m_v, dtype)

        fig_s = go.Figure(go.Bar(
            x=df_f['Geography'], y=df_f['estimate'],
            marker=dict(color=COLOR_PRIMARY, cornerradius=3, line=dict(width=0)),
            error_y=dict(type='data', symmetric=False, array=ep, arrayminus=em,
                         color=COLOR_ERROR_BAR, thickness=1.5, width=4),
            customdata=df_f[['moe']].fillna(0).values,
            hovertemplate=bar_hover(var_cfg),
        ))
        fig_s.update_layout(COMMON_LAYOUT)
        fig_s.update_layout(
            yaxis_title=y_label,
            margin=dict(t=20, b=120, l=55, r=20),
            yaxis=dict(showgrid=True, gridcolor=COLOR_GRID, gridwidth=1, griddash='dot',
                       zeroline=False, range=get_bar_range(df_f, dtype), fixedrange=True),
            bargap=0.25,
        )
        safe = c.replace(' ', '_')
        fname = f"bar_subdivision_{safe}.html"
        write_chart_html(fig_s, os.path.join(charts_dir, fname), src_bar)
        bar_file_dict[c] = f"charts/{fname}"

    bar_opts = '\n'.join(f'<option value="{p}">{n}</option>' for n, p in bar_file_dict.items())
    with open(os.path.join(output_dir, f"bar_final_{var_lower}.html"), "w", encoding="utf-8") as f:
        f.write(simple_bar_html(title, file_bar_county, bar_opts))

    # ==================================================================
    # B. LINE CHARTS  (longitudinal — year range)
    # ==================================================================
    print(f"  [{var_name}] Line charts...")

    src_line = build_source_annotation(acs_table, all_years)
    file_line_county = f"line_county_{var_lower}.html"
    unique_counties = sorted(df_counties['County'].unique())

    # --- County Line ---
    fig_cl = go.Figure()
    init_range = get_line_range(df_counties[df_counties['County'] == unique_counties[0]], dtype)

    for i, county in enumerate(unique_counties):
        filt = df_counties[df_counties['County'] == county]
        y_val  = filt['estimate'].tolist()
        moe_val = filt['moe'].fillna(0).tolist()
        em, ep = calculate_clamped_errors(y_val, moe_val, dtype)

        fig_cl.add_trace(go.Scatter(
            x=filt['year'], y=filt['estimate'],
            error_y=dict(type="data", array=ep, arrayminus=em, visible=True,
                         color=COLOR_ERROR_BAR, width=2, thickness=1.5, symmetric=False),
            mode="lines+markers", name=county, visible=(i == 0),
            marker=dict(size=8, color=COLOR_PRIMARY, line=dict(width=2, color='white')),
            line=dict(color=COLOR_PRIMARY, width=2.5),
            customdata=filt[['moe']].fillna(0).values,
            hovertemplate=line_hover(var_cfg),
        ))

    county_btns = []
    for i, county in enumerate(unique_counties):
        vis = [False] * len(unique_counties); vis[i] = True
        r = get_line_range(df_counties[df_counties['County'] == county], dtype)
        county_btns.append(dict(label=county, method="update",
                                args=[{"visible": vis}, {"yaxis.range": r}]))

    fig_cl.update_layout(COMMON_LAYOUT)
    fig_cl.update_layout(
        xaxis_title="Year", yaxis_title=y_label,
        margin=dict(t=90, b=50, l=55, r=20),
        updatemenus=[dict(active=0, buttons=county_btns, x=1.0, y=1.22,
                          xanchor='right', yanchor='top', bgcolor='white',
                          bordercolor=COLOR_GRID, borderwidth=1.5,
                          font=dict(family="DM Sans, sans-serif", size=12))],
        yaxis=dict(showgrid=True, gridcolor=COLOR_GRID, gridwidth=1, griddash='dot',
                   zeroline=False, range=init_range, fixedrange=True),
    )
    write_chart_html(fig_cl, os.path.join(charts_dir, file_line_county), src_line)

    # --- Subdivision Lines ---
    line_file_dict = {}
    for county in counties:
        subs = sorted(clean_sub[clean_sub['County'] == county]['Geography'].unique())
        if not subs:
            continue
        fig_sl = go.Figure()
        init_sub_range = get_line_range(df[df['Geography'] == subs[0]], dtype)

        for i, sub in enumerate(subs):
            filt = df[df['Geography'] == sub]
            y_val  = filt['estimate'].tolist()
            moe_val = filt['moe'].fillna(0).tolist()
            em, ep = calculate_clamped_errors(y_val, moe_val, dtype)

            fig_sl.add_trace(go.Scatter(
                x=filt['year'], y=filt['estimate'],
                error_y=dict(type="data", array=ep, arrayminus=em,
                             color=COLOR_ERROR_BAR, width=2, thickness=1.5, symmetric=False),
                mode="lines+markers", name=sub, visible=(i == 0),
                marker=dict(size=8, color=COLOR_PRIMARY, line=dict(width=2, color='white')),
                line=dict(color=COLOR_PRIMARY, width=2.5),
                customdata=filt[['moe']].fillna(0).values,
                hovertemplate=line_hover(var_cfg),
            ))

        sub_btns = []
        for i, sub in enumerate(subs):
            vis = [False] * len(subs); vis[i] = True
            r = get_line_range(df[df['Geography'] == sub], dtype)
            sub_btns.append(dict(label=sub, method="update",
                                 args=[{"visible": vis}, {"yaxis.range": r}]))

        fig_sl.update_layout(COMMON_LAYOUT)
        fig_sl.update_layout(
            xaxis_title="Year", yaxis_title=y_label,
            margin=dict(t=90, b=50, l=55, r=20),
            updatemenus=[dict(active=0, buttons=sub_btns, x=1.0, y=1.22,
                              xanchor='right', yanchor='top', bgcolor='white',
                              bordercolor=COLOR_GRID, borderwidth=1.5,
                              font=dict(family="DM Sans, sans-serif", size=12))],
            yaxis=dict(showgrid=True, gridcolor=COLOR_GRID, gridwidth=1, griddash='dot',
                       zeroline=False, range=init_sub_range, fixedrange=True),
        )
        safe = county.replace(' ', '_')
        fname = f"line_subdivision_{safe}.html"
        write_chart_html(fig_sl, os.path.join(charts_dir, fname), src_line)
        line_file_dict[county] = f"charts/{fname}"

    line_opts = '\n'.join(f'<option value="{p}">{n}</option>' for n, p in line_file_dict.items())
    with open(os.path.join(output_dir, f"line_final_{var_lower}.html"), "w", encoding="utf-8") as f:
        f.write(simple_line_html(title, file_line_county, line_opts))

    # ==================================================================
    # C. MAPS
    # ==================================================================
    print(f"  [{var_name}] Maps...")

    src_map = build_source_annotation(acs_table, None, single_year=int(latest_year))

    filtered_sub = gdf_sub.merge(recent_df, on="GEOID")
    filtered_cty = gdf_cty.merge(recent_counties_df, on="GEOID")
    reg_center = {
        "lat": filtered_cty.geometry.centroid.y.mean(),
        "lon": filtered_cty.geometry.centroid.x.mean(),
    }

    def save_map(gdf, zoom, center, filepath, label_col):
        clean = gdf[~((gdf['estimate'] == 0) & (gdf['moe'].fillna(0) == 0))]
        if clean.empty:
            return
        fig_m = px.choropleth_mapbox(
            clean, geojson=clean.set_index("GEOID").geometry, locations="GEOID",
            color="estimate", hover_name=label_col, hover_data=["moe"],
            mapbox_style="carto-positron", opacity=0.85,
            zoom=zoom, center=center, color_continuous_scale=BRAND_COLOR_SCALE,
        )
        fig_m.update_traces(hovertemplate=map_hover(var_cfg))
        fig_m.update_layout(COMMON_LAYOUT)
        fig_m.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            coloraxis_colorbar=dict(
                title="", len=0.45, thickness=14, yanchor="bottom", y=0.06,
                xanchor="right", x=0.96,
                bgcolor="rgba(255,255,255,0.85)", outlinewidth=0,
                tickfont=dict(size=10, color=COLOR_MUTED),
            ),
        )
        write_chart_html(fig_m, filepath, src_map)

    for mode in ('desktop', 'mobile'):
        save_map(filtered_cty, get_zoom(filtered_cty, mode), reg_center,
                 os.path.join(maps_dir, f"map_county_{var_name}_{mode}.html"), "County")
        save_map(filtered_sub, get_zoom(filtered_cty, mode), reg_center,
                 os.path.join(maps_dir, f"Region_map_{mode}.html"), "Geography")

    map_base_dict = {}
    for county in sorted(filtered_sub['County'].unique()):
        sub = filtered_sub[filtered_sub.County == county]
        c_center = {"lat": sub.geometry.centroid.y.mean(), "lon": sub.geometry.centroid.x.mean()}
        base = county.replace(' ', '_') + "_map"
        for mode in ('desktop', 'mobile'):
            save_map(sub, get_zoom(sub, mode), c_center,
                     os.path.join(maps_dir, f"{base}_{mode}.html"), "Geography")
        map_base_dict[county] = f"maps/{base}"

    cty_opts = '\n'.join(f'<option value="{p}">{n}</option>' for n, p in map_base_dict.items())
    with open(os.path.join(output_dir, f"map_final_{var_lower}.html"), "w", encoding="utf-8") as f:
        f.write(simple_map_html(title, var_name, cty_opts))

    print(f"  [{var_name}] Done")
