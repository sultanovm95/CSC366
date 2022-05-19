import pandas as pd
import MySQLdb
import secrets
import numpy as np
import os
from dotenv import load_dotenv
#Loads Enviroment Variables from .env file use command: 'touch .env' to create
load_dotenv()

#PORT for MYSQL
PORT = int(os.getenv('PORT'))
#Either Absolute path to dir, relative path, or nothing
DIRPATH = os.getenv('DIRPATH')
DB = os.getenv('MYSQL_DB')

sheet_ingest_func = {
    "Surveys": 0,
    "Users": 0,
    "Survey Questions New": 0,
    "QuestionResponses": 0,
    "URE Experience": 0,
    "Work Experience": 0,
    "Work Profile": 0,
    "Work Preferences": 0,
}

def ingest_work_responses(conn, df):
    print("Ingesting WORK responses")
    responses = []
    answers = []
    cursor = conn.cursor()

    for i, row in df.iterrows():
        if i == 0:
            continue
        # remove empty cells from dataframe
        if set(row.values) == {"NULL"}:
            break
        r = row[:91]

        # insert response
        response_num = int(r[0].lower().replace(" ", "").replace("fakecase", ""))
        response = (response_num, int(r[1]), 2)
        print(response)
        responses.append(response)

        # if r["QuestionId"] == "NULL":
        #     break

        # r["QuestionId"] = int(r["QuestionId"])
        # r["Survey"] = int(r["Survey"])
        # r["ResponseValue"] = int(r["ResponseValue"])
        # values.append(tuple(r.values))

    # --- INSERT INTO THE TABLE and commit changes
    cursor.executemany(
        """INSERT INTO response (Id, UserId, SurveyId, AnswerDate) VALUES (%s, %s, %s, NOW())""",
        responses,
    )
    conn.commit()


def ingest_ure_responses(conn, df):
    print("Ingesting URE responses")
    responses = []
    answers = []
    cursor = conn.cursor()

    for i, row in df.iterrows():
        if i == 0:
            continue
        # remove empty cells from dataframe
        if set(row.values) == {"NULL"}:
            break
        r = row[:96]

        # insert response
        response_num = int(r[0].lower().replace(" ", "").replace("fakecase", ""))
        response = (response_num, int(r[1]), 1)
        print(response)
        responses.append(response)

        # if r["QuestionId"] == "NULL":
        #     break

        # r["QuestionId"] = int(r["QuestionId"])
        # r["Survey"] = int(r["Survey"])
        # r["ResponseValue"] = int(r["ResponseValue"])
        # values.append(tuple(r.values))

    # --- INSERT INTO THE TABLE and commit changes
    cursor.executemany(
        """INSERT INTO response (Id, UserId, SurveyId, AnswerDate) VALUES (%s, %s, %s, NOW())""",
        responses,
    )
    conn.commit()


def ingest_question_answers(conn, df):
    print("Ingesting question answers")
    values = []
    cursor = conn.cursor()

    for _, row in df.iterrows():
        r = row[["Survey", "QuestionId", "ResponseValue", "ResponseText", "Comment"]]

        if r["QuestionId"] == "NULL":
            break

        r["QuestionId"] = int(r["QuestionId"])
        r["Survey"] = int(r["Survey"])
        r["ResponseValue"] = int(r["ResponseValue"])
        values.append(tuple(r.values))

    # --- INSERT INTO THE TABLE and commit changes
    cursor.executemany(
        """INSERT INTO questionAcceptableAnswer (SurveyId, QuestionId, AnswerValue, AnswerText, Comment) VALUES (%s, %s, %s, %s, %s)""",
        values,
    )
    conn.commit()


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
        """INSERT INTO survey (Id, ShortName, Name, Description, CreatedDate, LastUpdated) VALUES (%s, %s, %s, %s, NOW(), NOW())""",
        values,
    )
    conn.commit()


def ingest_criteria(conn, df):
    values = []
    cursor = conn.cursor()

    for _, row in df.iloc[1:].iterrows():
        r = tuple(row[["ID", "Characteristc", "Description", "Dimension"]].values)
        values.append(r)

    # --- INSERT INTO THE TABLE and commit changes
    cursor.executemany(
        """INSERT INTO criteria (CId, cName, cDescription, cCategory) VALUES (%s, %s, %s, %s)""",
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


def drop_tables(conn, file_path= DIRPATH + "sql/CLEANUP.sql"):
    with open(file_path) as cleanup:
        drop = cleanup.read()
        cursor = conn.cursor()
        cursor.execute(drop)
    print("Dropped Tables")


def build_tables(conn, file_path= DIRPATH + "sql/SETUP.sql"):
    with open(file_path) as cleanup:
        tables = cleanup.read()
        cursor = conn.cursor()
        cursor.execute(tables)
    print("Built Tables")


if __name__ == "__main__":
    conn = MySQLdb.connect(host="127.0.0.1", port=PORT, user="root", database=DB)
    drop_tables(conn)
    build_tables(conn)

    sheets = ingest_data(
        DIRPATH + "data/info/Data-v03.xlsx",
    )

    ingest_surveys(conn, sheets["Surveys"])
    ingest_users(conn, sheets["Users"])
    ingest_questions(conn, sheets["Survey Questions New"])
    ingest_question_answers(conn, sheets["QuestionResponses"])
    ingest_ure_responses(conn, sheets["URE Experience"])
    ingest_work_responses(conn, sheets["Work Experience"])
    ingest_criteria(conn, pd.read_csv(DIRPATH + "data/info/profile.csv"))

    conn.close()
