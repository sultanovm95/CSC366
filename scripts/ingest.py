import pandas as pd
import MySQLdb
import secrets
import numpy as np
import os
import glob
from dotenv import load_dotenv
import math

# Loads Enviroment Variables from .env file use command: 'touch .env' to create
load_dotenv()

# PORT for MYSQL
USER = os.getenv("MYSQL_USER")
PASSWORD = os.getenv("PASSWORD")
HOST = os.getenv("MYSQL_HOST")
PORT = int(os.getenv("PORT"))
# Either Absolute path to dir, relative path, or nothing
DIRPATH = os.getenv("DIRPATH")
DB = os.getenv("MYSQL_DB")


def _retrieve_questions(conn, surveyid):
    cursor = conn.cursor()
    questions = {}

    cursor.execute(
        f"SELECT id, surveyid, question FROM question WHERE surveyid = {surveyid}"
    )
    result = cursor.fetchall()
    for q in result:
        questions[q[2].lower()] = q[0]
    # print(questions)
    return questions


def _check_questions(questions, check):
    for index, d in enumerate(check):
        assert questions.get(d) is not None, f"{index} {d}"


def ingest_work_responses(conn, df):
    print("Ingesting WORK responses")
    responses = []
    answers = []

    cursor = conn.cursor()
    questions = _retrieve_questions(conn, 2)
    q = []

    for i, row in df.iterrows():
        # remove empty cells from dataframe
        if set(row.values) == {"NULL"}:
            break
        r = row[:91]
        if i == 0:
            q = r[2:].apply(lambda x: x.replace("\n", "").lower()).values
            _check_questions(questions, q)
            continue

        # insert response
        response_num = int(r[0].lower().replace(" ", "").replace("fakecase", ""))
        response = (response_num, int(r[1]), 2, response_num + 50)
        responses.append(response)

        for i in range(len(r[2:])):
            ans = (questions[q[i]], response_num, r[i + 2])
            answers.append(ans)

    # --- INSERT INTO THE TABLE and commit changes
    cursor.executemany(
        """INSERT INTO response (Id, UserId, SurveyId, SurveyProfile, AnswerDate) VALUES (%s, %s, %s, %s, NOW())""",
        responses,
    )
    cursor.executemany(
        """INSERT INTO answers (QuestionId, ResponseId, AnswerValue) VALUES (%s, %s, %s)""",
        answers,
    )
    conn.commit()


