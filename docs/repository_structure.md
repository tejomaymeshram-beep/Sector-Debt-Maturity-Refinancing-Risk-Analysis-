# Repository Structure

## Objective

The repository separates raw data, processed data, reusable source code, notebooks, documentation, dashboard components and tests.

Each file has a single responsibility.

Business logic exists only inside `src/`.

Notebooks call reusable functions instead of containing calculations.

---

# Directory Layout

```
Sector-Debt-Maturity-Refinancing-Risk-Analysis/

│
├── dashboard/
│   └── dashboard.py
│
├── data/
│   ├── raw/
│   ├── intermediate/
│   ├── processed/
│   └── final/
│
├── docs/
│   ├── assumptions.md
│   ├── data_dictionary.md
│   ├── methodology.md
│   └── repository_structure.md
│
├── notebooks/
│   ├── 01_build_datasets.ipynb
│   ├── 02_stress_model.ipynb
│   └── 03_dashboard_export.ipynb
│
├── src/
│   ├── config.py
│   ├── io.py
│   ├── preprocessing.py
│   ├── sector_model.py
│   ├── credit_model.py
│   ├── refinancing_model.py
│   ├── stress_model.py
│   ├── dashboard_dataset.py
│   └── validation.py
│
├── tests/
│
├── README.md
├── LICENSE
├── requirements.txt
└── .gitignore
```

---

# Folder Responsibilities

## dashboard/

Contains the Streamlit application.

Performs user interaction and visualisation.

Contains no financial calculations.

---

## data/

Stores every dataset used by the project.

### raw/

Original source files.

Never modified.

### intermediate/

Temporary outputs generated during processing.

Can be recreated.

### processed/

Reference datasets used by the financial model.

Produced by Notebook 1.

### final/

Final datasets exported for dashboard consumption.

Produced by Notebook 3.

---

## docs/

Project documentation.

Contains methodology, assumptions, data dictionary and repository structure.

No executable code.

---

## notebooks/

Pipeline execution.

Notebook 1 builds processed datasets.

Notebook 2 performs refinancing stress calculations.

Notebook 3 prepares dashboard datasets.

---

## src/

Reusable Python modules.

Contains every financial calculation.

No duplicated logic or notebook-specific code.

---

## tests/

Validation scripts.

Verifies calculations, joins, missing values and output consistency.

---

# Execution Flow

```
Raw Data
    │
    ▼
Notebook 1
    │
    ▼
Processed Data
    │
    ▼
Notebook 2
    │
    ▼
Stress Model
    │
    ▼
Notebook 3
    │
    ▼
Dashboard Dataset
    │
    ▼
Streamlit Dashboard
```

---

# Design Principles

- One responsibility per file
- No duplicated calculations
- Reusable modules only inside `src/`
- Raw data remains unchanged
- Every output is reproducible
- User inputs affect only scenario calculations
- All file paths are repository-relative
- Dashboard consumes exported datasets rather than rebuilding the pipeline
