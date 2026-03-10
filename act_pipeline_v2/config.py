"""
ACT Dashboard Pipeline v2 — Variable Configuration
====================================================
Each variable is defined once. The pipeline reads this config to decide
which pipeline type to run, how to format axes/hovers, and what
categories/colors to use for multi-category variables.

v2 changes:
  - Added `acs_table` for source citations
  - Output folders use _v2 suffix
"""

# =====================================================================
# RACE / ETHNICITY shared categories
# =====================================================================
RACE_ORDER = [
    "White (Non-Hispanic)",
    "Black (Non-Hispanic)",
    "Hispanic or Latino (Any Race)",
    "Asian (Non-Hispanic)",
    "Two or More Races (Non-Hispanic)",
    "Native American (Non-Hispanic)",
    "Pacific Islander (Non-Hispanic)",
    "Other (Non-Hispanic)",
]

RACE_COLORS = {
    RACE_ORDER[0]: "#3B82F6",   # Blue
    RACE_ORDER[1]: "#F97316",   # Orange
    RACE_ORDER[2]: "#22C55E",   # Green
    RACE_ORDER[3]: "#EF4444",   # Red
    RACE_ORDER[4]: "#EC4899",   # Pink
    RACE_ORDER[5]: "#8B5CF6",   # Purple
    RACE_ORDER[6]: "#A16207",   # Amber-brown
    RACE_ORDER[7]: "#6B7280",   # Gray
}

RACE_SYMBOLS = {k: v for k, v in zip(
    RACE_ORDER,
    ['circle', 'square', 'diamond', 'cross', 'x', 'triangle-up', 'triangle-down', 'pentagon']
)}

