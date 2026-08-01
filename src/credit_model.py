"""
credit_model.py

Build sector credit characteristics and refinancing baseline datasets.
"""

import pandas as pd


def calculate_default_spread(
    sector_master: pd.DataFrame,
    risk_free_rate: float,
) -> pd.DataFrame:
    """
    Compute sector default spreads.
    """

    credit = sector_master[
        [
            "Sector",
            "Avg_Cost_of_Debt"
        ]
    ].copy()

    credit["Default_Spread"] = (
        credit["Avg_Cost_of_Debt"]
        - risk_free_rate
    )

    return credit


def assign_synthetic_ratings(
    credit: pd.DataFrame,
    rating_lookup: pd.DataFrame,
) -> pd.DataFrame:
    """
    Match each sector to the closest synthetic rating.
    """

    lookup = rating_lookup[
        rating_lookup["Firm_Type"] == "Small/Riskier"
    ].copy()

    lookup = lookup[
        [
            "Synthetic_Rating",
            "Default_Spread",
            "Lower_ICR",
            "Upper_ICR"
        ]
    ]


    def nearest_rating(spread):

        idx = (
            lookup["Default_Spread"]
            - spread
        ).abs().idxmin()

        return lookup.loc[idx]


    rows = []

    for _, row in credit.iterrows():

        match = nearest_rating(
            row["Default_Spread"]
        )

        rows.append({

            "Sector":
                row["Sector"],

            "Avg_Cost_of_Debt":
                row["Avg_Cost_of_Debt"],

            "Default_Spread":
                row["Default_Spread"],

            "Synthetic_Rating":
                match["Synthetic_Rating"],

            "ICR_Low":
                match["Lower_ICR"],

            "ICR_High":
                match["Upper_ICR"],

            "ICR_Mid":
                (
                    match["Lower_ICR"]
                    +
                    match["Upper_ICR"]
                ) / 2

        })

    return pd.DataFrame(rows)


def add_rating_scores(
    credit: pd.DataFrame,
    rating_score_map: dict,
) -> pd.DataFrame:
    """
    Map synthetic ratings to numeric scores.
    """

    credit = credit.copy()

    credit["Rating_Score"] = (
        credit["Synthetic_Rating"]
        .map(rating_score_map)
    )

    return credit


def build_threshold_profile(
    credit: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate rating migration buffers.
    """

    profile = credit.copy()

    profile["Distance_To_Downgrade"] = (
        profile["ICR_Mid"]
        -
        profile["ICR_Low"]
    )

    profile["Distance_To_Upgrade"] = (
        profile["ICR_High"]
        -
        profile["ICR_Mid"]
    )

    profile["Downgrade_Buffer_Pct"] = (
        profile["Distance_To_Downgrade"]
        /
        profile["ICR_Mid"]
    ) * 100

    profile["Upgrade_Buffer_Pct"] = (
        profile["Distance_To_Upgrade"]
        /
        profile["ICR_Mid"]
    ) * 100

    return profile


def build_refinancing_baseline(
    allocation: pd.DataFrame,
    maturity_wall: pd.DataFrame,
    credit_profile: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build sector refinancing exposure table.
    """

    allocation_long = allocation.melt(

        id_vars="Sector",

        var_name="Year",

        value_name="Allocation_Pct"

    )

    allocation_long["Year"] = (
        allocation_long["Year"]
        .astype(int)
    )

    us_wall = maturity_wall[
        maturity_wall["Region"] == "US"
    ].copy()

    us_wall = us_wall[
        us_wall["Year"] >= 2026
    ].copy()

    refi = allocation_long.merge(

        us_wall,

        on="Year",

        how="left"

    )

    refi["Debt_Maturing_USD_Bn"] = (

        refi["Total_Debt_USD_Bn"]

        *

        refi["Allocation_Pct"]

        / 100

    )

    credit_cols = [

        "Sector",

        "Synthetic_Rating",

        "Rating_Score",

        "ICR_Mid"

    ]

    refi = refi.merge(

        credit_profile[credit_cols],

        on="Sector",

        how="left"

    )

    refi = refi[
        [

            "Sector",

            "Year",

            "Allocation_Pct",

            "Total_Debt_USD_Bn",

            "Debt_Maturing_USD_Bn",

            "Synthetic_Rating",

            "Rating_Score",

            "ICR_Mid"

        ]
    ]

    refi = refi.sort_values(

        [

            "Year",

            "Debt_Maturing_USD_Bn"

        ],

        ascending=[True, False]

    ).reset_index(drop=True)

    return refi
