# Project Assumptions

## Purpose

This document records every modelling assumption used throughout the project.

Each assumption is explicit and documented.
Any future improvement should replace an assumption with observable data rather than introducing additional assumptions.

---

# Assumption 1

## Sector-Level Debt Maturity Allocation

### Statement

Publicly available sector-level corporate debt maturity schedules were not available.

Sector debt maturing each year is therefore assumed to be proportional to each sector's share of total debt.

### Implementation

Debt_Maturing_USD_Bn = Regional_Maturity_Wall × Sector_Allocation_Pct

### Reason

Neither S&P Global nor publicly available market datasets provide annual debt maturity schedules at the sector level.

Commercial datasets containing this information are subscription-based.

### Limitation

Some sectors refinance earlier or later than others.

The assumption removes this timing difference.

### Future Improvement

Replace proportional allocation with observed sector-level maturity schedules when reliable data becomes available.

---

# Assumption 2

## User-Controlled Allocation

### Statement

Sector allocation percentages are intentionally user editable.

### Reason

Different analysts may hold different refinancing assumptions.

Allowing user-defined allocations makes the project suitable for scenario analysis without modifying source code.

### Limitation

The dashboard does not automatically normalise yearly totals.

Users are responsible for maintaining internally consistent allocations.

The application should display a warning whenever yearly totals differ materially from 100%.

---

# Assumption 3

## Constant Baseline Financial Structure

### Statement

Sector financial characteristics remain constant throughout the stress horizon.

The following variables do not change across years.

- Total debt
- Interest expense
- Cost of debt
- EBITDA margin
- Net margin
- Gross margin
- Capital structure

### Reason

The project isolates refinancing risk.

Operational changes are introduced only through user-defined EBITDA stress.

### Limitation

Real companies continuously refinance, deleverage and change capital structure.

These dynamics are intentionally excluded.

---

# Assumption 4

## Synthetic Credit Ratings

### Statement

Sector ratings are derived using Professor Aswath Damodaran's synthetic rating methodology.

Professor Aswath Damodaran teaches Corporate Finance and Valuation at Stern School of Business, New York University.

### Reason

The methodology provides a transparent and widely recognised mapping between interest coverage ratios and credit ratings.

### Limitation

Synthetic ratings approximate average sector credit quality.

They are not agency-issued ratings.

---

# Assumption 5

## Rating Stability

### Statement

Baseline ratings remain fixed throughout the model.

Only stressed ratings are recalculated.

### Reason

The project evaluates migration caused by refinancing stress rather than historical rating transitions.

### Limitation

The model does not simulate gradual rating drift before stress occurs.

---

# Assumption 6

## Refinancing Pricing

### Statement

Every refinancing event is priced using the same annual scenario shock.

Refinancing_Cost = Avg_Cost_of_Debt + Scenario_Shock

### Reason

The objective is to measure sensitivity to changes in financing conditions.

### Limitation

Individual issuers refinance at different spreads depending on maturity, market access and credit quality.

---

# Assumption 7

## Cumulative Refinancing

### Statement

Additional interest expense accumulates over time.

Debt refinanced in one year continues to affect all subsequent years.

### Reason

New borrowing remains outstanding after refinancing.

### Limitation

The model does not include debt repayment or early refinancing after issuance.

---

# Assumption 8

## EBITDA Stress

### Statement

EBITDA changes only through user-defined percentage shocks.

### Reason

This isolates operating performance from refinancing effects.

### Limitation

Sector-specific earnings behaviour is not modelled.

---

# Assumption 9

## Geographic Scope

### Statement

Regional maturity walls are allocated using United States maturity schedules.

### Reason

The United States represents the largest publicly available corporate maturity dataset and provides sufficient coverage for scenario construction.

### Limitation

Sector refinancing patterns outside the United States may differ materially.

---

# Assumption 10

## Source Reconciliation

### Statement

Regional maturity totals were reconciled against financial and non-financial rating breakdowns.

Minor differences of approximately USD 1 billion were retained.

### Reason

These differences arise from source-table rounding and are immaterial relative to annual maturity volumes measured in hundreds or thousands of billions of dollars.

### Limitation

Perfect numerical reconciliation is intentionally not forced in order to preserve source lineage.

---

# Assumption 11

## Scope of the Project

### Statement

The project evaluates refinancing pressure.

It is not a default prediction model, bankruptcy forecasting model and bond valuation model.

### Primary Outputs

- Refinancing exposure
- Interest burden
- Interest coverage deterioration
- Rating migration
- Fallen angel identification

---

# Assumption 12

## Dashboard Behaviour

### Statement

Only user-editable scenario variables trigger recalculation inside the dashboard.

The financial methodology remains unchanged.

### User Inputs

- Base rate shock
- Credit spread shock
- EBITDA shock
- Sector allocation percentages

All remaining processed datasets are treated as fixed reference inputs.
