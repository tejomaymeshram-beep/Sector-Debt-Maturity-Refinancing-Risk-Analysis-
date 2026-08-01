"""
test_stress_model.py

Validation tests for stress model calculations.
"""

import pandas as pd
import numpy as np
from pathlib import Path


def test_stress_model_output_shape():
    """Verify stress model output dimensions."""
    
    from src.io import load_csv
    
    DATA_DIR = Path("data/processed")
    model = load_csv(DATA_DIR / "sector_stress_model.csv")
    
    # 8 sectors × 4 years = 32 rows
    assert len(model) == 32, f"Expected 32 rows, got {len(model)}"
    
    # Should have many columns after all calculations
    assert model.shape[1] >= 40, f"Expected >=40 columns, got {model.shape[1]}"
    
    print("✓ test_stress_model_output_shape passed")


def test_notches_changed_is_integer():
    """Verify Notches_Changed contains only integers."""
    
    from src.io import load_csv
    
    DATA_DIR = Path("data/processed")
    model = load_csv(DATA_DIR / "sector_stress_model.csv")
    
    non_null = model[model["Notches_Changed"].notna()]
    assert all(
        non_null["Notches_Changed"] == non_null["Notches_Changed"].astype(int)
    ), "Notches_Changed must be integers"
    
    print("✓ test_notches_changed_is_integer passed")


def test_icr_range_validity():
    """Verify ICR_Low < ICR_Mid < ICR_High."""
    
    from src.io import load_csv
    
    DATA_DIR = Path("data/processed")
    credit = load_csv(DATA_DIR / "sector_credit_profile.csv")
    
    assert all(
        credit["ICR_Low"] <= credit["ICR_Mid"]
    ), "ICR_Low must be ≤ ICR_Mid"
    
    assert all(
        credit["ICR_Mid"] <= credit["ICR_High"]
    ), "ICR_Mid must be ≤ ICR_High"
    
    print("✓ test_icr_range_validity passed")


def test_allocation_sums_to_100():
    """Verify sector allocations sum to 100% each year."""
    
    from src.io import load_csv
    
    DATA_DIR = Path("data/processed")
    alloc = load_csv(DATA_DIR / "sector_maturity_allocation_by_year.csv")
    
    year_cols = [c for c in alloc.columns if c != "Sector"]
    
    for year in year_cols:
        total = alloc[year].sum()
        assert abs(total - 100.0) < 1.0, (
            f"Year {year} allocation total {total:.2f}% (expected ~100%)"
        )
    
    print("✓ test_allocation_sums_to_100 passed")


def test_no_null_key_columns():
    """Verify no nulls in critical columns."""
    
    from src.io import load_csv
    
    DATA_DIR = Path("data/processed")
    model = load_csv(DATA_DIR / "sector_stress_model.csv")
    
    critical = [
        "Sector",
        "Year",
        "Stressed_Rating",
        "Notches_Changed",
        "Stressed_ICR",
    ]
    
    for col in critical:
        null_count = model[col].isna().sum()
        assert null_count == 0, f"{col} has {null_count} nulls"
    
    print("✓ test_no_null_key_columns passed")


def test_dashboard_input_columns():
    """Verify dashboard_input.csv has required columns."""
    
    from src.io import load_csv
    
    DATA_DIR = Path("data/processed")
    dashboard = load_csv(DATA_DIR / "dashboard_input.csv")
    
    required = [
        "Sector",
        "Year",
        "Synthetic_Rating_y",
        "Stressed_Rating",
        "Notches_Changed",
        "Fallen_Angel_Flag",
        "ICR_Mid_y",
        "Stressed_ICR",
        "Interest_Expense_Increase_Pct",
        "Refinancing_Pct",
        "Cumulative_Refinancing_Pct",
    ]
    
    for col in required:
        assert col in dashboard.columns, f"Missing column {col}"
    
    print("✓ test_dashboard_input_columns passed")


def test_fallen_angel_logic():
    """Verify Fallen_Angel_Flag is only True for IG→SG transitions."""
    
    from src.io import load_csv
    
    DATA_DIR = Path("data/processed")
    model = load_csv(DATA_DIR / "sector_stress_model.csv")
    
    fallen_angels = model[model["Fallen_Angel_Flag"] == True]
    
    # All fallen angels should have Current_Rating_Score >= 10 and Stressed < 10
    for _, row in fallen_angels.iterrows():
        assert row["Current_Rating_Score"] >= 10
        assert row["Stressed_Rating_Score"] < 10
    
    print("✓ test_fallen_angel_logic passed")


def test_cumulative_metrics_monotonic():
    """Verify cumulative metrics are non-decreasing by year."""
    
    from src.io import load_csv
    
    DATA_DIR = Path("data/processed")
    model = load_csv(DATA_DIR / "sector_stress_model.csv")
    
    for sector in model["Sector"].unique():
        sector_data = model[model["Sector"] == sector].sort_values("Year")
        
        cumul_refi = sector_data["Cumulative_Refinancing_Pct"].values
        assert all(
            cumul_refi[i] <= cumul_refi[i+1] for i in range(len(cumul_refi)-1)
        ), f"{sector}: Cumulative_Refinancing_Pct not monotonic"
    
    print("✓ test_cumulative_metrics_monotonic passed")


def run_all_tests():
    """Execute all test functions."""
    
    tests = [
        test_stress_model_output_shape,
        test_notches_changed_is_integer,
        test_icr_range_validity,
        test_allocation_sums_to_100,
        test_no_null_key_columns,
        test_dashboard_input_columns,
        test_fallen_angel_logic,
        test_cumulative_metrics_monotonic,
    ]
    
    print("\n" + "="*70)
    print("RUNNING TEST SUITE")
    print("="*70 + "\n")
    
    failed = []
    
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed.append(test.__name__)
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            failed.append(test.__name__)
    
    print("\n" + "="*70)
    if failed:
        print(f"FAILED: {len(failed)} test(s)")
        for name in failed:
            print(f"  - {name}")
    else:
        print("SUCCESS: All tests passed")
    print("="*70 + "\n")


if __name__ == "__main__":
    run_all_tests()
