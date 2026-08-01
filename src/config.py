from pathlib import Path


# ==========================================================
# Repository Paths
# ==========================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT_DIR / "data"

RAW_DATA_DIR = DATA_DIR / "raw"

INTERMEDIATE_DATA_DIR = DATA_DIR / "intermediate"

PROCESSED_DATA_DIR = DATA_DIR / "processed"

FINAL_DATA_DIR = DATA_DIR / "final"

DASHBOARD_DIR = ROOT_DIR / "dashboard"

DOCS_DIR = ROOT_DIR / "docs"

NOTEBOOKS_DIR = ROOT_DIR / "notebooks"


# ==========================================================
# Raw Data Files
# ==========================================================

SECTOR_DEBT_FILE = (
    RAW_DATA_DIR / "sector_debt_clean.xlsx"
)

SECTOR_MARGIN_FILE = (
    RAW_DATA_DIR / "sector_margins_clean.xlsx"
)

SECTOR_WACC_FILE = (
    RAW_DATA_DIR / "sector_wacc_clean.xlsx"
)

SYNTHETIC_RATING_FILE = (
    RAW_DATA_DIR / "synthetic_rating_lookup.xlsx"
)

FRED_MASTER_FILE = (
    RAW_DATA_DIR / "fred_master.csv"
)


# ==========================================================
# Processed Data Files
# ==========================================================

SECTOR_MAPPING_FILE = (
    PROCESSED_DATA_DIR / "sector_mapping.csv"
)

SECTOR_MASTER_FILE = (
    PROCESSED_DATA_DIR / "sector_master.csv"
)

SECTOR_CREDIT_PROFILE_FILE = (
    PROCESSED_DATA_DIR / "sector_credit_profile.csv"
)

SECTOR_THRESHOLD_PROFILE_FILE = (
    PROCESSED_DATA_DIR / "sector_threshold_profile.csv"
)

SECTOR_MATURITY_ALLOCATION_FILE = (
    PROCESSED_DATA_DIR /
    "sector_maturity_allocation_by_year.csv"
)

SECTOR_REFINANCING_BASELINE_FILE = (
    PROCESSED_DATA_DIR /
    "sector_refinancing_baseline.csv"
)

STRESS_PARAMETER_FILE = (
    PROCESSED_DATA_DIR /
    "stress_parameter_template.csv"
)

SECTOR_STRESS_MODEL_FILE = (
    PROCESSED_DATA_DIR /
    "sector_stress_model.csv"
)

SECTOR_STRESS_RESULTS_FILE = (
    PROCESSED_DATA_DIR /
    "sector_stress_results.csv"
)

SECTOR_STRESS_SUMMARY_FILE = (
    PROCESSED_DATA_DIR /
    "sector_stress_summary.csv"
)

DASHBOARD_INPUT_FILE = (
    PROCESSED_DATA_DIR /
    "dashboard_input.csv"
)


# ==========================================================
# Final Data Files
# ==========================================================

GLOBAL_MATURITY_WALL_FILE = (
    FINAL_DATA_DIR /
    "global_maturity_wall.csv"
)

REGIONAL_MATURITY_WALL_FILE = (
    FINAL_DATA_DIR /
    "regional_maturity_wall.csv"
)

GLOBAL_RATING_WALL_FILE = (
    FINAL_DATA_DIR /
    "global_rating_wall.csv"
)

REGIONAL_RATING_WALL_FILE = (
    FINAL_DATA_DIR /
    "regional_rating_wall.csv"
)


# ==========================================================
# Financial Constants
# ==========================================================

RISK_FREE_RATE = 0.0395


# ==========================================================
# Rating Scores
# ==========================================================

RATING_SCORE = {

    "D2/D": 1,

    "C2/C": 2,

    "Ca2/CC": 3,

    "Caa/CCC": 4,

    "B3/B-": 5,

    "B2/B": 6,

    "B1/B+": 7,

    "Ba2/BB": 8,

    "Ba1/BB+": 9,

    "Baa2/BBB": 10,

    "A3/A-": 11,

    "A2/A": 12,

    "A1/A+": 13,

    "Aa2/AA": 14,

    "Aaa/AAA": 15
}


# ==========================================================
# Default Scenario
# ==========================================================

DEFAULT_BASE_RATE_SHOCK_BP = 100

DEFAULT_CREDIT_SPREAD_SHOCK_BP = 150

DEFAULT_EBITDA_SHOCK_PCT = -10


# ==========================================================
# Project Years
# ==========================================================

PROJECT_YEARS = [

    2026,
    2027,
    2028,
    2029

]


# ==========================================================
# Sector List
# ==========================================================

PROJECT_SECTORS = [

    "TECH",

    "HC",

    "MEDIA",

    "ENERGY",

    "CONS",

    "IND",

    "CHEM",

    "FOOD"

]


# ==========================================================
# Required Processed Files
# ==========================================================

REQUIRED_PROCESSED_FILES = [

    SECTOR_MAPPING_FILE,

    SECTOR_MASTER_FILE,

    SECTOR_CREDIT_PROFILE_FILE,

    SECTOR_THRESHOLD_PROFILE_FILE,

    SECTOR_MATURITY_ALLOCATION_FILE,

    SECTOR_REFINANCING_BASELINE_FILE,

    STRESS_PARAMETER_FILE

]


# ==========================================================
# Dashboard Files
# ==========================================================

DASHBOARD_REQUIRED_FILES = [

    DASHBOARD_INPUT_FILE,

    SECTOR_STRESS_RESULTS_FILE,

    SECTOR_STRESS_SUMMARY_FILE

]
