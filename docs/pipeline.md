# Pipeline Architecture

## Design Philosophy

The repository follows a one-directional data pipeline.

Raw data is transformed into validated intermediate datasets.

Validated datasets are converted into processed model inputs.

Processed inputs are consumed by the stress model.

Stress outputs are consumed by the dashboard.

No module is permitted to modify an upstream dataset.

Every stage produces deterministic outputs from deterministic inputs.

## Repository Flow

Raw Data
↓
Cleaning
↓
Validation
↓
Sector Aggregation
↓
Credit Profile Construction
↓
Refinancing Baseline Construction
↓
Stress Model
↓
Dashboard Outputs

## Directory Responsibilities

data/raw/
Original source datasets.
Never modified by project code.

data/intermediate/
Temporary cleaned datasets generated during processing.
May be deleted and regenerated.

data/processed/
Final datasets consumed by the dashboard and downstream calculations.

data/final/
Reference datasets obtained from external sources.
These remain unchanged and are used during processing.

src/
Reusable Python modules.
Contains all business logic.
No notebook-specific code.

dashboard/
Interactive dashboard.
Contains only user interface and dashboard-specific orchestration.
No financial calculations should originate here.

notebooks/
Demonstration notebooks only.
Used for executing the pipeline sequentially.
No business logic should exist exclusively inside notebooks.

docs/
Project documentation.

tests/
Validation scripts.

## Pipeline Stages

Stage 1
Read raw datasets.

Outputs:
Cleaned source tables.

Stage 2
Validate cleaned datasets.

Checks include:
- missing values
- duplicate records
- schema validation
- industry reconciliation
- mapping completeness

Outputs:
Validated intermediate datasets.

Stage 3
Construct sector master dataset.

Inputs:
- sector debt
- margins
- cost of capital
- mapping

Outputs:
sector_master.csv

Stage 4
Construct sector credit profile.

Inputs:
- sector_master.csv
- synthetic_rating_lookup.xlsx

Outputs:
sector_credit_profile.csv

Stage 5
Construct sector maturity allocation.

Inputs:
- sector_master.csv
- regional maturity wall

Outputs:
sector_maturity_allocation_by_year.csv

Stage 6
Construct refinancing baseline.

Inputs:
- sector_credit_profile.csv
- maturity allocation
- regional maturity wall

Outputs:
sector_refinancing_baseline.csv

Stage 7
Construct threshold profile.

Inputs:
- sector_credit_profile.csv
- rating lookup

Outputs:
sector_threshold_profile.csv

Stage 8
Execute stress model.

Inputs:
- sector_master.csv
- sector_credit_profile.csv
- sector_refinancing_baseline.csv
- stress_parameter_template.csv

Outputs:
- sector_stress_model.csv
- sector_stress_results.csv
- sector_stress_summary.csv
- dashboard_input.csv

Stage 9
Dashboard.

Reads only processed CSV files.

Accepts user-defined stress inputs.

Recalculates only stress-dependent variables.

Writes nothing to disk.

## Dependency Graph

Raw Damodaran Files
│
├── sector_mapping.csv
│
├── sector_debt_clean.xlsx
├── sector_margin_clean.xlsx
├── sector_wacc_clean.xlsx
│
▼
sector_master.csv
│
├──────────────┐
│              │
▼              ▼
sector_credit_profile.csv
sector_maturity_allocation_by_year.csv
│              │
└──────┬───────┘
       │
regional_maturity_wall.csv
       │
       ▼
sector_refinancing_baseline.csv
       │
       ├──────────────┐
       │              │
sector_master.csv     │
sector_credit_profile.csv
       │              │
stress_parameter_template.csv
       │
       ▼
sector_stress_model.csv
       │
       ▼
sector_stress_results.csv
       │
       ▼
sector_stress_summary.csv
       │
       ▼
dashboard_input.csv
       │
       ▼
dashboard.py

## Module Dependencies

Each module may import only lower-level modules.

Allowed

utils
↓

validation

↓

preprocessing

↓

aggregation

↓

credit

↓

refinancing

↓

stress

↓

dashboard

Not Allowed

dashboard
↓

stress

↓

dashboard

No circular dependencies are permitted.

## Data Ownership

Each dataset has exactly one creator.

sector_master.csv
Owned by aggregation module.

sector_credit_profile.csv
Owned by credit module.

sector_maturity_allocation_by_year.csv
Owned by allocation module.

sector_refinancing_baseline.csv
Owned by refinancing module.

sector_threshold_profile.csv
Owned by threshold module.

sector_stress_model.csv
Owned by stress module.

dashboard_input.csv
Owned by stress module.

No other module may overwrite these datasets.

## Error Handling

Every pipeline stage must verify:

- required files exist
- expected columns exist
- column data types
- duplicate keys
- missing critical values
- merge success
- output row counts

Execution stops immediately if validation fails.

## Reproducibility

Running the complete pipeline from the same input datasets must always generate identical processed datasets.

No random numbers.

No manual edits.

No hidden notebook state.

No execution-order dependence.

Every output must be reproducible from repository contents alone.