# =====================================================================
# VARIABLE REGISTRY
# =====================================================================
VARIABLES = [
    # ==================================================================
    # SIMPLE PIPELINE — Percentages
    # ==================================================================
    {
        "name": "Percent_Below_Poverty_Last_12_MO",
        "title": "Poverty Rate (Last 12 Mo)",
        "pipeline": "simple",
        "data_type": "percent",
        "y_label": "Percent (%)",
        "hover_prefix": "Rate",
        "hover_format": ",.1f",
        "hover_moe_fmt": ",.1f",
        "hover_suffix": "%",
        "acs_table": "S1701_C03_001",
    },
    {
        "name": "Percent_Under_18_Below_Poverty_Last_12_MO",
        "title": "Under 18 Years Old Poverty Rate (Last 12 Mo)",
        "pipeline": "simple",
        "data_type": "percent",
        "y_label": "Percent (%)",
        "hover_prefix": "Rate",
        "hover_format": ",.1f",
        "hover_moe_fmt": ",.1f",
        "hover_suffix": "%",
        "acs_table": "S1701_C03_002",
    },
    {
        "name": "Percent_Households_Receiving_SNAP",
        "title": "Households Receiving SNAP (%)",
        "pipeline": "simple",
        "data_type": "percent",
        "y_label": "Percent (%)",
        "hover_prefix": "Rate",
        "hover_format": ",.1f",
        "hover_moe_fmt": ",.1f",
        "hover_suffix": "%",
        "acs_table": "S2201_C04_001",
    },
    {
        "name": "Percent_Households_With_Internet_Subscriptions",
        "title": "Households with Internet (%)",
        "pipeline": "simple",
        "data_type": "percent",
        "y_label": "Percent (%)",
        "hover_prefix": "Rate",
        "hover_format": ",.1f",
        "hover_moe_fmt": ",.1f",
        "hover_suffix": "%",
        "acs_table": "S2801_C02_012",
    },
    {
        "name": "Percent_Housing_Units_Vacant",
        "title": "Vacant Housing Units (%)",
        "pipeline": "simple",
        "data_type": "percent",
        "y_label": "Percent (%)",
        "hover_prefix": "Rate",
        "hover_format": ",.1f",
        "hover_moe_fmt": ",.1f",
        "hover_suffix": "%",
        "acs_table": "DP04_0003PE",
    },
    {
        "name": "Percent_Non_Institutionalized_Civilians_Uninsured",
        "title": "Uninsured Rate (%)",
        "pipeline": "simple",
        "data_type": "percent",
        "y_label": "Percent (%)",
        "hover_prefix": "Rate",
        "hover_format": ",.1f",
        "hover_moe_fmt": ",.1f",
        "hover_suffix": "%",
        "acs_table": "S2701_C05_001",
    },
    {
        "name": "Percent_Occupied_Homes_Owner_Occupied",
        "title": "Owner-Occupied Homes (%)",
        "pipeline": "simple",
        "data_type": "percent",
        "y_label": "Percent (%)",
        "hover_prefix": "Rate",
        "hover_format": ",.1f",
        "hover_moe_fmt": ",.1f",
        "hover_suffix": "%",
        "acs_table": "DP04_0046PE",
    },
    {
        "name": "Percent_Occupied_Houses_With_No_Vehicles",
        "title": "Homes with No Vehicle (%)",
        "pipeline": "simple",
        "data_type": "percent",
        "y_label": "Percent (%)",
        "hover_prefix": "Rate",
        "hover_format": ",.1f",
        "hover_moe_fmt": ",.1f",
        "hover_suffix": "%",
        "acs_table": "S2504_C02_027E",
    },
    # ==================================================================
    # SIMPLE PIPELINE — Currency
    # ==================================================================
    {
        "name": "Median_Household_Income",
        "title": "Median Household Income",
        "pipeline": "simple",
        "data_type": "currency",
        "y_label": "Median Household Income ($)",
        "hover_prefix": "Income",
        "hover_format": ",.0f",
        "hover_moe_fmt": ",.0f",
        "hover_suffix": "",
        "hover_dollar": True,
        "acs_table": "B19013_001",
    },
    {
        "name": "Median_Owner_Occupied_Housing_Value",
        "title": "Median Owner-Occupied Housing Value",
        "pipeline": "simple",
        "data_type": "currency",
        "y_label": "Median Housing Value ($)",
        "hover_prefix": "Value",
        "hover_format": ",.0f",
        "hover_moe_fmt": ",.0f",
        "hover_suffix": "",
        "hover_dollar": True,
        "acs_table": "DP04_0089E",
    },
    {
        "name": "Median_Rent",
        "title": "Median Gross Rent",
        "pipeline": "simple",
        "data_type": "currency",
        "y_label": "Median Gross Rent ($)",
        "hover_prefix": "Rent",
        "hover_format": ",.0f",
        "hover_moe_fmt": ",.0f",
        "hover_suffix": "",
        "hover_dollar": True,
        "acs_table": "DP04_0134",
    },
    # ==================================================================
    # SIMPLE PIPELINE — Count
    # ==================================================================
    {
        "name": "Total_Population",
        "title": "Total Population",
        "pipeline": "simple",
        "data_type": "count",
        "y_label": "Total Population",
        "hover_prefix": "Pop",
        "hover_format": ",.0f",
        "hover_moe_fmt": ",.0f",
        "hover_suffix": "",
        "acs_table": "B01003_001",
    },
    # ==================================================================
    # MULTI-CATEGORY — Race/Ethnicity Percentages
    # ==================================================================
    {
        "name": "Child_Poverty_Race_Ethnicity",
        "title": "Child Poverty by Race/Ethnicity",
        "pipeline": "multi",
        "data_type": "percent",
        "y_label": "Child Poverty Rate (%)",
        "hover_prefix": "Rate",
        "hover_format": ",.1f",
        "hover_moe_fmt": ",.1f",
        "hover_suffix": "%",
        "acs_table": "B17001",
        "order": RACE_ORDER,
        "color_map": RACE_COLORS,
        "symbol_map": RACE_SYMBOLS,
    },
    {
        "name": "Female_Poverty_Race_Ethnicity",
        "title": "Female Poverty by Race/Ethnicity",
        "pipeline": "multi",
        "data_type": "percent",
        "y_label": "Female Poverty Rate (%)",
        "hover_prefix": "Rate",
        "hover_format": ",.1f",
        "hover_moe_fmt": ",.1f",
        "hover_suffix": "%",
        "acs_table": "B17001",
        "order": RACE_ORDER,
        "color_map": RACE_COLORS,
        "symbol_map": RACE_SYMBOLS,
    },
    {
        "name": "Senior_Poverty_Race_Ethnicity",
        "title": "Senior Poverty by Race/Ethnicity",
        "pipeline": "multi",
        "data_type": "percent",
        "y_label": "Senior Poverty Rate (%)",
        "hover_prefix": "Rate",
        "hover_format": ",.1f",
        "hover_moe_fmt": ",.1f",
        "hover_suffix": "%",
        "acs_table": "B17001",
        "order": RACE_ORDER,
        "color_map": RACE_COLORS,
        "symbol_map": RACE_SYMBOLS,
    },
    {
        "name": "Homeownership_Race_Ethnicity_Distribution",
        "title": "Homeownership by Race/Ethnicity",
        "pipeline": "multi",
        "data_type": "percent",
        "y_label": "Homeownership Rate (%)",
        "hover_prefix": "Rate",
        "hover_format": ",.1f",
        "hover_moe_fmt": ",.1f",
        "hover_suffix": "%",
        "acs_table": "B25003",
        "order": RACE_ORDER,
        "color_map": RACE_COLORS,
        "symbol_map": RACE_SYMBOLS,
    },
    {
        "name": "Race_Ethnicity_Distribution",
        "title": "Race/Ethnicity Distribution",
        "pipeline": "multi",
        "data_type": "percent",
        "y_label": "Percent of Population (%)",
        "hover_prefix": "Rate",
        "hover_format": ",.1f",
        "hover_moe_fmt": ",.1f",
        "hover_suffix": "%",
        "acs_table": "B03002",
        "order": RACE_ORDER,
        "color_map": RACE_COLORS,
        "symbol_map": RACE_SYMBOLS,
    },
    # ==================================================================
    # MULTI-CATEGORY — Race/Ethnicity Currency
    # ==================================================================
    {
        "name": "Median_Income_Race_Ethnicity",
        "title": "Median Income by Race/Ethnicity",
        "pipeline": "multi",
        "data_type": "currency",
        "y_label": "Median Household Income ($)",
        "hover_prefix": "Income",
        "hover_format": ",.0f",
        "hover_moe_fmt": ",.0f",
        "hover_suffix": "",
        "hover_dollar": True,
        "acs_table": "B19013",
        "order": RACE_ORDER,
        "color_map": RACE_COLORS,
        "symbol_map": RACE_SYMBOLS,
    },
    # ==================================================================
    # MULTI-CATEGORY — Distributions
    # ==================================================================
    {
        "name": "Age_Distribution",
        "title": "Population by Age Group",
        "pipeline": "multi",
        "data_type": "percent",
        "y_label": "Percent of Population (%)",
        "hover_prefix": "Rate",
        "hover_format": ",.1f",
        "hover_moe_fmt": ",.1f",
        "hover_suffix": "%",
        "acs_table": "S0101",
        "order": [
            "Under 5 Years", "5 to 9 Years", "10 to 14 Years",
            "15 to 19 Years", "20 to 24 Years", "25 to 29 Years",
            "30 to 34 Years", "35 to 39 Years", "40 to 44 Years",
            "45 to 49 Years", "50 to 54 Years", "55 to 59 Years",
            "60 to 64 Years", "65 to 69 Years", "70 to 74 Years",
            "75 to 79 Years", "80 to 84 Years", "85 Years and Over",
        ],
        "color_map": {
            "Under 5 Years": "#3B82F6", "5 to 9 Years": "#60A5FA",
            "10 to 14 Years": "#F97316", "15 to 19 Years": "#FB923C",
            "20 to 24 Years": "#22C55E", "25 to 29 Years": "#4ADE80",
            "30 to 34 Years": "#EF4444", "35 to 39 Years": "#F87171",
            "40 to 44 Years": "#8B5CF6", "45 to 49 Years": "#A78BFA",
            "50 to 54 Years": "#EC4899", "55 to 59 Years": "#F472B6",
            "60 to 64 Years": "#06B6D4", "65 to 69 Years": "#22D3EE",
            "70 to 74 Years": "#A16207", "75 to 79 Years": "#CA8A04",
            "80 to 84 Years": "#6B7280", "85 Years and Over": "#9CA3AF",
        },
        "symbol_map": {k: v for k, v in zip(
            ["Under 5 Years", "5 to 9 Years", "10 to 14 Years",
             "15 to 19 Years", "20 to 24 Years", "25 to 29 Years",
             "30 to 34 Years", "35 to 39 Years", "40 to 44 Years",
             "45 to 49 Years", "50 to 54 Years", "55 to 59 Years",
             "60 to 64 Years", "65 to 69 Years", "70 to 74 Years",
             "75 to 79 Years", "80 to 84 Years", "85 Years and Over"],
            ['circle', 'square', 'diamond', 'cross', 'x', 'triangle-up',
             'triangle-down', 'pentagon', 'hexagram', 'star', 'circle',
             'square', 'diamond', 'cross', 'x', 'triangle-up',
             'triangle-down', 'pentagon']
        )},
    },
    {
        "name": "Commute_Time_Distribution",
        "title": "Commute Time Distribution",
        "pipeline": "multi",
        "data_type": "percent",
        "y_label": "% of Commuters",
        "hover_prefix": "Rate",
        "hover_format": ",.1f",
        "hover_moe_fmt": ",.1f",
        "hover_suffix": "%",
        "acs_table": "B08303",
        "order": [
            "Less than 5 min", "5 to 9 min", "10 to 14 min", "15 to 19 min",
            "20 to 24 min", "25 to 29 min", "30 to 34 min", "35 to 39 min",
            "40 to 44 min", "45 to 59 min", "60 to 89 min", "90 or more min",
        ],
        "color_map": {
            "Less than 5 min": "#3B82F6", "5 to 9 min": "#F97316",
            "10 to 14 min": "#22C55E", "15 to 19 min": "#EF4444",
            "20 to 24 min": "#8B5CF6", "25 to 29 min": "#A16207",
            "30 to 34 min": "#EC4899", "35 to 39 min": "#6B7280",
            "40 to 44 min": "#84CC16", "45 to 59 min": "#06B6D4",
            "60 to 89 min": "#93C5FD", "90 or more min": "#FDBA74",
        },
        "symbol_map": {},
    },
    {
        "name": "Rent_Burden_Distribution",
        "title": "Rent Burden Distribution",
        "pipeline": "multi",
        "data_type": "percent",
        "y_label": "% of Renters",
        "hover_prefix": "Rate",
        "hover_format": ",.1f",
        "hover_moe_fmt": ",.1f",
        "hover_suffix": "%",
        "acs_table": "B25070",
        "order": [
            "Not Burdened", "Rent Burdened",
            "Severely Rent Burdened", "Not Computed",
        ],
        "color_map": {
            "Not Burdened": "#16A34A",
            "Rent Burdened": "#F97316",
            "Severely Rent Burdened": "#DC2626",
            "Not Computed": "#9CA3AF",
        },
        "symbol_map": {
            "Not Burdened": "circle",
            "Rent Burdened": "diamond",
            "Severely Rent Burdened": "cross",
            "Not Computed": "square",
        },
    },
    {
        "name": "Transportation_Mode_Distribution",
        "title": "Transportation by Mode",
        "pipeline": "multi",
        "data_type": "percent",
        "y_label": "% of Workers",
        "hover_prefix": "Rate",
        "hover_format": ",.1f",
        "hover_moe_fmt": ",.1f",
        "hover_suffix": "%",
        "acs_table": "B08301",
        "order": [
            "Drove Alone", "Carpooled", "Public Transportation",
            "Worked from Home", "Walked", "Bicycle",
            "Taxi, Motorcycle, or Other",
        ],
        "color_map": {
            "Drove Alone": "#3B82F6", "Carpooled": "#F97316",
            "Public Transportation": "#22C55E", "Worked from Home": "#8B5CF6",
            "Walked": "#EF4444", "Bicycle": "#06B6D4",
            "Taxi, Motorcycle, or Other": "#6B7280",
        },
        "symbol_map": {k: v for k, v in zip(
            ["Drove Alone", "Carpooled", "Public Transportation",
             "Worked from Home", "Walked", "Bicycle",
             "Taxi, Motorcycle, or Other"],
            ['circle', 'square', 'diamond', 'cross', 'x', 'triangle-up', 'triangle-down']
        )},
    },
]

# Quick lookup by name
VARIABLE_MAP = {v["name"]: v for v in VARIABLES}