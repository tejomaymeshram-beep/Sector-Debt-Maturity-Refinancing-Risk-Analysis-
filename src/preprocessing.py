"""
preprocessing.py

Utilities for preparing already-cleaned Damodaran datasets
for downstream modelling.
"""

from __future__ import annotations

import pandas as pd


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df.columns = (
        df.columns
          .str.strip()
          .str.replace(" ", "_")
          .str.replace("-", "_")
          .str.replace("%", "_Pct")
          .str.replace("/", "_", regex=False)
    )

    return df


def strip_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    obj_cols = df.select_dtypes(include="object").columns

    for col in obj_cols:
        df[col] = df[col].astype(str).str.strip()

    return df


def remove_duplicate_industries(
    df: pd.DataFrame,
    key: str = "Industry_Name"
) -> pd.DataFrame:

    if key not in df.columns:
        return df

    return (
        df
        .drop_duplicates(subset=key)
        .reset_index(drop=True)
    )


def convert_numeric_columns(
    df: pd.DataFrame,
    exclude=("Industry_Name",)
) -> pd.DataFrame:

    df = df.copy()

    for col in df.columns:

        if col in exclude:
            continue

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    return df


def preprocess_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generic preprocessing for Damodaran datasets.
    """

    df = standardize_columns(df)

    df = strip_text_columns(df)

    df = remove_duplicate_industries(df)

    df = convert_numeric_columns(df)

    return df
