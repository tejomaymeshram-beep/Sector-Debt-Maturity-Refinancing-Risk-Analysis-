# Data Dictionary

## Purpose

This document defines every dataset used by the project pipeline.
Each dataset has one owner, one creation stage, and one downstream purpose.

No dataset should exist without a defined consumer.

## Dataset Flow

Raw Data
↓

Intermediate Processing
↓

Processed Datasets
↓

Stress Model
↓

Dashboard

---

# sector_mapping.csv

## Owner

Sector Aggregation Module

## Source

Manual mapping created from Damodaran industry classifications.

## Purpose

Maps individual industries into DMRRA sectors.

## Primary Key

Industry_Name

## Columns

| Column | Description |
|----------|-------------|
| Industry_Name | Original Damodaran industry |
| DMRRA_Sector | Final project sector |
| Status | INCLUDE or EXCLUDE |

## Downstream Used By

- sector_master.csv

---

# sector_master.csv

## Owner

Aggregation Module

## Source

Debt dataset

Margin dataset

WACC dataset

Sector mapping

## Purpose

Contains debt-weighted financial characteristics for each sector.

Represents the financial baseline of every sector.

## Primary Key

Sector

## Columns

| Column | Description |
|----------|-------------|
| Sector | Final sector name |
| Industry_Count | Number of industries included |
| Total_Debt_M | Total debt |
| Total_Interest_Expense_M | Interest expense |
| Avg_Cost_of_Debt | Debt-weighted cost of debt |
| Avg_Debt_Pct | Debt ratio |
| Avg_Cost_of_Capital | Weighted cost of capital |
| Avg_EBITDA_Margin | EBITDA margin |
| Avg_Net_Margin | Net margin |
| Avg_Gross_Margin | Gross margin |
| Avg_Beta | Debt-weighted beta |
| Avg_ST_Debt_Pct | Short-term debt percentage |

## Downstream Used By

- sector_credit_profile.csv
- sector_stress_model.csv

---

# sector_credit_profile.csv

## Owner

Credit Module

## Source

sector_master.csv

Damodaran synthetic rating table

## Purpose

Assigns synthetic ratings to sectors.

Provides all credit characteristics required by the stress model.

## Primary Key

Sector

## Columns

| Column | Description |
|----------|-------------|
| Sector | Sector name |
| Avg_Cost_of_Debt | Sector borrowing cost |
| Default_Spread | Implied default spread |
| Synthetic_Rating | Baseline rating |
| ICR_Low | Downgrade threshold |
| ICR_High | Upgrade threshold |
| ICR_Mid | Midpoint of rating band |
| Rating_Score | Numeric rating scale |

## Downstream Used By

- sector_refinancing_baseline.csv
- sector_threshold_profile.csv
- sector_stress_model.csv

---

# sector_threshold_profile.csv

## Owner

Threshold Module

## Source

sector_credit_profile.csv

## Purpose

Stores rating transition boundaries.

No calculations originate here.

## Primary Key

Sector

## Columns

| Column | Description |
|----------|-------------|
| Sector | Sector |
| Synthetic_Rating | Baseline rating |
| Lower_ICR | Downgrade threshold |
| Upper_ICR | Upgrade threshold |
| Distance_To_Downgrade | Current downgrade buffer |
| Distance_To_Upgrade | Current upgrade buffer |
| Downgrade_Buffer_Pct | Relative downgrade buffer |
| Upgrade_Buffer_Pct | Relative upgrade buffer |

## Downstream Used By

Dashboard

---

# sector_maturity_allocation_by_year.csv

## Owner

Allocation Module

## Source

sector_master.csv

## Purpose

Stores user-editable maturity allocation assumptions.

## Primary Key

Sector

## Columns

| Column | Description |
|----------|-------------|
| Sector | Sector |
| 2026 | Allocation percentage |
| 2027 | Allocation percentage |
| 2028 | Allocation percentage |
| 2029 | Allocation percentage |

