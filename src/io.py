from pathlib import Path

import pandas as pd


def load_csv(path):

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"CSV file not found:\n{path}"
        )

    return pd.read_csv(path)


def save_csv(df, path, index=False):

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        path,
        index=index
    )


def load_excel(path, sheet_name=0):

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Excel file not found:\n{path}"
        )

    return pd.read_excel(
        path,
        sheet_name=sheet_name,
        engine="openpyxl"
    )


def save_excel(df, path, sheet_name="Sheet1"):

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with pd.ExcelWriter(
        path,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            sheet_name=sheet_name,
            index=False
        )


def file_exists(path):

    return Path(path).exists()


def make_directory(path):

    Path(path).mkdir(
        parents=True,
        exist_ok=True
    )


def list_files(directory):

    directory = Path(directory)

    if not directory.exists():
        raise FileNotFoundError(
            f"Directory not found:\n{directory}"
        )

    return sorted(directory.iterdir())


def load_multiple_csv(files):

    data = {}

    for name, path in files.items():

        data[name] = load_csv(path)

    return data


def load_multiple_excel(files):

    data = {}

    for name, path in files.items():

        data[name] = load_excel(path)

    return data
