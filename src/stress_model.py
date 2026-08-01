"""
stress_model.py

Core stress model calculation engine.
Implements all formulas per calculation_instructions.md.
"""

import numpy as np
import pandas as pd


RATING_ORDER = {
    "Aaa/AAA": 15,
    "Aa2/AA": 14,
    "A1/A+": 13,
    "A2/A": 12,
    "A3/A-": 11,
    "Baa2/BBB": 10,
    "Ba1/BB+": 9,
    "Ba2/BB": 8,
    "B1/B+": 7,
    "B2/B": 6,
    "B3/B-": 5,
    "Caa/CCC": 4,
    "Ca2/CC": 3,
    "C2/C": 2,
    "D2/D": 1,
}

RATING_BANDS = [
    ("Aaa/AAA", 12.50, float("inf")),
    ("Aa2/AA", 9.50, 12.50),
    ("A1/A+", 7.50, 9.50),
    ("A2/A", 6.00, 7.50),
    ("A3/A-", 4.50, 6.00),
    ("Baa2/BBB", 4.00, 4.50),
    ("Ba1/BB+", 3.50, 4.00),
    ("Ba2/BB", 3.00, 3.50),
    ("B1/B+", 2.50, 3.00),
    ("B2/B", 2.00, 2.50),
    ("B3/B-", 1.50, 2.00),
    ("Caa/CCC", 1.25, 1.50),
    ("Ca2/CC", 0.80, 1.25),
    ("C2/C", 0.50, 0.80),
    ("D2/D", float("-inf"), 0.50),
]


def map_icr_to_rating(icr_value: float) -> str:
    """
    Formula 20: Map Stressed_ICR to synthetic rating using ICR bands.
    Bands ordered highest to lowest; first match wins.
    """
    if pd.isna(icr_value):
        return None
    
    for label, low, high in RATING_BANDS:
        if low <= icr_value < high:
            return label
    
    return None


