"""
validation.py

Data validation and quality checks.
"""

import pandas as pd


def validate_dataframe_schema(
    df: pd.DataFrame,
    required_columns: list,
    name: str = "DataFrame"
) -> list[str]:
    """
    Check that dataframe contains all required columns.
    Returns list of error messages; empty if valid.
    """
    
    errors = []
    missing = [c for c in required_columns if c not in df.columns]
    
    if missing:
        errors.append(
            f"{name}: Missing columns {missing}"
        )
    
    return errors


def validate_no_nulls(
    df: pd.DataFrame,
    columns: list,
    name: str = "DataFrame"
) -> list[str]:
    """
    Check that specified columns have no null values.
    """
    
    errors = []
    
    for col in columns:
        if col not in df.columns:
            continue
        
        null_count = df[col].isna().sum()
        
        if null_count > 0:
            errors.append(
                f"{name}.{col}: {null_count} null values"
            )
    
    return errors


def validate_no_duplicates(
    df: pd.DataFrame,
    subset: list,
    name: str = "DataFrame"
) -> list[str]:
    """
    Check for duplicate rows on specified columns.
    """
    
    errors = []
    dup_count = df.duplicated(subset=subset).sum()
    
    if dup_count > 0:
        errors.append(
            f"{name}: {dup_count} duplicate rows on {subset}"
        )
    
    return errors


def validate_sector_refinancing_baseline(
    df: pd.DataFrame,
) -> list[str]:
    """
    Validate sector_refinancing_baseline.csv structure and content.
    """
    
    errors = []
    
    # Schema
    required_cols = [
        "Sector",
        "Year",
        "Allocation_Pct",
        "Total_Debt_USD_Bn",
        "Debt_Maturing_USD_Bn",
        "Synthetic_Rating",
        "Rating_Score",
        "ICR_Mid"
    ]
    errors.extend(
        validate_dataframe_schema(
            df,
            required_cols,
            "sector_refinancing_baseline"
        )
    )
    
    # No nulls in key columns
    key_cols = ["Sector", "Year", "Debt_Maturing_USD_Bn"]
    errors.extend(
        validate_no_nulls(df, key_cols, "sector_refinancing_baseline")
    )
    
    # Allocation totals per year should be ~100%
    if "Allocation_Pct" in df.columns and "Year" in df.columns:
        for year in df["Year"].unique():
            year_total = df[df["Year"] == year]["Allocation_Pct"].sum()
            if abs(year_total - 100.0) > 1.0:
                errors.append(
                    f"sector_refinancing_baseline: Year {year} allocation total {year_total:.2f}% (expected ~100%)"
                )
    
    return errors


def validate_credit_profile(
    df: pd.DataFrame,
) -> list[str]:
    """
    Validate sector_credit_profile.csv.
    """
    
    errors = []
    
    required_cols = [
        "Sector",
        "Avg_Cost_of_Debt",
        "Default_Spread",
        "Synthetic_Rating",
        "ICR_Low",
        "ICR_High",
        "ICR_Mid",
        "Rating_Score"
    ]
    errors.extend(
        validate_dataframe_schema(
            df,
            required_cols,
            "sector_credit_profile"
        )
    )
    
    key_cols = ["Sector", "Synthetic_Rating", "Rating_Score"]
    errors.extend(
        validate_no_nulls(df, key_cols, "sector_credit_profile")
    )
    
    # ICR ranges: Low < Mid < High
    if all(c in df.columns for c in ["ICR_Low", "ICR_Mid", "ICR_High"]):
        invalid = df[
            ~(
                (df["ICR_Low"] <= df["ICR_Mid"])
                &
                (df["ICR_Mid"] <= df["ICR_High"])
            )
        ]
        if len(invalid) > 0:
            errors.append(
                f"sector_credit_profile: {len(invalid)} rows violate ICR_Low ≤ ICR_Mid ≤ ICR_High"
            )
    
    return errors


