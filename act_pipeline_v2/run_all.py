"""
ACT Dashboard Pipeline v2 — Main Runner
=========================================
Processes all (or selected) variables. Outputs go to Output_<name>_v2/ folders
so your existing work is never overwritten.

Usage:
    python run_all.py                                        # All variables
    python run_all.py --only Median_Rent                     # One variable
    python run_all.py --only "Median_Rent,Total_Population"  # Several
    python run_all.py --base-path "C:\\Users\\camer\\Desktop\\ACT"
"""

import os
import sys
import time
import argparse

import pandas as pd
import geopandas as gpd

from config import VARIABLES, VARIABLE_MAP
import pipeline_simple
import pipeline_multi


def main():
    parser = argparse.ArgumentParser(description="ACT Dashboard Generator v2")
    parser.add_argument("--base-path", default=r"C:\Users\camer\Desktop\ACT",
                        help="Root project directory")
    parser.add_argument("--only", default=None,
                        help="Comma-separated variable names (default: all)")
    parser.add_argument("--skip-shapes-cache", action="store_true",
                        help="Force re-read of shapefiles")
    args = parser.parse_args()

    BASE = args.base_path

    # --- Select variables ---
    if args.only:
        names = [n.strip() for n in args.only.split(",")]
        variables = [VARIABLE_MAP[n] for n in names if n in VARIABLE_MAP]
        missing = [n for n in names if n not in VARIABLE_MAP]
        if missing:
            print(f"WARNING: Unknown variable(s): {missing}")
    else:
        variables = VARIABLES

    if not variables:
        print("No variables to process.")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"ACT Dashboard Pipeline v2 — {len(variables)} variable(s)")
    print(f"Base: {BASE}")
    print(f"Output suffix: _v2  (your existing folders are safe)")
    print(f"{'='*60}\n")

    # --- Load shapes ONCE ---
    shp_sub = os.path.join(BASE, "shapes", "most_recent_subdivision_shapes.geojson")
    shp_cty = os.path.join(BASE, "shapes", "most_recent_county_shapes.geojson")
    cache_sub = shp_sub.replace(".geojson", "_simplified.geojson")
    cache_cty = shp_cty.replace(".geojson", "_simplified.geojson")

    if not args.skip_shapes_cache and os.path.exists(cache_sub) and os.path.exists(cache_cty):
        print("Loading cached simplified shapes...")
        gdf_sub = gpd.read_file(cache_sub)
        gdf_cty = gpd.read_file(cache_cty)
    else:
        print("Loading & simplifying shapes (will cache for next run)...")
        gdf_sub = gpd.read_file(shp_sub)
        gdf_cty = gpd.read_file(shp_cty)
        gdf_sub['geometry'] = gdf_sub['geometry'].simplify(tolerance=0.001, preserve_topology=True)
        gdf_cty['geometry'] = gdf_cty['geometry'].simplify(tolerance=0.001, preserve_topology=True)
        try:
            gdf_sub.to_file(cache_sub, driver="GeoJSON")
            gdf_cty.to_file(cache_cty, driver="GeoJSON")
            print(f"  Cached to {cache_sub}")
        except Exception as e:
            print(f"  Could not cache: {e}")

    gdf_sub['GEOID'] = gdf_sub['GEOID'].astype(str)
    gdf_cty['GEOID'] = gdf_cty['GEOID'].astype(str)

    # --- Process variables ---
    t0 = time.time()
    ok, fail = [], []

    for var_cfg in variables:
        var_name = var_cfg["name"]
        ptype    = var_cfg["pipeline"]
        print(f"\n--- [{var_name}] ({ptype}) ---")

        # NOTE: reads from the ORIGINAL Output_ folder, writes to Output_*_v2
        src_dir = os.path.join(BASE, f"Output_{var_name}")
        sub_csv = os.path.join(src_dir, f"{var_name}_subdivisions.csv")
        cty_csv = os.path.join(src_dir, f"{var_name}_counties.csv")

        # v2 output goes to a NEW folder
        output_dir = os.path.join(BASE, f"Output_{var_name}_v2")
        charts_dir = os.path.join(output_dir, "charts")
        maps_dir   = os.path.join(output_dir, "maps")

        if not os.path.exists(sub_csv):
            print(f"  SKIPPED — not found: {sub_csv}")
            fail.append((var_name, "CSV not found"))
            continue

        os.makedirs(charts_dir, exist_ok=True)
        os.makedirs(maps_dir, exist_ok=True)

        try:
            df = pd.read_csv(sub_csv)
            df_counties = pd.read_csv(cty_csv)

            for d in [df, df_counties]:
                d['GEOID'] = d['GEOID'].astype(str)
            df['Geography'] = df['Geography'].astype(str).str.upper()
            df_counties['County'] = df_counties['County'].astype(str).str.upper()

            latest = df['year'].max()
            recent_df  = df[df['year'] == latest].copy()
            recent_cty = df_counties[df_counties['year'] == latest].copy()

            runner = pipeline_simple if ptype == "simple" else pipeline_multi
            runner.run(var_cfg, df, df_counties, recent_df, recent_cty,
                       gdf_sub.copy(), gdf_cty.copy(), output_dir, charts_dir, maps_dir)
            ok.append(var_name)

        except Exception as e:
            import traceback
            print(f"  ERROR: {e}")
            traceback.print_exc()
            fail.append((var_name, str(e)))

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"DONE — {len(ok)} ok, {len(fail)} failed ({elapsed:.1f}s)")
    if fail:
        print("\nFailed:")
        for n, r in fail:
            print(f"  x {n}: {r}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
