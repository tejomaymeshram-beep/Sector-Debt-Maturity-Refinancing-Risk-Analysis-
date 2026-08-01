# Methodology

## Project Objective
This project quantifies sector-level corporate debt refinancing risk under alternative interest-rate and credit-spread scenarios. It estimates the effect of refinancing upcoming debt maturities on interest expense, interest coverage, rating migration and refinancing pressure across sectors.

## Scope
The analysis is performed at the sector level using publicly available financial datasets. Company-level refinancing schedules are outside the scope because comprehensive maturity schedules are not publicly available without commercial data providers.

## Business Problem
Large debt maturity concentrations create refinancing risk when borrowing costs increase. Higher refinancing costs increase interest expense, reduce interest coverage and may lead to rating deterioration. The project measures this transmission mechanism under user-defined stress scenarios.

## Modelling Philosophy
The model follows a deterministic cash-flow approach.

It does not estimate default probabilities.

It does not forecast macroeconomic variables.

It measures how predefined financing shocks propagate through sector financials.

## Data Sources

### NYU Stern (Professor Aswath Damodaran)
Used for sector financial characteristics.

Source datasets include:
- Cost of debt
- Capital structure
- EBITDA margin
- Net margin
- Gross margin
- Cost of capital
- Beta

These datasets provide the sector financial inputs used throughout the model.

### S&P Investor Fact Book
Used for global corporate debt maturity walls.

Provides:
- Global debt maturing by year
- Regional maturity schedules
- Investment-grade debt
- Speculative-grade debt

These values define the refinancing universe.

## Data Preparation

Raw datasets undergo:

- industry reconciliation
- sector mapping
- weighted aggregation
- rating assignment
- maturity allocation
- validation

The outputs become processed datasets used by the calculation engine.

## Sector Construction

Individual industries are mapped into sectors.

Excluded industries include:

- Banks
- Insurance
- Real Estate
- Utilities

These sectors are excluded because their capital structures differ materially from non-financial corporates and require separate modelling assumptions.

## Sector Aggregation

Sector financial metrics are calculated using debt-weighted averages.

Debt is used as the weighting variable because larger borrowers contribute proportionally more to refinancing exposure.

Metrics aggregated include:

- Cost of debt
- Cost of capital
- EBITDA margin
- Gross margin
- Net margin
- Beta
- Short-term debt percentage

## Credit Profile Construction

Each sector is assigned:

- synthetic credit rating
- rating score
- implied interest coverage ratio
- downgrade threshold
- upgrade threshold

Synthetic ratings are assigned using Professor Damodaran's default spread methodology for Small/Riskier firms.

## Debt Maturity Allocation

Sector-level maturity schedules are not publicly available.
The model therefore allocates each year's regional maturity wall across sectors using user-defined allocation percentages.
Default allocation equals sector debt share.
Users may replace these allocations without modifying model code.
The model intentionally does not normalise allocations.
Incorrect allocations remain visible to the user.

## Stress Framework

User-defined inputs are supplied through:
stress_parameter_template.csv

For each year the user specifies:

- base rate shock
- credit spread shock
- EBITDA shock

The dashboard recalculates all dependent metrics from these inputs.

## Refinancing Model

For each sector and year the model calculates:

- refinancing cost
- additional interest expense
- cumulative refinancing burden
- stressed interest expense
- stressed EBITDA
- stressed interest coverage
- refinancing percentage
- cumulative refinancing percentage

These calculations produce the stressed financial profile.

## Rating Migration

Stressed interest coverage is compared against predefined rating bands.

The model determines:

- stressed rating
- notch change
- downgrade flag
- upgrade flag
- fallen angel flag

Rating bands are fixed reference data.

The model does not estimate new rating boundaries.

## Validation

Validation was performed at multiple stages.

Checks include:

- dataset completeness
- industry reconciliation
- duplicate detection
- allocation totals
- weighted aggregation
- maturity reconciliation
- rating consistency
- calculation verification

Regional maturity totals differ from published rating breakdowns by approximately USD 1 billion in several years.

These differences are attributable to source-table rounding and were retained to preserve source fidelity.

## Model Assumptions

The principal assumptions are:

- sector debt share approximates sector maturity share
- refinancing occurs at year-end
- refinancing affects interest expense immediately
- existing debt pricing remains unchanged
- only refinanced debt reprices
- sector financial characteristics remain representative
- rating methodology remains fixed
- users provide economically reasonable stress inputs

## Model Limitations

The model does not include:

- company-level maturity schedules
- bond-level refinancing
- floating-rate debt repricing
- covenant modelling
- liquidity analysis
- debt amortisation
- maturity extensions
- default probability estimation
- behavioural responses
- macroeconomic forecasting

These limitations arise primarily from public data availability rather than modelling capability.

## Outputs

The project produces three categories of outputs.

Processed datasets:
- sector master
- sector credit profile
- refinancing baseline
- threshold profile
- stress parameters

Calculation outputs:
- stress model
- stress results
- stress summary

Dashboard output:
- interactive refinancing risk analysis under user-defined scenarios
