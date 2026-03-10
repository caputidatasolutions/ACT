"""
ACT Dashboard Pipeline v2 — Multi-Category Pipeline
=====================================================
v2: improved visuals, source as HTML footer, _v2 output folders.
"""

import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils import (
    COLOR_PRIMARY, COLOR_ERROR_BAR, COLOR_GRID, COLOR_MUTED,
    BRAND_COLOR_SCALE, COMMON_LAYOUT, MOBILE_CONFIG,
    get_zoom, get_bar_range, get_line_range, calculate_clamped_errors,
    bar_hover, map_hover, multi_line_hover, _safe,
    build_source_annotation, write_chart_html,
    multi_bar_html, multi_line_html, multi_map_html,
)


def run(var_cfg, df, df_counties, recent_df, recent_counties_df,
        gdf_sub, gdf_cty, output_dir, charts_dir, maps_dir):

    var_name  = var_cfg["name"]
    title     = var_cfg["title"]
    dtype     = var_cfg["data_type"]
    y_label   = var_cfg["y_label"]
    order     = var_cfg["order"]
    color_map = var_cfg["color_map"]
    symbol_map = var_cfg.get("symbol_map", {})
    cat_col   = var_cfg.get("category_col", "Variable_Description")
    acs_table = var_cfg.get("acs_table", "")

    all_years = sorted(df['year'].dropna().unique())
    latest_year = df['year'].max()

    # --- DATA PREP ---
    def prepare(dataframe):
        # Log any categories in the data that aren't in our order list
        actual_cats = dataframe[cat_col].dropna().unique()
        unmatched = [c for c in actual_cats if c not in order]
        if unmatched:
            print(f"  WARNING: [{var_name}] Found categories not in order list: {unmatched}")
            matched = [c for c in actual_cats if c in order]
            print(f"  Matched categories: {matched}")
        dataframe[cat_col] = pd.Categorical(dataframe[cat_col], categories=order, ordered=True)
        # Drop rows where category didn't match (NaN after Categorical conversion)
        before = len(dataframe)
        dataframe = dataframe.dropna(subset=[cat_col])
        after = len(dataframe)
        if before != after:
            print(f"  WARNING: [{var_name}] Dropped {before - after} rows with unmatched categories")
        return dataframe.sort_values(['County', 'Geography', 'year', cat_col])

    df_agg     = prepare(df.copy())
    df_cty_agg = prepare(df_counties.copy())
    recent_agg     = df_agg[df_agg['year'] == latest_year].copy()
    recent_cty_agg = df_cty_agg[df_cty_agg['year'] == latest_year].copy()

    # ==================================================================
    # A. BAR CHARTS
    # ==================================================================
    print(f"  [{var_name}] Bar charts...")

    src_bar = build_source_annotation(acs_table, None, single_year=int(latest_year))
    file_bar_county = f"bar_county_{var_name}.html"
    file_bar_subdiv = f"bar_subdivision_{var_name}.html"
    unique_counties = sorted(recent_cty_agg['County'].unique())

    # --- County Bar ---
    fig_bc = go.Figure()
    for i, county in enumerate(unique_counties):
        cdata = recent_cty_agg[recent_cty_agg['County'] == county].sort_values(cat_col).dropna(subset=['estimate'])
        x = cdata[cat_col].tolist()
        y = cdata['estimate'].tolist()
        m = cdata['moe'].fillna(0).tolist()
        em, ep = calculate_clamped_errors(y, m, dtype)
        colors = [color_map.get(r, '#6B7280') for r in x]

        fig_bc.add_trace(go.Bar(
            x=x, y=y, name=county,
            error_y=dict(type='data', symmetric=False, array=ep, arrayminus=em,
                         color=COLOR_ERROR_BAR, thickness=1.5, width=4),
            visible=(i == 0), marker=dict(color=colors, cornerradius=3, line=dict(width=0)),
            customdata=list(zip(m)),
            hovertemplate=bar_hover(var_cfg), showlegend=False,
        ))

    btns = []
    for i, county in enumerate(unique_counties):
        vis = [False] * len(unique_counties); vis[i] = True
        cdata_btn = recent_cty_agg[recent_cty_agg['County'] == county].dropna(subset=['estimate'])
        r = get_bar_range(cdata_btn, dtype)
        btns.append(dict(label=county, method="update", args=[{"visible": vis}, {"yaxis.range": r}]))

    # Initial range from first county
    init_cty_data = recent_cty_agg[recent_cty_agg['County'] == unique_counties[0]].dropna(subset=['estimate'])
    init_bar_range = get_bar_range(init_cty_data, dtype)

    fig_bc.update_layout(COMMON_LAYOUT)
    fig_bc.update_layout(
        yaxis_title=y_label, xaxis_title="",
        updatemenus=[dict(active=0, buttons=btns, x=1.0, y=1.12,
                          xanchor='right', yanchor='top', bgcolor='white',
                          bordercolor=COLOR_GRID, borderwidth=1.5,
                          font=dict(family="DM Sans, sans-serif", size=12))],
        margin=dict(t=50, b=100, l=55, r=20), showlegend=False, bargap=0.22,
        yaxis=dict(showgrid=True, gridcolor=COLOR_GRID, gridwidth=1, griddash='dot',
                   zeroline=False, range=init_bar_range, fixedrange=True),
    )
    write_chart_html(fig_bc, os.path.join(charts_dir, file_bar_county), src_bar)

    # --- Subdivision Bar ---
    clean_sub = recent_agg[
        (recent_agg['Geography'] != 'COUNTY SUBDIVISIONS NOT DEFINED') &
        (recent_agg['estimate'].notnull())
    ].copy()
    all_subs = sorted(clean_sub['Geography'].unique())

    if all_subs:
        fig_bs = go.Figure()
        for i, sub in enumerate(all_subs):
            sdata = clean_sub[clean_sub['Geography'] == sub].sort_values(cat_col)
            x = sdata[cat_col].tolist()
            y = sdata['estimate'].tolist()
            m = sdata['moe'].fillna(0).tolist()
            em, ep = calculate_clamped_errors(y, m, dtype)
            colors = [color_map.get(r, '#6B7280') for r in x]

            fig_bs.add_trace(go.Bar(
                x=x, y=y, name=sub,
                error_y=dict(type='data', symmetric=False, array=ep, arrayminus=em,
                             color=COLOR_ERROR_BAR, thickness=1.5, width=4),
                visible=(i == 0), marker=dict(color=colors, cornerradius=3, line=dict(width=0)),
                customdata=list(zip(m)),
                hovertemplate=bar_hover(var_cfg), showlegend=False,
            ))

        sbtns = []
        for i, sub in enumerate(all_subs):
            vis = [False] * len(all_subs); vis[i] = True
            sdata_btn = clean_sub[clean_sub['Geography'] == sub].dropna(subset=['estimate'])
            r = get_bar_range(sdata_btn, dtype)
            sbtns.append(dict(label=sub, method="update", args=[{"visible": vis}, {"yaxis.range": r}]))

        # Initial range from first subdivision
        init_sub_data = clean_sub[clean_sub['Geography'] == all_subs[0]].dropna(subset=['estimate'])
        init_sub_bar_range = get_bar_range(init_sub_data, dtype)

        fig_bs.update_layout(COMMON_LAYOUT)
        fig_bs.update_layout(
            yaxis_title=y_label, xaxis_title="",
            updatemenus=[dict(active=0, buttons=sbtns, x=1.0, y=1.12,
                              xanchor='right', yanchor='top', bgcolor='white',
                              bordercolor=COLOR_GRID, borderwidth=1.5,
                              font=dict(family="DM Sans, sans-serif", size=12))],
            margin=dict(t=50, b=100, l=55, r=20), showlegend=False, bargap=0.22,
            yaxis=dict(showgrid=True, gridcolor=COLOR_GRID, gridwidth=1, griddash='dot',
                       zeroline=False, range=init_sub_bar_range, fixedrange=True),
        )
        write_chart_html(fig_bs, os.path.join(charts_dir, file_bar_subdiv), src_bar)

    with open(os.path.join(output_dir, f"bar_final_{var_name}.html"), "w", encoding="utf-8") as f:
        f.write(multi_bar_html(title, file_bar_county, file_bar_subdiv, int(latest_year)))

    # ==================================================================
    # B. LINE CHARTS
    # ==================================================================
    print(f"  [{var_name}] Line charts...")

    src_line = build_source_annotation(acs_table, all_years)

    clean_sub_agg = df_agg[
        (df_agg['Geography'] != 'COUNTY SUBDIVISIONS NOT DEFINED') &
        (df_agg['estimate'].notnull())
    ].copy()
    unique_subs = sorted(clean_sub_agg['Geography'].unique())

    for cat in order:
        safe_cat   = _safe(cat)
        cat_color  = color_map.get(cat, '#6B7280')
        cat_symbol = symbol_map.get(cat, 'circle')

        # County line
        df_cat_cty = df_cty_agg[df_cty_agg[cat_col] == cat]
        fig_lc = go.Figure()

        for i, county in enumerate(unique_counties):
            d = df_cat_cty[df_cat_cty['County'] == county]
            has_data = not d.empty and d['estimate'].notna().any()
            if has_data:
                y = d['estimate'].tolist()
                m = d['moe'].fillna(0).tolist()
                em, ep = calculate_clamped_errors(y, m, dtype)
                fig_lc.add_trace(go.Scatter(
                    x=d['year'], y=d['estimate'],
                    mode='lines+markers', name=county, visible=(i == 0),
                    line=dict(color=cat_color, width=2.5),
                    marker=dict(symbol=cat_symbol, size=9, color=cat_color,
                                line=dict(width=2, color='white')),
                    error_y=dict(type='data', array=ep, arrayminus=em, visible=True,
                                 color=COLOR_ERROR_BAR, width=2, thickness=1.5, symmetric=False),
                    hovertemplate=multi_line_hover(var_cfg, county, cat),
                    customdata=d[['moe']],
                ))
            else:
                fig_lc.add_trace(go.Scatter(
                    x=[2020], y=[0], mode='text', text=["NO DATA"],
                    name=county, visible=(i == 0), showlegend=False, hoverinfo='skip',
                ))

        cbtns = []
        for i, county in enumerate(unique_counties):
            vis = [False] * len(unique_counties); vis[i] = True
            r = get_line_range(df_cat_cty[df_cat_cty['County'] == county], dtype)
            cbtns.append(dict(label=county, method="update", args=[{"visible": vis}, {"yaxis.range": r}]))

        init_r = get_line_range(df_cat_cty[df_cat_cty['County'] == unique_counties[0]], dtype)
        fig_lc.update_layout(COMMON_LAYOUT)
        fig_lc.update_layout(
            yaxis_title=y_label, xaxis_title="Year",
            margin=dict(t=90, b=50, l=55, r=20), showlegend=False,
            updatemenus=[dict(active=0, buttons=cbtns, x=1.0, y=1.22,
                              xanchor='right', yanchor='top', bgcolor='white',
                              bordercolor=COLOR_GRID, borderwidth=1.5,
                              font=dict(family="DM Sans, sans-serif", size=12))],
            yaxis=dict(showgrid=True, gridcolor=COLOR_GRID, gridwidth=1, griddash='dot',
                       zeroline=False, range=init_r, fixedrange=True),
        )
        write_chart_html(fig_lc, os.path.join(charts_dir, f"line_county_{safe_cat}.html"), src_line)

        # Subdivision line
        if unique_subs:
            df_cat_sub = clean_sub_agg[clean_sub_agg[cat_col] == cat]
            fig_ls = go.Figure()

            for i, sub in enumerate(unique_subs):
                d = df_cat_sub[df_cat_sub['Geography'] == sub]
                has_data = not d.empty and d['estimate'].notna().any()
                if has_data:
                    y = d['estimate'].tolist()
                    m = d['moe'].fillna(0).tolist()
                    em, ep = calculate_clamped_errors(y, m, dtype)
                    fig_ls.add_trace(go.Scatter(
                        x=d['year'], y=d['estimate'],
                        mode='lines+markers', name=sub, visible=(i == 0),
                        line=dict(color=cat_color, width=2.5),
                        marker=dict(symbol=cat_symbol, size=9, color=cat_color,
                                    line=dict(width=2, color='white')),
                        error_y=dict(type='data', array=ep, arrayminus=em, visible=True,
                                     color=COLOR_ERROR_BAR, width=2, thickness=1.5, symmetric=False),
                        hovertemplate=multi_line_hover(var_cfg, sub, cat),
                        customdata=d[['moe']],
                    ))
                else:
                    fig_ls.add_trace(go.Scatter(
                        x=[2020], y=[0], mode='text', text=["NO DATA"],
                        name=sub, visible=(i == 0), showlegend=False, hoverinfo='skip',
                    ))

            sbtns = []
            for i, sub in enumerate(unique_subs):
                vis = [False] * len(unique_subs); vis[i] = True
                r = get_line_range(df_cat_sub[df_cat_sub['Geography'] == sub], dtype)
                sbtns.append(dict(label=sub, method="update", args=[{"visible": vis}, {"yaxis.range": r}]))

            init_r = get_line_range(df_cat_sub[df_cat_sub['Geography'] == unique_subs[0]], dtype)
            fig_ls.update_layout(COMMON_LAYOUT)
            fig_ls.update_layout(
                yaxis_title=y_label, xaxis_title="Year",
                margin=dict(t=90, b=50, l=55, r=20), showlegend=False,
                updatemenus=[dict(active=0, buttons=sbtns, x=1.0, y=1.22,
                                  xanchor='right', yanchor='top', bgcolor='white',
                                  bordercolor=COLOR_GRID, borderwidth=1.5,
                                  font=dict(family="DM Sans, sans-serif", size=12))],
                yaxis=dict(showgrid=True, gridcolor=COLOR_GRID, gridwidth=1, griddash='dot',
                           zeroline=False, range=init_r, fixedrange=True),
            )
            write_chart_html(fig_ls, os.path.join(charts_dir, f"line_subdiv_{safe_cat}.html"), src_line)

    first_safe = _safe(order[0])
    with open(os.path.join(output_dir, f"line_final_{var_name}.html"), "w", encoding="utf-8") as f:
        f.write(multi_line_html(title, order, first_safe))

    # ==================================================================
    # C. MAPS
    # ==================================================================
    print(f"  [{var_name}] Maps...")

    src_map = build_source_annotation(acs_table, None, single_year=int(latest_year))

    filtered_sub = gdf_sub.merge(recent_agg, on="GEOID")
    filtered_cty = gdf_cty.merge(recent_cty_agg, on="GEOID")
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
                xanchor="right", x=0.96, bgcolor="rgba(255,255,255,0.85)",
                outlinewidth=0, tickfont=dict(size=10, color=COLOR_MUTED)),
        )
        write_chart_html(fig_m, filepath, src_map)

    for cat in order:
        safe_cat = _safe(cat)
        df_cty_race = filtered_cty[filtered_cty[cat_col] == cat]
        df_sub_race = filtered_sub[filtered_sub[cat_col] == cat]
        for mode in ('desktop', 'mobile'):
            save_map(df_cty_race, get_zoom(filtered_cty, mode), reg_center,
                     os.path.join(maps_dir, f"map_county_{safe_cat}_{mode}.html"), "County")
            save_map(df_sub_race, get_zoom(filtered_cty, mode), reg_center,
                     os.path.join(maps_dir, f"map_subdiv_{safe_cat}_{mode}.html"), "Geography")

    first_safe = _safe(order[0])
    with open(os.path.join(output_dir, f"map_final_{var_name}.html"), "w", encoding="utf-8") as f:
        f.write(multi_map_html(title, order, first_safe))

    print(f"  [{var_name}] Done")
