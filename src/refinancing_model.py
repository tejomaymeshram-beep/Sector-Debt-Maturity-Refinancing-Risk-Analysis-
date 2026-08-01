"""
refinancing_model.py

Sector refinancing risk metrics.
"""

import pandas as pd


def calculate_exposure_score(
    refi: pd.DataFrame
) -> pd.DataFrame:
    """
    Score sectors based on refinancing exposure.
    """

    refi = refi.copy()

    refi["Exposure_Score"] = (
        refi["Debt_Maturing_USD_Bn"]
        /
        refi["Debt_Maturing_USD_Bn"].max()
    ) * 100

    return refi


def calculate_rating_risk_score(
    refi: pd.DataFrame
) -> pd.DataFrame:
    """
    Higher score represents weaker credit quality.
    """

    refi = refi.copy()

    refi["Rating_Risk_Score"] = (

        (
            refi["Rating_Score"].max()
            -
            refi["Rating_Score"]
        )

        /

        (
            refi["Rating_Score"].max()
            -
            refi["Rating_Score"].min()
        )

    ) * 100

    return refi


def calculate_icr_risk_score(
    refi: pd.DataFrame
) -> pd.DataFrame:
    """
    Lower ICR implies higher refinancing risk.
    """

    refi = refi.copy()

    refi["ICR_Risk_Score"] = (

        (
            refi["ICR_Mid"].max()
            -
            refi["ICR_Mid"]
        )

        /

        (
            refi["ICR_Mid"].max()
            -
            refi["ICR_Mid"].min()
        )

    ) * 100

    return refi


def calculate_baseline_risk_index(
    refi: pd.DataFrame,
    exposure_weight=0.40,
    rating_weight=0.30,
    icr_weight=0.30
) -> pd.DataFrame:
    """
    Composite refinancing risk score.
    """

    refi = refi.copy()

    refi["Baseline_Risk_Index"] = (

        exposure_weight
        * refi["Exposure_Score"]

        +

        rating_weight
        * refi["Rating_Risk_Score"]

        +

        icr_weight
        * refi["ICR_Risk_Score"]

    )

    return refi


def rank_refinancing_risk(
    refi: pd.DataFrame
) -> pd.DataFrame:
    """
    Rank sectors by baseline refinancing risk.
    """

    refi = refi.sort_values(

        "Baseline_Risk_Index",

        ascending=False

    ).reset_index(drop=True)

    return refi


def build_refinancing_risk_profile(
    refinancing_baseline: pd.DataFrame
) -> pd.DataFrame:
    """
    Complete refinancing risk pipeline.
    """

    refi = calculate_exposure_score(
        refinancing_baseline
    )

    refi = calculate_rating_risk_score(
        refi
    )

    refi = calculate_icr_risk_score(
        refi
    )

    refi = calculate_baseline_risk_index(
        refi
    )

    refi = rank_refinancing_risk(
        refi
    )

    return refi
