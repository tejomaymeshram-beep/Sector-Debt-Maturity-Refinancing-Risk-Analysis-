"""
DMRRA — Debt Maturity and Refinancing Risk Analysis
Streamlit Dashboard

Interactive stress scenario modelling with real-time parameter adjustment.
"""

import os
import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# 1. CONFIGURATION & CONSTANTS
# ──────────────────────────────────────────────────────────────────────────────

APP_TITLE = "Debt Maturity and Refinancing Risk Analysis"
APP_SUBTITLE = "Stress-scenario modelling of refinancing exposure across sectors"

# Determine data directory — assumes data/processed/ exists relative to repo root
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
DATA_DIR = REPO_ROOT / "data" / "processed"

REQUIRED_FILES = {
    "sector_refinancing_baseline.csv": [
        "Sector", "Year", "Allocation_Pct", "Total_Debt_USD_Bn",
        "Debt_Maturing_USD_Bn", "Synthetic_Rating", "Rating_Score", "ICR_Mid"
    ],
    "sector_credit_profile.csv": [
        "Sector", "Avg_Cost_of_Debt", "Default_Spread", "Synthetic_Rating",
        "ICR_Low", "ICR_High", "ICR_Mid", "Rating_Score"
    ],
    "sector_master.csv": [
        "Sector", "Total_Debt_M", "Total_Interest_Expense_M"
    ],
    "sector_maturity_allocation_by_year.csv": ["Sector"],
    "stress_parameter_template.csv": [
        "Year", "Base_Rate_Shock_bp", "Credit_Spread_Shock_bp", "EBITDA_Shock_Pct"
    ],
}