def validate_stress_model_output(
    df: pd.DataFrame,
) -> list[str]:
    """
    Validate sector_stress_model.csv output.
    """
    
    errors = []
    
    required_cols = [
        "Sector",
        "Year",
        "Debt_Maturing_USD_Bn",
        "Stressed_ICR",
        "Stressed_Rating",
        "Notches_Changed",
        "Fallen_Angel_Flag",
        "Interest_Expense_Increase_Pct",
        "Refinancing_Pct",
        "Cumulative_Refinancing_Pct"
    ]
    errors.extend(
        validate_dataframe_schema(
            df,
            required_cols,
            "sector_stress_model"
        )
    )
    
    key_cols = ["Sector", "Year", "Stressed_Rating"]
    errors.extend(
        validate_no_nulls(df, key_cols, "sector_stress_model")
    )
    
    # Notches_Changed must be integer or NaN
    if "Notches_Changed" in df.columns:
        non_null = df[df["Notches_Changed"].notna()]
        if not all(non_null["Notches_Changed"] == non_null["Notches_Changed"].astype(int)):
            errors.append(
                "sector_stress_model.Notches_Changed: must be integer values"
            )
    
    return errors


def validate_sector_master(
    df: pd.DataFrame,
) -> list[str]:
    """
    Validate sector_master.csv.
    """
    
    errors = []
    
    required_cols = [
        "Sector",
        "Industry_Count",
        "Total_Debt_M",
        "Total_Interest_Expense_M",
        "Avg_Cost_of_Debt"
    ]
    errors.extend(
        validate_dataframe_schema(
            df,
            required_cols,
            "sector_master"
        )
    )
    
    key_cols = ["Sector", "Total_Debt_M"]
    errors.extend(
        validate_no_nulls(df, key_cols, "sector_master")
    )
    
    # No negative debt
    if "Total_Debt_M" in df.columns:
        negative = df[df["Total_Debt_M"] < 0]
        if len(negative) > 0:
            errors.append(
                f"sector_master: {len(negative)} sectors with negative Total_Debt_M"
            )
    
    return errors


def validate_maturity_allocation(
    df: pd.DataFrame,
) -> list[str]:
    """
    Validate sector_maturity_allocation_by_year.csv.
    """
    
    errors = []
    
    if "Sector" not in df.columns:
        errors.append("sector_maturity_allocation: missing Sector column")
        return errors
    
    # Year columns should exist and sum to ~100%
    year_cols = [c for c in df.columns if c != "Sector"]
    
    if not year_cols:
        errors.append(
            "sector_maturity_allocation: no year columns found"
        )
        return errors
    
    for year_col in year_cols:
        try:
            year_total = df[year_col].sum()
            if abs(year_total - 100.0) > 1.0:
                errors.append(
                    f"sector_maturity_allocation.{year_col}: sum {year_total:.2f}% (expected ~100%)"
                )
        except TypeError:
            errors.append(
                f"sector_maturity_allocation.{year_col}: cannot sum (type error)"
            )
    
    return errors


def run_all_validations(
    refinancing_baseline: pd.DataFrame,
    credit_profile: pd.DataFrame,
    sector_master: pd.DataFrame,
    maturity_allocation: pd.DataFrame,
    stress_model: pd.DataFrame = None,
) -> dict:
    """
    Run complete validation suite.
    Returns dict mapping dataset name to list of error messages.
    """
    
    results = {
        "sector_refinancing_baseline": validate_sector_refinancing_baseline(
            refinancing_baseline
        ),
        "sector_credit_profile": validate_credit_profile(
            credit_profile
        ),
        "sector_master": validate_sector_master(
            sector_master
        ),
        "sector_maturity_allocation": validate_maturity_allocation(
            maturity_allocation
        ),
    }
    
    if stress_model is not None:
        results["sector_stress_model"] = validate_stress_model_output(
            stress_model
        )
    
    return results


def print_validation_report(
    validation_results: dict,
) -> None:
    """
    Pretty-print validation results.
    """
    
    print("\n" + "="*70)
    print("VALIDATION REPORT")
    print("="*70)
    
    all_errors = []
    
    for dataset, errors in validation_results.items():
        
        if errors:
            print(f"\n❌ {dataset}")
            for err in errors:
                print(f"   - {err}")
            all_errors.extend(errors)
        else:
            print(f"\n✓ {dataset}")
    
    print("\n" + "="*70)
    if all_errors:
        print(f"FAILED: {len(all_errors)} validation error(s)")
    else:
        print("SUCCESS: All validations passed")
    print("="*70 + "\n")
