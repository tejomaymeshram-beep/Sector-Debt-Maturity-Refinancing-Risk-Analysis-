"""
sector_model.py

Build sector-level financial profiles from Damodaran industry datasets.
"""

import numpy as np
import pandas as pd


def weighted_average(
    group: pd.DataFrame,
    value_col: str,
    weight_col: str,
):
    """
    Debt-weighted average.
    """

    valid = group[[value_col, weight_col]].dropna()

    if valid.empty:
        return np.nan

    return np.average(
        valid[value_col],
        weights=valid[weight_col]
    )


def build_sector_master(
    debt: pd.DataFrame,
    margins: pd.DataFrame,
    wacc: pd.DataFrame,
    mapping: pd.DataFrame,
    weight_col: str = "Total_Debt_with_Leases_M"
) -> pd.DataFrame:
    """
    Construct sector-level financial master table.
    """

    master = debt.merge(
        margins,
        on="Industry_Name",
        how="inner"
    )

    master = master.merge(
        wacc,
        on="Industry_Name",
        how="inner"
    )

    master = master.merge(
        mapping,
        on="Industry_Name",
        how="inner"
    )

    master = master[
        master["Status"] == "INCLUDE"
    ].copy()

    sector_rows = []

    for sector, grp in master.groupby("DMRRA_Sector"):

        row = {}

        row["Sector"] = sector

        row["Industry_Count"] = len(grp)

        row["Total_Debt_M"] = grp[
            "Total_Debt_with_Leases_M"
        ].sum()

        row["Total_Interest_Expense_M"] = grp[
            "Interest_Expense_M"
        ].sum()

        row["Avg_Cost_of_Debt"] = weighted_average(
            grp,
            "Cost_of_Debt",
            weight_col
        )

        row["Avg_Cost_of_Capital"] = weighted_average(
            grp,
            "Cost_of_Capital",
            weight_col
        )

        row["Avg_EBITDA_Margin"] = weighted_average(
            grp,
            "EBITDA_Margin",
            weight_col
        )

        row["Avg_Operating_Margin"] = weighted_average(
            grp,
            "Operating_Margin",
            weight_col
        )

        row["Avg_Net_Margin"] = weighted_average(
            grp,
            "Net_Margin",
            weight_col
        )

        row["Avg_Gross_Margin"] = weighted_average(
            grp,
            "Gross_Margin",
            weight_col
        )

        row["Avg_Beta"] = weighted_average(
            grp,
            "Beta",
            weight_col
        )

        row["Avg_ST_Debt_Pct"] = weighted_average(
            grp,
            "ST_Debt_Pct_Total",
            weight_col
        )

        sector_rows.append(row)

    sector_master = pd.DataFrame(
        sector_rows
    )

    sector_master = sector_master.sort_values(
        "Total_Debt_M",
        ascending=False
    ).reset_index(drop=True)

    return sector_master


def build_maturity_allocation(
    sector_master: pd.DataFrame,
    years=(2026, 2027, 2028, 2029)
) -> pd.DataFrame:
    """
    Allocate sector debt shares across maturity years.

    Current methodology assumes identical sector allocation
    each year, matching the original notebook.
    """

    total_debt = sector_master["Total_Debt_M"].sum()

    allocation = sector_master[
        [
            "Sector",
            "Total_Debt_M"
        ]
    ].copy()

    allocation["Share_Pct"] = (
        allocation["Total_Debt_M"]
        / total_debt
    ) * 100

    output = allocation[
        ["Sector"]
    ].copy()

    for year in years:
        output[str(year)] = allocation["Share_Pct"]

    return output