RATING_ORDER = {
    "D2/D": 1, "C2/C": 2, "Ca2/CC": 3, "Caa/CCC": 4, "B3/B-": 5,
    "B2/B": 6, "B1/B+": 7, "Ba2/BB": 8, "Ba1/BB+": 9, "Baa2/BBB": 10,
    "A3/A-": 11, "A2/A": 12, "A1/A+": 13, "Aa2/AA": 14, "Aaa/AAA": 15,
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

COLOUR_NEUTRAL = "#4a90d9"
COLOUR_STRESS = "#c0392b"
COLOUR_IMPROVE = "#27ae60"
COLOUR_WARNING = "#d68910"
COLOUR_GREY = "#95a5a6"


# ──────────────────────────────────────────────────────────────────────────────
# 2. FILE VALIDATION & LOADING
# ──────────────────────────────────────────────────────────────────────────────

def validate_data_directory(data_dir: Path) -> list[str]:
    """
    Validate that all required CSV files exist and have required columns.
    Returns list of error messages; empty list = all valid.
    """
    errors = []
    
    if not data_dir.exists():
        errors.append(f"Data directory not found: {data_dir}")
        return errors
    
    for filename, required_cols in REQUIRED_FILES.items():
        filepath = data_dir / filename
        
        if not filepath.exists():
            errors.append(f"Missing: {filename}")
            continue
        
        try:
            df = pd.read_csv(filepath, nrows=1)
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                errors.append(f"{filename}: missing columns {missing}")
        except Exception as e:
            errors.append(f"{filename}: cannot read ({e})")
    
    return errors


@st.cache_data(show_spinner=False)
def load_source_data(data_dir: Path) -> dict[str, pd.DataFrame]:
    """
    Load all source CSV files into memory.
    Cached after first load for performance.
    """
    raw = {}
    
    for filename in REQUIRED_FILES.keys():
        filepath = data_dir / filename
        df = pd.read_csv(filepath)
        
        # Coerce Year to integer where column exists
        if "Year" in df.columns:
            df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
        
        # Handle year columns in allocation table (may be strings like "2026")
        if filename == "sector_maturity_allocation_by_year.csv":
            year_cols = [c for c in df.columns if c != "Sector"]
            rename_map = {}
            for col in year_cols:
                try:
                    rename_map[col] = int(col)
                except (ValueError, TypeError):
                    pass
            if rename_map:
                df.rename(columns=rename_map, inplace=True)
        
        raw[filename] = df
    
    return raw


# ──────────────────────────────────────────────────────────────────────────────
# 3. STRESS MODEL CALCULATION
# ──────────────────────────────────────────────────────────────────────────────

def map_icr_to_rating(icr_value: float) -> str:
    """Map Stressed_ICR to rating label using RATING_BANDS."""
    if pd.isna(icr_value):
        return None
    for label, low, high in RATING_BANDS:
        if low <= icr_value < high:
            return label
    return None


def execute_stress_model(
    baseline: pd.DataFrame,
    credit: pd.DataFrame,
    master: pd.DataFrame,
    stress_params: pd.DataFrame,
) -> pd.DataFrame:
    """
    Execute complete stress model calculation.
    
    Implements all formulas from calculation_instructions.md.
    Returns full model dataframe with all stress metrics.
    """
    
    # ── Merge datasets ────────────────────────────────────────────────────────
    model = baseline.copy()
    
    credit_merge = credit[[
        "Sector", "Avg_Cost_of_Debt", "Default_Spread", "Synthetic_Rating",
        "ICR_Low", "ICR_High", "ICR_Mid", "Rating_Score"
    ]].copy()
    
    model = model.merge(
        credit_merge,
        on="Sector",
        how="left",
        suffixes=("_x", "_y")
    )
    
    master_merge = master[[
        "Sector", "Total_Debt_M", "Total_Interest_Expense_M"
    ]].copy()
    
    model = model.merge(master_merge, on="Sector", how="left")
    
    stress_merge = stress_params[[
        "Year", "Base_Rate_Shock_bp", "Credit_Spread_Shock_bp", "EBITDA_Shock_Pct"
    ]].copy()
    
    model = model.merge(stress_merge, on="Year", how="left")
    
    # Ensure sort order for cumulative calculations
    model = model.sort_values(["Sector", "Year"]).reset_index(drop=True)
    
    # ── Formula 1: Year_Specific_Shock ───────────────────────────────────────
    model["Year_Specific_Shock"] = (
        model["Base_Rate_Shock_bp"] + model["Credit_Spread_Shock_bp"]
    ) / 10_000
    
    # ── Formula 2: Refinancing_Cost ──────────────────────────────────────────
    model["Refinancing_Cost"] = (
        model["Avg_Cost_of_Debt"] + model["Year_Specific_Shock"]
    )
    
    # ── Formula 3: Additional_Interest_Expense ────────────────────────────────
    model["Additional_Interest_Expense"] = (
        model["Debt_Maturing_USD_Bn"]
        * (model["Refinancing_Cost"] - model["Avg_Cost_of_Debt"])
    )
    
    # ── Formula 4: Cumulative_Interest_Burden ─────────────────────────────────
    model["Cumulative_Interest_Burden"] = model.groupby(
        "Sector"
    )["Additional_Interest_Expense"].cumsum()
    
    # ── Formula 5: Implied_EBITDA_M ──────────────────────────────────────────
    model["Implied_EBITDA_M"] = (
        model["ICR_Mid_y"] * model["Total_Interest_Expense_M"]
    )
    
    # ── Formula 6: Stressed_EBITDA_M ─────────────────────────────────────────
    model["Stressed_EBITDA_M"] = (
        model["Implied_EBITDA_M"] * (1 + model["EBITDA_Shock_Pct"] / 100)
    )
    
    # ── Formula 7 & 8: Interest expense ──────────────────────────────────────
    model["Baseline_Interest_Expense_M"] = model["Total_Interest_Expense_M"]
    
    model["Stressed_Interest_Expense_M"] = (
        model["Total_Interest_Expense_M"] + model["Cumulative_Interest_Burden"]
    )
    
    # ── Formula 9: Stressed_ICR ──────────────────────────────────────────────
    model["Stressed_ICR"] = np.where(
        model["Stressed_Interest_Expense_M"] == 0,
        np.nan,
        model["Stressed_EBITDA_M"] / model["Stressed_Interest_Expense_M"],
    )
    
    # ── Formula 10: Refinancing_Pct ──────────────────────────────────────────
    model["Refinancing_Pct"] = np.where(
        model["Total_Debt_M"] == 0,
        np.nan,
        (model["Debt_Maturing_USD_Bn"] / (model["Total_Debt_M"] / 1000)) * 100,
    )
    
    # ── Formula 11: Cumulative_Refinancing_Pct ───────────────────────────────
    model["Cumulative_Refinancing_Pct"] = model.groupby(
        "Sector"
    )["Refinancing_Pct"].cumsum()
    
    # ── Formula 12: Interest_Expense_Increase_Pct ────────────────────────────
    model["Interest_Expense_Increase_Pct"] = np.where(
        model["Baseline_Interest_Expense_M"] == 0,
        np.nan,
        (
            (model["Stressed_Interest_Expense_M"] - model["Baseline_Interest_Expense_M"])
            / model["Baseline_Interest_Expense_M"]
        ) * 100,
    )
    
    # ── Formula 13: ICR_Decline_Pct ──────────────────────────────────────────
    model["ICR_Decline_Pct"] = np.where(
        model["ICR_Mid_y"] == 0,
        np.nan,
        ((model["ICR_Mid_y"] - model["Stressed_ICR"]) / model["ICR_Mid_y"]) * 100,
    )
    
    # ── Formula 14 & 15: Distance metrics ────────────────────────────────────
    model["Distance_To_Downgrade_After_Stress"] = (
        model["Stressed_ICR"] - model["ICR_Low"]
    )
    model["Distance_To_Upgrade_After_Stress"] = (
        model["ICR_High"] - model["Stressed_ICR"]
    )
    
    # ── Formula 16 & 17: Flags ───────────────────────────────────────────────
    model["Downgrade_Flag"] = model["Stressed_ICR"] < model["ICR_Low"]
    model["Upgrade_Flag"] = model["Stressed_ICR"] > model["ICR_High"]
    
    # ── Formula 18: Threshold_Status ─────────────────────────────────────────
    model["Threshold_Status"] = "Within Band"
    model.loc[model["Downgrade_Flag"], "Threshold_Status"] = "Downgrade"
    model.loc[model["Upgrade_Flag"], "Threshold_Status"] = "Upgrade"
    
    # ── Formula 19: Current_Rating_Score ─────────────────────────────────────
    model["Current_Rating_Score"] = model["Synthetic_Rating_y"].map(RATING_ORDER)
    
    # ── Formula 20: Stressed_Rating ──────────────────────────────────────────
    model["Stressed_Rating"] = model["Stressed_ICR"].apply(map_icr_to_rating)
    
    # ── Formula 21: Stressed_Rating_Score ────────────────────────────────────
    model["Stressed_Rating_Score"] = model["Stressed_Rating"].map(RATING_ORDER)
    
    # ── Formula 22: Notches_Changed ──────────────────────────────────────────
    model["Notches_Changed"] = (
        model["Stressed_Rating_Score"] - model["Current_Rating_Score"]
    )
    
    # ── Formula 23: Fallen_Angel_Flag ────────────────────────────────────────
    model["Fallen_Angel_Flag"] = (
        (model["Current_Rating_Score"] >= 10) & (model["Stressed_Rating_Score"] < 10)
    )
    
    return model


# ──────────────────────────────────────────────────────────────────────────────
# 4. CHART FUNCTIONS
# ──────────────────────────────────────────────────────────────────────────────

def chart_stressed_icr_by_year(df: pd.DataFrame, sectors: list[str]) -> go.Figure:
    """Line chart: Stressed ICR over years per sector."""
    plot_df = df[df["Sector"].isin(sectors)].copy()
    plot_df["Year_str"] = plot_df["Year"].astype(str)
    
    fig = go.Figure()
    for sector in sectors:
        sector_data = plot_df[plot_df["Sector"] == sector].sort_values("Year")
        fig.add_trace(go.Scatter(
            x=sector_data["Year_str"],
            y=sector_data["Stressed_ICR"],
            name=sector,
            mode="lines+markers",
            hovertemplate="Year: %{x}<br>Stressed ICR: %{y:.3f}x<extra></extra>",
        ))
    
    fig.update_layout(
        title="Stressed Interest Coverage Ratio by Year",
        xaxis_title="Year",
        yaxis_title="Stressed ICR (×)",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=500,
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(150,150,150,0.2)")
    return fig


def chart_notch_heatmap(df: pd.DataFrame) -> go.Figure:
    """Heatmap: Notches_Changed per Sector × Year."""
    pivot = df.pivot_table(
        index="Sector",
        columns="Year",
        values="Notches_Changed",
        aggfunc="first"
    )
    pivot.columns = [str(c) for c in pivot.columns]
    
    colorscale = [
        [0.0, "#c0392b"],   # Red for downgrades
        [0.5, "#ecf0f1"],   # White for no change
        [1.0, "#27ae60"],   # Green for upgrades
    ]
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=list(pivot.columns),
        y=list(pivot.index),
        colorscale=colorscale,
        zmid=0,
        text=pivot.values,
        texttemplate="%{text:.0f}",
        colorbar=dict(title="Notches"),
        hovertemplate="Sector: %{y}<br>Year: %{x}<br>Notches: %{z:.0f}<extra></extra>",
    ))
    
    fig.update_layout(
        title="Rating Notch Change Under Stress",
        xaxis_title="Year",
        yaxis_title="Sector",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=400,
    )
    return fig


