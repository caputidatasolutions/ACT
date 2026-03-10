# ACT Dashboard Pipeline v2 — Setup & Run Guide

## What This Does

This pipeline replaces your 22 Jupyter notebooks with **4 Python files** that generate all your HTML dashboards (bar charts, line charts, maps) for every ACS variable. Outputs go to `Output_<name>_v2/` folders so **your existing work is never touched**.

### v2 Improvements
- **Refreshed chart styling**: rounded bar corners, dotted gridlines, white-outlined markers, better spacing
- **Source citations**: Every chart and map shows `Source: U.S. Census Bureau, ACS 5-Year Estimates, Table <ID> (<years>)`
- **Modern dashboard headers**: cleaner fonts, polished dropdowns with hover/focus states
- **Refined color palette**: deeper primary blue, softer error bars, improved map color scale

---

## Step-by-Step Setup

### Step 1: Download the Pipeline Files

Download these 4 files from Claude and save them together in a **single folder**:

```
C:\Users\camer\Desktop\ACT\act_pipeline_v2\
├── run_all.py
├── config.py
├── utils.py
├── pipeline_simple.py
└── pipeline_multi.py
```

> **Important**: All 5 files must be in the **same folder**. The scripts import from each other.

### Step 2: Open VS Code

1. Open **Visual Studio Code**
2. Go to **File → Open Folder**
3. Navigate to `C:\Users\camer\Desktop\ACT\act_pipeline_v2` and click **Select Folder**
4. You should see all 5 `.py` files in the VS Code sidebar

### Step 3: Open the Terminal in VS Code

1. Go to **Terminal → New Terminal** (or press `` Ctrl+` ``)
2. A terminal panel opens at the bottom of VS Code
3. Make sure you're in the right folder. The prompt should show something like:

```
PS C:\Users\camer\Desktop\ACT\act_pipeline_v2>
```

If not, type:
```
cd C:\Users\camer\Desktop\ACT\act_pipeline_v2
```

### Step 4: Check Your Python Environment

Make sure the packages you already use are available:

```
python --version
```

You should see Python 3.x. If `python` doesn't work, try `python3` or `py`.

Your notebooks already use these packages, so they should be installed:
```
pip install pandas numpy geopandas plotly
```

### Step 5: Run the Pipeline

**Process ALL 22 variables at once:**
```
python run_all.py
```

**Process just one variable (to test first):**
```
python run_all.py --only Median_Rent
```

**Process a few specific ones:**
```
python run_all.py --only "Median_Rent,Total_Population,Child_Poverty_Race_Ethnicity"
```

**If your ACT folder is somewhere else:**
```
python run_all.py --base-path "D:\Projects\ACT"
```

### Step 6: Check the Output

After it runs, you'll see new folders alongside your existing ones:

```
C:\Users\camer\Desktop\ACT\
├── Output_Median_Rent\          ← your EXISTING work (untouched)
├── Output_Median_Rent_v2\       ← NEW v2 output
│   ├── bar_final_median_rent.html
│   ├── line_final_median_rent.html
│   ├── map_final_median_rent.html
│   ├── charts\
│   │   ├── bar_county_median_rent.html
│   │   ├── line_county_median_rent.html
│   │   └── ...
│   └── maps\
│       ├── map_county_Median_Rent_desktop.html
│       └── ...
├── Output_Total_Population\     ← existing
├── Output_Total_Population_v2\  ← new
└── ...
```

Open any `bar_final_*.html`, `line_final_*.html`, or `map_final_*.html` in a browser to preview.

### Step 7: Update Your Website Iframes

Once you're happy with the v2 output, update your website's iframe `src` paths to point to the `_v2` folders. The file names inside are identical to your current structure, so you just need to change the folder name.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'geopandas'` | Run `pip install geopandas` in the terminal |
| `FileNotFoundError: CSV not found` | The R script hasn't been run for that variable yet. The pipeline reads from your existing `Output_<name>/` folders |
| `python` command not found | Try `py` or `python3` instead. Or check that Python is in your PATH |
| Shapes take a long time | First run simplifies shapes and caches them. Subsequent runs load the cache instantly |
| Want to re-run a variable | Just run it again — the _v2 folder gets overwritten (not your originals) |

---

## Adding a New Variable Later

1. Open `config.py`
2. Add a new dict to the `VARIABLES` list (copy an existing one as a template)
3. Make sure the `name` matches your R output folder name
4. Run `python run_all.py --only Your_New_Variable_Name`

---

## File Reference

| File | Purpose |
|---|---|
| `run_all.py` | Main entry point. Run this from the terminal |
| `config.py` | All 22 variable definitions: names, types, ACS table IDs, categories, colors |
| `utils.py` | Shared styling, axis calculators, source annotations, HTML templates |
| `pipeline_simple.py` | Generates charts/maps for single-estimate variables (12 variables) |
| `pipeline_multi.py` | Generates charts/maps for multi-category variables (10 variables) |