## Validation Rules

Each year should total approximately 100%.

The dashboard should warn if totals differ materially.

The dashboard must never automatically normalise values.

## Downstream Used By

sector_refinancing_baseline.csv

---

# sector_refinancing_baseline.csv

## Owner

Refinancing Module

## Source

Regional maturity wall

Sector allocation

Sector credit profile

## Purpose

Transforms regional maturity totals into sector-level refinancing exposure.

Represents baseline refinancing before stress.

## Primary Key

Sector + Year

## Columns

| Column | Description |
|----------|-------------|
| Sector | Sector |
| Year | Calendar year |
| Allocation_Pct | Sector allocation |
| Total_Debt_USD_Bn | Regional maturity wall |
| Debt_Maturing_USD_Bn | Sector debt maturing |
| Synthetic_Rating | Baseline rating |
| Rating_Score | Numeric rating |
| ICR_Mid | Baseline interest coverage |

## Downstream Used By

sector_stress_model.csv

---

# stress_parameter_template.csv

## Owner

User

## Source

Manual input

## Purpose

Contains all scenario assumptions.

This is the only dataset intentionally modified by users during dashboard execution.

## Primary Key

Year

## Columns

| Column | Description |
|----------|-------------|
| Year | Scenario year |
| Base_Rate_Shock_bp | Treasury shock |
| Credit_Spread_Shock_bp | Spread shock |
| EBITDA_Shock_Pct | Earnings shock |

## Downstream Used By

sector_stress_model.csv

---

# sector_stress_model.csv

## Owner

Stress Module

## Source

Merged calculation dataset.

## Purpose

Intermediate calculation table.

Contains every calculation required to produce dashboard outputs.

This dataset should never be edited manually.

## Primary Key

Sector + Year

## Major Variable Groups

Baseline Variables

Stress Inputs

Interest Calculations

Coverage Calculations

Rating Calculations

Migration Variables

Risk Indicators

## Downstream Used By

sector_stress_results.csv

dashboard_input.csv

---

# sector_stress_results.csv

## Owner

Stress Module

## Purpose

Stores final stressed financial outputs.

Contains one record per sector per year.

## Primary Key

Sector + Year

## Typical Variables

- Stressed_ICR
- Stressed_Rating
- Rating_Score
- Interest_Expense
- Notches_Changed
- Downgrade_Flag
- Upgrade_Flag
- Fallen_Angel_Flag

## Downstream Used By

Dashboard

---

# sector_stress_summary.csv

## Owner

Stress Module

## Purpose

Stores aggregated dashboard statistics.

Contains summary metrics only.

Examples include:

- downgrade counts
- upgrade counts
- fallen angel count
- worst sector
- worst year
- average rating change

## Downstream Used By

Dashboard KPI cards

---

# dashboard_input.csv

## Owner

Stress Module

## Purpose

Final dataset consumed by dashboard visualisations.

The dashboard should not perform financial modelling using raw datasets.

Only user-defined scenario variables should trigger recalculation.

## Primary Key

Sector + Year

## Typical Variables

| Variable Group | Examples |
|---------------|----------|
| Sector | Sector, Year |
| Credit | Baseline Rating, Stressed Rating |
| Interest | Interest Expense, Interest Increase |
| Coverage | Baseline ICR, Stressed ICR |
| Migration | Notches Changed, Fallen Angel Flag |
| Exposure | Debt Maturing, Refinancing Percentage |

---

# Data Ownership Rules

Each processed dataset has exactly one producing module.

No downstream module may overwrite an upstream dataset.

Intermediate datasets may be regenerated.

Processed datasets are treated as stable interfaces between modules.

Dashboard code must consume processed datasets only.

Business logic must never be duplicated inside the dashboard.

The dashboard is responsible only for user interaction, scenario updates and visualisation.

All financial calculations remain inside the stress calculation module.