def chart_distance_to_downgrade(df: pd.DataFrame, year: int) -> go.Figure:
    """Horizontal bar: Distance to downgrade threshold per sector."""
    year_df = df[df["Year"] == year].sort_values("Distance_To_Downgrade_After_Stress")
    
    colors = [
        COLOUR_STRESS if x < 0 else COLOUR_NEUTRAL
        for x in year_df["Distance_To_Downgrade_After_Stress"]
    ]
    
    fig = go.Figure(data=go.Bar(
        x=year_df["Distance_To_Downgrade_After_Stress"],
        y=year_df["Sector"],
        orientation="h",
        marker_color=colors,
        hovertemplate="Sector: %{y}<br>Distance: %{x:.3f}x<extra></extra>",
    ))
    
    fig.add_vline(
        x=0,
        line_dash="dash",
        line_color=COLOUR_STRESS,
        line_width=2,
    )
    
    fig.update_layout(
        title=f"Distance to Downgrade Threshold — Year {year}",
        xaxis_title="Stressed ICR − ICR Low (×)",
        yaxis_title="Sector",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=400,
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(150,150,150,0.2)")
    fig.update_yaxes(showgrid=False)
    return fig


def chart_cumulative_refinancing(df: pd.DataFrame, sectors: list[str]) -> go.Figure:
    """Bar chart: Cumulative refinancing exposure by year."""
    plot_df = df[df["Sector"].isin(sectors)].copy()
    plot_df["Year_str"] = plot_df["Year"].astype(str)
    
    fig = go.Figure()
    for sector in sectors:
        sector_data = plot_df[plot_df["Sector"] == sector].sort_values("Year")
        fig.add_trace(go.Bar(
            x=sector_data["Year_str"],
            y=sector_data["Cumulative_Refinancing_Pct"],
            name=sector,
            hovertemplate="Year: %{x}<br>Cumulative Refi: %{y:.2f}%<extra></extra>",
        ))
    
    fig.update_layout(
        title="Cumulative Refinancing Exposure (% of Total Debt)",
        xaxis_title="Year",
        yaxis_title="Cumulative Refinancing (%)",
        barmode="group",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=500,
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(150,150,150,0.2)")
    return fig


# ──────────────────────────────────────────────────────────────────────────────
# 5. TABLE BUILDERS
# ──────────────────────────────────────────────────────────────────────────────

def build_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """Build summary: one row per Sector showing key metrics."""
    summary = df.groupby("Sector").agg({
        "Year": "count",
        "Stressed_ICR": ["min", "mean", "max"],
        "Notches_Changed": "first",
        "Fallen_Angel_Flag": "any",
        "Interest_Expense_Increase_Pct": "max",
        "Cumulative_Refinancing_Pct": "max",
    }).reset_index()
    
    summary.columns = [
        "Sector", "Years", "Min_ICR", "Avg_ICR", "Max_ICR",
        "Notches", "Fallen_Angel", "Max_Interest_Δ(%)", "Max_Refi(%)"
    ]
    
    return summary


def build_migration_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Build transition matrix: Current Rating → Stressed Rating."""
    final_year = df[df["Year"] == df["Year"].max()].copy()
    
    transition = pd.crosstab(
        final_year["Synthetic_Rating_y"],
        final_year["Stressed_Rating"],
        margins=True,
        margins_name="Total"
    )
    
    return transition


# ──────────────────────────────────────────────────────────────────────────────
# 6. MAIN APPLICATION
# ──────────────────────────────────────────────────────────────────────────────

def main():
    """Main Streamlit application."""
    
    st.set_page_config(
        page_title=APP_TITLE,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # ── Header ────────────────────────────────────────────────────────────────
    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)
    st.divider()
    
    # ── Validate data directory ───────────────────────────────────────────────
    errors = validate_data_directory(DATA_DIR)
    if errors:
        st.error("**Data Validation Failed**")
        for err in errors:
            st.write(f"- {err}")
        st.write(f"\nExpected data directory: `{DATA_DIR}`")
        st.stop()
    
    # ── Load source data ──────────────────────────────────────────────────────
    try:
        raw = load_source_data(DATA_DIR)
    except Exception as e:
        st.error(f"Data loading failed: {e}")
        st.text(traceback.format_exc())
        st.stop()
    
    # ── Initialize session state for model caching ────────────────────────────
    if "model_cache" not in st.session_state:
        st.session_state.model_cache = None
        st.session_state.last_params = None
    
    # ── Sidebar: Stress Parameters ────────────────────────────────────────────
    st.sidebar.header("⚙️ Stress Parameters")
    
    stress_params = raw["stress_parameter_template.csv"].copy()
    edited_params = []
    
    for _, row in stress_params.iterrows():
        year = int(row["Year"])
        st.sidebar.markdown(f"**Year {year}**")
        
        base_rate = st.sidebar.number_input(
            f"Base Rate Shock (bp)",
            value=float(row["Base_Rate_Shock_bp"]),
            step=25.0,
            key=f"base_{year}",
        )
        
        credit_spread = st.sidebar.number_input(
            f"Credit Spread Shock (bp)",
            value=float(row["Credit_Spread_Shock_bp"]),
            step=25.0,
            key=f"credit_{year}",
        )
        
        ebitda_shock = st.sidebar.number_input(
            f"EBITDA Shock (%)",
            value=float(row["EBITDA_Shock_Pct"]),
            step=1.0,
            key=f"ebitda_{year}",
        )
        
        edited_params.append({
            "Year": year,
            "Base_Rate_Shock_bp": base_rate,
            "Credit_Spread_Shock_bp": credit_spread,
            "EBITDA_Shock_Pct": ebitda_shock,
        })
        
        st.sidebar.markdown("---")
    
    stress_params_edited = pd.DataFrame(edited_params)
    
    # ── Sidebar: Sector Filter ────────────────────────────────────────────────
    st.sidebar.header("🔍 Sector Filter")
    
    all_sectors = sorted(
        raw["sector_credit_profile.csv"]["Sector"].unique().tolist()
    )
    selected_sectors = st.sidebar.multiselect(
        "Select sectors to display",
        options=all_sectors,
        default=all_sectors,
    )
    
    if not selected_sectors:
        st.warning("Please select at least one sector.")
        st.stop()
    
    # ── Sidebar: Year Selection ───────────────────────────────────────────────
    st.sidebar.header("📅 Year Selection")
    
    all_years = sorted(stress_params_edited["Year"].unique().tolist())
    selected_year = st.sidebar.selectbox(
        "Year for single-year views",
        options=all_years,
        index=len(all_years) - 1,
    )
    
    # ── Execute Stress Model (with caching) ───────────────────────────────────
    st.sidebar.header("🔄 Model Status")
    
    # Create hash of current parameters to detect changes
    params_hash = hash(str(stress_params_edited.values))
    
    if (st.session_state.model_cache is None or 
        st.session_state.last_params != params_hash):
        
        with st.sidebar:
            with st.spinner("Calculating stress model..."):
                try:
                    model = execute_stress_model(
                        baseline=raw["sector_refinancing_baseline.csv"],
                        credit=raw["sector_credit_profile.csv"],
                        master=raw["sector_master.csv"],
                        stress_params=stress_params_edited,
                    )
                    
                    st.session_state.model_cache = model
                    st.session_state.last_params = params_hash
                    st.success("Model calculated ✓")
                    
                except Exception as e:
                    st.error(f"Model calculation failed: {e}")
                    st.text(traceback.format_exc())
                    st.stop()
    else:
        st.sidebar.info("Using cached model")
    
    model = st.session_state.model_cache
    filtered_model = model[model["Sector"].isin(selected_sectors)].copy()
    
    # ── Tab Layout ────────────────────────────────────────────────────────────
    (tab_overview, tab_icr, tab_refinancing, 
     tab_migration, tab_sector, tab_data) = st.tabs([
        "📊 Overview",
        "📈 ICR Analysis",
        "💰 Refinancing",
        "⚡ Rating Migration",
        "🔎 Sector Detail",
        "📋 Full Data",
    ])
    
    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1: OVERVIEW
    # ══════════════════════════════════════════════════════════════════════════
    with tab_overview:
        st.subheader("Scenario Summary")
        
        with st.expander("Active Stress Parameters", expanded=False):
            st.dataframe(
                stress_params_edited,
                use_container_width=True,
                hide_index=True,
            )
        
        # Key metrics
        year_data = filtered_model[filtered_model["Year"] == selected_year]
        
        n_downgrade = int(year_data["Downgrade_Flag"].sum())
        n_fallen = int(year_data["Fallen_Angel_Flag"].sum())
        n_upgrade = int(year_data["Upgrade_Flag"].sum())
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Downgrade Risk", n_downgrade, delta=None)
        col2.metric("Fallen Angels", n_fallen, delta=None)
        col3.metric("Upgrade Risk", n_upgrade, delta=None)
        col4.metric("Sectors Analyzed", len(selected_sectors), delta=None)
        
        st.divider()
        
        # Notch heatmap
        st.subheader("Rating Notch Change — All Sectors")
        st.plotly_chart(
            chart_notch_heatmap(filtered_model),
            use_container_width=True,
        )
        
        st.divider()
        
        # Distance to downgrade
        st.subheader(f"Distance to Downgrade — Year {selected_year}")
        st.plotly_chart(
            chart_distance_to_downgrade(year_data, selected_year),
            use_container_width=True,
        )
    
    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2: ICR ANALYSIS
    # ══════════════════════════════════════════════════════════════════════════
    with tab_icr:
        st.subheader("Interest Coverage Ratio Analysis")
        
        st.plotly_chart(
            chart_stressed_icr_by_year(filtered_model, selected_sectors),
            use_container_width=True,
        )
        
        st.divider()
        
        # ICR decline pivot table
        st.subheader("ICR Decline Under Stress (%)")
        pivot_decline = filtered_model.pivot_table(
            index="Sector",
            columns="Year",
            values="ICR_Decline_Pct",
            aggfunc="first"
        )
        pivot_decline.columns = [str(c) for c in pivot_decline.columns]
        
        st.dataframe(
            pivot_decline.style.format("{:.2f}%", na_rep="—"),
            use_container_width=True,
        )
    
    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3: REFINANCING EXPOSURE
    # ══════════════════════════════════════════════════════════════════════════
    with tab_refinancing:
        st.subheader("Refinancing Exposure")
        
        st.plotly_chart(
            chart_cumulative_refinancing(filtered_model, selected_sectors),
            use_container_width=True,
        )
        
        st.divider()
        
        # Debt maturing
        st.subheader("Debt Maturing by Year (USD bn)")
        pivot_debt = filtered_model.pivot_table(
            index="Sector",
            columns="Year",
            values="Debt_Maturing_USD_Bn",
            aggfunc="first"
        )
        pivot_debt.columns = [str(c) for c in pivot_debt.columns]
        
        st.dataframe(
            pivot_debt.style.format("{:,.2f}", na_rep="—"),
            use_container_width=True,
        )
        
        st.divider()
        
        # Additional interest
        st.subheader("Additional Interest Expense (USD bn)")
        pivot_interest = filtered_model.pivot_table(
            index="Sector",
            columns="Year",
            values="Additional_Interest_Expense",
            aggfunc="first"
        )
        pivot_interest.columns = [str(c) for c in pivot_interest.columns]
        
        st.dataframe(
            pivot_interest.style.format("{:,.4f}", na_rep="—"),
            use_container_width=True,
        )
    
    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4: RATING MIGRATION
    # ══════════════════════════════════════════════════════════════════════════
    with tab_migration:
        st.subheader("Rating Migration Summary")
        
        summary = build_summary_table(filtered_model)
        
        st.dataframe(
            summary.style.format({
                "Min_ICR": "{:.3f}",
                "Avg_ICR": "{:.3f}",
                "Max_ICR": "{:.3f}",
                "Max_Interest_Δ(%)": "{:.2f}",
                "Max_Refi(%)": "{:.2f}",
            }, na_rep="—"),
            use_container_width=True,
            hide_index=True,
        )
        
        st.divider()
        
        # Transition matrix
        st.subheader("Rating Transition Matrix (Final Year)")
        transition = build_migration_matrix(filtered_model)
        st.dataframe(transition, use_container_width=True)
        
        st.divider()
        
        # Fallen angels
        st.subheader("Fallen Angel Events (IG → SG)")
        fa = filtered_model[filtered_model["Fallen_Angel_Flag"] == True][[
            "Sector", "Year", "Synthetic_Rating_y", "Stressed_Rating",
            "Current_Rating_Score", "Stressed_Rating_Score"
        ]].drop_duplicates()
        
        if len(fa) > 0:
            st.dataframe(fa, use_container_width=True, hide_index=True)
        else:
            st.info("No fallen angel events under current scenario.")
    
    # ══════════════════════════════════════════════════════════════════════════
    # TAB 5: SECTOR DETAIL
    # ══════════════════════════════════════════════════════════════════════════
    with tab_sector:
        st.subheader("Single-Sector Deep Dive")
        
        chosen_sector = st.selectbox(
            "Choose sector",
            options=selected_sectors,
            key="sector_select",
        )
        
        sector_data = model[model["Sector"] == chosen_sector].sort_values("Year")
        
        if len(sector_data) == 0:
            st.warning(f"No data for {chosen_sector}")
        else:
            # ICR trajectory
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=sector_data["Year"].astype(str),
                y=sector_data["ICR_Mid_y"],
                name="Baseline ICR",
                mode="lines+markers",
                line=dict(color=COLOUR_NEUTRAL, dash="dot", width=2),
                marker=dict(symbol="circle", size=8),
            ))
            
            fig.add_trace(go.Scatter(
                x=sector_data["Year"].astype(str),
                y=sector_data["Stressed_ICR"],
                name="Stressed ICR",
                mode="lines+markers",
                line=dict(color=COLOUR_STRESS, width=2),
                marker=dict(symbol="x", size=10),
            ))
            
            icr_low = sector_data["ICR_Low"].iloc[0]
            icr_high = sector_data["ICR_High"].iloc[0]
            
            fig.add_hline(
                y=icr_low,
                line_dash="dash",
                line_color=COLOUR_STRESS,
                annotation_text="Downgrade Threshold",
                annotation_position="right",
            )
            
            fig.add_hline(
                y=icr_high,
                line_dash="dash",
                line_color=COLOUR_IMPROVE,
                annotation_text="Upgrade Threshold",
                annotation_position="right",
            )
            
            fig.update_layout(
                title=f"ICR Trajectory — {chosen_sector}",
                xaxis_title="Year",
                yaxis_title="ICR (×)",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=500,
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            
            # Detailed metrics
            st.subheader(f"Metrics — {chosen_sector}")
            detail_cols = [
                "Year", "Synthetic_Rating_y", "Stressed_Rating", "Notches_Changed",
                "ICR_Mid_y", "Stressed_ICR", "ICR_Decline_Pct",
                "Debt_Maturing_USD_Bn", "Refinancing_Pct",
                "Interest_Expense_Increase_Pct", "Threshold_Status"
            ]
            
            detail = sector_data[
                [c for c in detail_cols if c in sector_data.columns]
            ].copy()
            detail["Year"] = detail["Year"].astype(str)
            
            st.dataframe(
                detail.style.format({
                    "ICR_Mid_y": "{:.3f}",
                    "Stressed_ICR": "{:.3f}",
                    "ICR_Decline_Pct": "{:.2f}%",
                    "Debt_Maturing_USD_Bn": "{:,.2f}",
                    "Refinancing_Pct": "{:.2f}%",
                    "Interest_Expense_Increase_Pct": "{:.4f}%",
                    "Notches_Changed": "{:+.0f}",
                }, na_rep="—"),
                use_container_width=True,
                hide_index=True,
            )
    
    # ══════════════════════════════════════════════════════════════════════════
    # TAB 6: FULL DATA
    # ══════════════════════════════════════════════════════════════════════════
    with tab_data:
        st.subheader("Full Model Output")
        st.caption("Complete calculated dataset with all stress metrics.")
        
        display_df = filtered_model.copy()
        display_df["Year"] = display_df["Year"].astype(str)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )
        
        # Download button
        csv_export = display_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download as CSV",
            data=csv_export,
            file_name="dmrra_stress_output.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
