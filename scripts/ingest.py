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


def ingest_questions(conn, df):
    print("Ingesting questions")
    values = []
    cursor = conn.cursor()

    for _, row in df.iterrows():
        r = row[
            [
                "QuestionId",
                "Survey",
                "Question",
                "QuestionType",
                "Profile Characteristic",
                "Note",
            ]
        ]

        if r["QuestionId"] == "NULL":
            break
        r["QuestionId"] = int(r["QuestionId"])
        r["Survey"] = int(r["Survey"])
        assert r["Survey"] in (1, 2)
        values.append(tuple(r.values))
    print(values[0])

    # --- INSERT INTO THE TABLE and commit changes
    cursor.executemany(
        """INSERT INTO question (Id, SurveyId, Question, QuestionType, ProfileCharacteristic, Note) VALUES (%s, %s, %s, %s, %s, %s)""",
        values,
    )
    conn.commit()


def ingest_users(conn, df):
    print("Ingesting users")
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
    print("Ingesting surveys")
    values = []
    cursor = conn.cursor()

    for _, row in df.iterrows():
        r = tuple(row[["Id", "Short Name", "Name", "Description"]].values)
        values.append(r)

    # --- INSERT INTO THE TABLE and commit changes
    cursor.executemany(
        """INSERT INTO survey (Id, ShortName, Name, Description, Created, LastUpdated) VALUES (%s, %s, %s, %s, NOW(), NOW())""",
        values,
    )
    conn.commit()


def ingest_data(filename: str):
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
    print("Dropped Tables")


def build_tables(conn, file_path="../sql/SETUP.sql"):
    with open(file_path) as cleanup:
        tables = cleanup.read()
        cursor = conn.cursor()
        cursor.execute(tables)
    print("Built Tables")


if __name__ == "__main__":
    conn = MySQLdb.connect(host="127.0.0.1", port=12345, user="root", database="temp")
    drop_tables(conn)
    build_tables(conn)

    sheets = ingest_data(
        "../data/info/Data-v03.xlsx",
    )

    ingest_surveys(conn, sheets["Surveys"])
    ingest_users(conn, sheets["Users"])
    ingest_questions(conn, sheets["Survey Questions New"])

    conn.close()