def ingest_ure_responses(conn, df):
    print("Ingesting URE responses")
    responses = []
    answers = []

    cursor = conn.cursor()
    questions = _retrieve_questions(conn, 1)
    q = []

    for i, row in df.iterrows():
        # remove empty cells from dataframe
        if set(row.values) == {"NULL"}:
            break
        r = row[:96]
        if i == 0:
            q = r[2:].apply(lambda x: x.replace("\n", "").lower()).values
            _check_questions(questions, q)
            continue

        # insert response
        response_num = int(r[0].lower().replace(" ", "").replace("fakecase", ""))
        response = (response_num, int(r[1]), 1, response_num + 50)
        responses.append(response)

        # insert answers
        for i in range(len(r[2:])):
            ans = (questions[q[i]], response_num, r[i + 2])
            answers.append(ans)

    # --- INSERT INTO THE TABLE and commit changes
    cursor.executemany(
        """INSERT INTO response (Id, UserId, SurveyId, SurveyProfile, AnswerDate) VALUES (%s, %s, %s, %s, NOW())""",
        responses,
    )

    cursor.executemany(
        """INSERT INTO answers (QuestionId, ResponseId, AnswerValue) VALUES (%s, %s, %s)""",
        answers,
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
        r["Question"] = r["Question"].replace("\n", "")
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
    print("Ingesting criteria")
    values = []
    cursor = conn.cursor()

    for _, row in df.iterrows():
        r = tuple(row[["ID", "Characteristc", "Description", "Dimension"]].values)
        values.append(r)

    # --- INSERT INTO THE TABLE and commit changes
    cursor.executemany(
        """INSERT INTO criteria (CId, cName, cDescription, cCategory) VALUES (%s, %s, %s, %s)""",
        values,
    )
    conn.commit()


def ingest_desired_profiles(conn, df):
    print("Ingesting desired profiles")
    values = []
    cursor = conn.cursor()
    for _, row in df.iterrows():
        r = (row["Profile Id"], row["Profile Name"], "Desired")
        values.append(r)

    # --- INSERT INTO THE TABLE and commit changes
    cursor.executemany(
        """INSERT INTO profile (PId, PName, PType) VALUES (%s, %s, %s)""",
        values,
    )
    conn.commit()


def ingest_work_profiles(conn, df):
    print("Ingesting work profiles")
    values = []
    profile = []
    cursor = conn.cursor()
    criteria = {}

    cursor.execute("SELECT CId, cName FROM criteria;")
    result = cursor.fetchall()
    for r in result:
        criteria[r[1].lower().strip()] = r[0]
    # pprint(criteria)

    pid = 51
    for i, row in df.iterrows():
        if i == 0:
            continue
        if row["Items"] == "NULL":
            break
        r = (pid, row["Items"], "Experience")
        values.append(r)

        for _r in row.iteritems():
            c = _r[0]
            if c == "Items":
                continue
            c = criteria[c.lower().strip()]
            val = math.ceil(float(_r[1]))
            assert 0 <= val <= 7
            profile.append((c, pid, val))

        pid += 1

    # --- INSERT INTO THE TABLE and commit changes
    cursor.executemany(
        """INSERT INTO profile (PId, PName, PType) VALUES (%s, %s, %s)""",
        values,
    )
    cursor.executemany(
        """INSERT INTO profileCriteria (CId, PId, cValue, importanceRating) VALUES (%s, %s, %s, 4)""",
        profile,
    )
    conn.commit()


def ingest_accountProfiles(conn, df):
    print("Ingesting accountProfiles")
    values = []
    cursor = conn.cursor()
    for _, row in df.iterrows():
        r = tuple(row[["User", "Profile Id"]].values)
        values.append(r)

    # --- INSERT INTO THE TABLE and commit changes
    cursor.executemany(
        """INSERT INTO accountProfile (AId, PId) VALUES (%s, %s)""",
        values,
    )
    conn.commit()


def ingest_desired_profileCriteria(conn, df):
    print("Ingesting desiredProfiles")
    desiredProfiles = []
    cursor = conn.cursor()
    criterion = df.keys()[3:]

    counter = 1
    for criteria in criterion[0::2]:
        importance = criterion[counter]
        cursor.execute("SELECT CId FROM criteria WHERE cName = '{0}'".format(criteria))
        CId = cursor.fetchone()[0]

        for _, row in df.iterrows():
            r = tuple([CId, row["Profile Id"], row[criteria], row[importance]])
            desiredProfiles.append(r)

        counter += 2

    # --- INSERT INTO THE TABLE and commit changes
    cursor.executemany(
        """INSERT INTO profileCriteria (CId, PId, cValue, importanceRating) VALUES (%s, %s, %s, %s)""",
        desiredProfiles,
    )
    conn.commit()


def ingest_onet(conn, df):
    print("Ingesting ONet")
    values = []
    profiles = []
    cursor = conn.cursor()

    cursor.execute("select max(PId) FROM profile")
    PId = cursor.fetchone()[0]
    
    for _, row in df.iloc[1:].iterrows():
        PId += 1
        r = tuple([row["Code"], row["Occupation"], row["Occupation Types"], PId])
        p = tuple([PId, row["Occupation"], "ONET"])

        #r = tuple(row[["Code", "Occupation", "Occupation Types"]].values)
        profiles.append(p)
        values.append(r)

    cursor.executemany(
        """INSERT INTO profile (PId, PName, PType) VALUES (%s, %s, %s)""",
        profiles
    )
    # --- INSERT INTO THE TABLE and commit changes
    cursor.executemany(
        """INSERT INTO onet (ONetId, ONetJob, ONetDescription, ONetProfile) VALUES (%s, %s, %s, %s)""",
        values,
    )
    conn.commit()

def ingest_ONet_Profile_Critiera(conn, df):
    print("Ingesting ONet Job Criteria")

    values = []
    cursor = conn.cursor()

    for _, row in df.iterrows():
        r = tuple([row["CId"], row["PId"], math.ceil((float(row["cValue"]) / 100) * 7), row["importanceRating"]])
        values.append(r)

    cursor.executemany(
        """INSERT INTO profileCriteria (CId, PId, cValue, importanceRating) VALUES (%s, %s, %s, %s)""",
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


def drop_tables(conn, file_path=DIRPATH + "sql/CLEANUP.sql"):
    with open(file_path) as cleanup:
        drop = cleanup.read()
        cursor = conn.cursor()
        cursor.execute(drop)
    print("Dropped Tables")


def build_tables(conn, file_path=DIRPATH + "sql/SETUP.sql"):
    with open(file_path) as cleanup:
        tables = cleanup.read()
        cursor = conn.cursor()
        cursor.execute(tables)
    print("Built Tables")


if __name__ == "__main__":
    conn = MySQLdb.connect(host=HOST, port=PORT, user=USER, password=PASSWORD, database=DB)
    drop_tables(conn)
    build_tables(conn)

    sheets = ingest_data(
        DIRPATH + "data/info/Data-v03.xlsx",
    )

    workprefs = pd.read_csv(DIRPATH + "data/info/WorkPrefs.csv")
    profiles = pd.read_csv(DIRPATH + "data/info/profile.csv")
    questionAnswers = pd.read_csv(DIRPATH + "data/info/QuestionResponses.csv", keep_default_na=False)
    onet = pd.read_csv(DIRPATH + "data/info/All_STEM_Occupations.csv")
    onetProfileCriteria = pd.read_csv(DIRPATH + "data/info/OnetProfileCriteria.csv")

    ingest_desired_profiles(conn, workprefs)
    ingest_criteria(conn, profiles)
    ingest_desired_profileCriteria(conn, workprefs)
    ingest_users(conn, sheets["Users"])
    ingest_accountProfiles(conn, workprefs)
    ingest_work_profiles(conn, sheets["Work Profile"])
    ingest_surveys(conn, sheets["Surveys"])
    ingest_questions(conn, sheets["Survey Questions New"])
    ingest_question_answers(conn, questionAnswers)
    ingest_ure_responses(conn, sheets["URE Experience"])
    ingest_work_responses(conn, sheets["Work Experience"])
    ingest_onet(conn, onet)
    ingest_ONet_Profile_Critiera(conn, onetProfileCriteria)

    conn.close()
