import pandas as pd
import MySQLdb
import secrets
import numpy as np

sheet_ingest_func = {
    "Surveys": 0,
    "Users": 0,
    "Survey Questions New": 0,
    "QuestionResponses": 0,
    "URE Survey Questions": 0,
    "Work Survey Questions": 0,
    "Survey Questions": 0,
    "URE Experience": 0,
    "Work Experience": 0,
    "Work Profile ": 0,
    "Work Profile-copy-values": 0,
    "Work Preferences": 0,
    "Definitions": 0,
}


def ingest_users(conn, df):
    values = []
    cursor = conn.cursor()

    for _, row in df.iterrows():
        r = row[["Id", "Name", "Email"]].values
        r = np.concatenate((r, [secrets.token_urlsafe(10), "user"]))
        values.append(tuple(r))

    # --- INSERT INTO THE TABLE and commit changes
    cursor.executemany(
        """INSERT INTO account (Id, Name, Email, Password, accountType) VALUES (%s, %s, %s, %s, %s)""",
        values,
    )
    conn.commit()


def ingest_surveys(conn, df):
    values = []
    cursor = conn.cursor()

    for _, row in df.iterrows():
        r = tuple(row[["Id", "Short Name", "Name", "Description"]].values)
        values.append(r)

    # --- INSERT INTO THE TABLE and commit changes
    cursor.executemany(
        """INSERT INTO survey (Id, ShortName, Name, Description, createdAt, lastUpdatedAt) VALUES (%s, %s, %s, %s, NOW(), NOW())""",
        values,
    )
    conn.commit()


def ingest_data(filename: str):
    """
    Ingest data from a csv file, returning the dataframes

    Parameters
    ----------
        filename : str
            path to .xlxs file

    Returns
    -------
        results : list of dict
            list of sheetnames with assicated dataframe for data

    Warns
    -----
        any sheets that can't be converted into a dataframe will be printed out for reformatting
    """
    book = pd.ExcelFile(filename, engine="openpyxl")
    results = {}

    for names in book.sheet_names:
        try:
            results[names] = pd.read_excel(book, names).replace(
                np.nan, "NULL", regex=True
            )
        except:  # noqa: E722
            print(f"{filename}:{names} failed to load due to formatting")
    return results


def drop_tables(conn, file_path="../sql/CLEANUP.sql"):
    with open(file_path) as cleanup:
        drop = cleanup.read()
        cursor = conn.cursor()
        cursor.execute(drop)


def build_tables(conn, file_path="../sql/SETUP.sql"):
    with open(file_path) as cleanup:
        tables = cleanup.read()
        cursor = conn.cursor()
        cursor.execute(tables)


if __name__ == "__main__":
    conn = MySQLdb.connect(host="127.0.0.1", port=12345, user="root", database="temp")
    drop_tables(conn)
    build_tables(conn)

    sheets = ingest_data(
        "../data/Data-v03.xlsx",
    )

    for key in sheets:
        if key == "Surveys":
            ingest_surveys(conn, sheets[key])
        elif key == "Users":
            ingest_users(conn, sheets[key])

    conn.close()