def build_stress_model(
    refinancing_baseline: pd.DataFrame,
    credit_profile: pd.DataFrame,
    sector_master: pd.DataFrame,
    stress_parameters: pd.DataFrame,
) -> pd.DataFrame:
    """
    Execute complete stress model pipeline.
    
    Merges baseline refinancing exposure with credit profiles, sector data,
    and stress parameters, then applies all stress calculations in order.
    
    Returns full calculated model with all intermediate and final metrics.
    """
    
    # ── Merge datasets ────────────────────────────────────────────────────────
    model = refinancing_baseline.copy()
    
    credit_cols = [
        "Sector",
        "Avg_Cost_of_Debt",
        "Default_Spread",
        "Synthetic_Rating",
        "ICR_Low",
        "ICR_High",
        "ICR_Mid"
    ]
    model = model.merge(
        credit_profile[credit_cols],
        on="Sector",
        how="left",
        suffixes=("_x", "_y")
    )
    
    master_cols = [
        "Sector",
        "Total_Debt_M",
        "Total_Interest_Expense_M"
    ]
    model = model.merge(
        sector_master[master_cols],
        on="Sector",
        how="left"
    )
    
    model = model.merge(
        stress_parameters[
            [
                "Year",
                "Base_Rate_Shock_bp",
                "Credit_Spread_Shock_bp",
                "EBITDA_Shock_Pct"
            ]
        ],
        on="Year",
        how="left"
    )
    
    # ── Ensure sort order for cumulative calculations ─────────────────────────
    model = model.sort_values(
        ["Sector", "Year"]
    ).reset_index(drop=True)
    
    # ── Formula 1: Year_Specific_Shock ────────────────────────────────────────
    model["Year_Specific_Shock"] = (
        model["Base_Rate_Shock_bp"]
        +
        model["Credit_Spread_Shock_bp"]
    ) / 10_000
    
    # ── Formula 2: Refinancing_Cost ───────────────────────────────────────────
    model["Refinancing_Cost"] = (
        model["Avg_Cost_of_Debt"]
        +
        model["Year_Specific_Shock"]
    )
    
    # ── Formula 3: Additional_Interest_Expense ────────────────────────────────
    model["Additional_Interest_Expense"] = (
        model["Debt_Maturing_USD_Bn"]
        *
        (
            model["Refinancing_Cost"]
            -
            model["Avg_Cost_of_Debt"]
        )
    )
    
    # ── Formula 4: Cumulative_Interest_Burden ─────────────────────────────────
    model["Cumulative_Interest_Burden"] = model.groupby(
        "Sector"
    )["Additional_Interest_Expense"].cumsum()
    
    # ── Formula 5: Implied_EBITDA_M ───────────────────────────────────────────
    model["Implied_EBITDA_M"] = (
        model["ICR_Mid"]
        *
        model["Total_Interest_Expense_M"]
    )
    
    # ── Formula 6: Stressed_EBITDA_M ──────────────────────────────────────────
    model["Stressed_EBITDA_M"] = (
        model["Implied_EBITDA_M"]
        *
        (
            1
            +
            model["EBITDA_Shock_Pct"] / 100
        )
    )
    
    # ── Formula 7: Baseline_Interest_Expense_M ────────────────────────────────
    model["Baseline_Interest_Expense_M"] = model[
        "Total_Interest_Expense_M"
    ]
    
    # ── Formula 8: Stressed_Interest_Expense_M ────────────────────────────────
    model["Stressed_Interest_Expense_M"] = (
        model["Total_Interest_Expense_M"]
        +
        model["Cumulative_Interest_Burden"]
    )
    
    # ── Formula 9: Stressed_ICR ──────────────────────────────────────────────
    model["Stressed_ICR"] = np.where(
        model["Stressed_Interest_Expense_M"] == 0,
        np.nan,
        model["Stressed_EBITDA_M"]
        /
        model["Stressed_Interest_Expense_M"]
    )
    
    # ── Formula 10: Refinancing_Pct ───────────────────────────────────────────
    model["Refinancing_Pct"] = np.where(
        model["Total_Debt_M"] == 0,
        np.nan,
        (
            model["Debt_Maturing_USD_Bn"]
            /
            (model["Total_Debt_M"] / 1000)
        ) * 100
    )
    
    # ── Formula 11: Cumulative_Refinancing_Pct ───────────────────────────────
    model["Cumulative_Refinancing_Pct"] = model.groupby(
        "Sector"
    )["Refinancing_Pct"].cumsum()
    
    # ── Formula 12: Interest_Expense_Increase_Pct ─────────────────────────────
    model["Interest_Expense_Increase_Pct"] = np.where(
        model["Baseline_Interest_Expense_M"] == 0,
        np.nan,
        (
            (
                model["Stressed_Interest_Expense_M"]
                -
                model["Baseline_Interest_Expense_M"]
            )
            /
            model["Baseline_Interest_Expense_M"]
        ) * 100
    )
    
    # ── Formula 13: ICR_Decline_Pct ───────────────────────────────────────────
    model["ICR_Decline_Pct"] = np.where(
        model["ICR_Mid"] == 0,
        np.nan,
        (
            (
                model["ICR_Mid"]
                -
                model["Stressed_ICR"]
            )
            /
            model["ICR_Mid"]
        ) * 100
    )
    
    # ── Formula 14 & 15: Distance metrics ─────────────────────────────────────
    model["Distance_To_Downgrade_After_Stress"] = (
        model["Stressed_ICR"]
        -
        model["ICR_Low"]
    )
    
    model["Distance_To_Upgrade_After_Stress"] = (
        model["ICR_High"]
        -
        model["Stressed_ICR"]
    )
    
    # ── Formula 16 & 17: Threshold flags ──────────────────────────────────────
    model["Downgrade_Flag"] = (
        model["Stressed_ICR"]
        
        model["ICR_Low"]
    )
    
    model["Upgrade_Flag"] = (
        model["Stressed_ICR"]
        >
        model["ICR_High"]
    )
    
    # ── Formula 18: Threshold_Status ──────────────────────────────────────────
    model["Threshold_Status"] = "Within Band"
    model.loc[model["Downgrade_Flag"], "Threshold_Status"] = "Downgrade"
    model.loc[model["Upgrade_Flag"], "Threshold_Status"] = "Upgrade"
    
    # ── Formula 19: Current_Rating_Score ──────────────────────────────────────
    model["Current_Rating_Score"] = (
        model["Synthetic_Rating_y"]
        .map(RATING_ORDER)
    )
    
    # ── Formula 20: Stressed_Rating ───────────────────────────────────────────
    model["Stressed_Rating"] = (
        model["Stressed_ICR"]
        .apply(map_icr_to_rating)
    )
    
    # ── Formula 21: Stressed_Rating_Score ─────────────────────────────────────
    model["Stressed_Rating_Score"] = (
        model["Stressed_Rating"]
        .map(RATING_ORDER)
    )
    
    # ── Formula 22: Notches_Changed ───────────────────────────────────────────
    model["Notches_Changed"] = (
        model["Stressed_Rating_Score"]
        -
        model["Current_Rating_Score"]
    )
    
    # ── Formula 23: Fallen_Angel_Flag ────────────────────────────────────────
    model["Fallen_Angel_Flag"] = (
        (model["Current_Rating_Score"] >= 10)
        &
        (model["Stressed_Rating_Score"] < 10)
    )
    
    return model


def build_stress_results(
    model: pd.DataFrame,
) -> pd.DataFrame:
    """
    Extract key outputs for dashboard and reporting.
    """
    
    results = model[
        [
            "Sector",
            "Year",
            "Synthetic_Rating_y",
            "Stressed_Rating",
            "Notches_Changed",
            "ICR_Mid",
            "Stressed_ICR",
            "Refinancing_Pct",
            "Cumulative_Refinancing_Pct",
            "Interest_Expense_Increase_Pct"
        ]
    ].copy()
    
    results = results.sort_values(
        ["Sector", "Year"]
    ).reset_index(drop=True)
    
    return results


def build_stress_summary(
    model: pd.DataFrame,
) -> pd.DataFrame:
    """
    Final-year summary: one row per sector showing peak stress impact.
    """
    
    summary = (
        model
        .sort_values(["Sector", "Year"])
        .groupby("Sector")
        .tail(1)
        .copy()
    )
    
    return summary


def build_dashboard_input(
    model: pd.DataFrame,
) -> pd.DataFrame:
    """
    Minimal dataset for dashboard ingestion.
    Columns match dashboard_input.csv specification exactly.
    """
    
    dashboard = model[
        [
            "Sector",
            "Year",
            "Synthetic_Rating_y",
            "Stressed_Rating",
            "Notches_Changed",
            "Fallen_Angel_Flag",
            "ICR_Mid",
            "Stressed_ICR",
            "Interest_Expense_Increase_Pct",
            "Refinancing_Pct",
            "Cumulative_Refinancing_Pct"
        ]
    ].copy()
    
    dashboard = dashboard.sort_values(
        ["Sector", "Year"]
    ).reset_index(drop=True)
    
    return dashboard
