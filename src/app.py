from cmath import pi
import MySQLdb
from utils.sqlconnect import get_connector
from flask import Flask, request
from flask_mysqldb import MySQL
from flask_cors import CORS
import json
import os
from dotenv import load_dotenv

from matcher import match, getONetJobs, getProfile, match_desired_onet, match_exp_onet

app = Flask(__name__)
CORS(app)

# Loads Enviroment Variables from .env file use command: 'touch .env' to create
load_dotenv()
# need to have the following variables in .env file by name
USER = os.getenv("MYSQL_USER")
PASSWORD = os.getenv("PASSWORD")
PORT = int(os.getenv("PORT"))
DB = os.getenv("MYSQL_DB")
HOST = os.getenv("MYSQL_HOST")

app.config.setdefault("MYSQL_HOST", HOST)
app.config.setdefault("MYSQL_USER", USER)
app.config.setdefault("MYSQL_PASSWORD", PASSWORD)
app.config.setdefault("MYSQL_DB", DB)
app.config.setdefault("MYSQL_PORT", PORT)
app.config.setdefault("MYSQL_UNIX_SOCKET", None)
app.config.setdefault("MYSQL_CONNECT_TIMEOUT", 10)
app.config.setdefault("MYSQL_READ_DEFAULT_FILE", None)
app.config.setdefault("MYSQL_USE_UNICODE", True)
app.config.setdefault("MYSQL_CHARSET", "utf8")
app.config.setdefault("MYSQL_SQL_MODE", None)
app.config.setdefault("MYSQL_CURSORCLASS", None)
app.config.setdefault("MYSQL_AUTOCOMMIT", False)
app.config.setdefault("MYSQL_CUSTOM_OPTIONS", None)

mysql = MySQL(app)


@app.route("/")
def dbUsers():
    cur = mysql.connection.cursor()
    cur.execute("select user,host from mysql.user")
    rv = cur.fetchall()
    return str(rv)


# Note use https://www.onetonline.org/link/summary/<job code to link to job page>
@app.route("/match/profile")
def getJobMatches(pid=0):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    pid = request.args.get("id", type=int)

    cur.execute("select ONetId, ONetJob, ONetDescription from onet")

    matchedJobs = []
    matches = match(pid)
    for m in matches:
        onetId = m[0]
        for job in cur:
            if job["ONetId"] == onetId:
                matchedJobs.append(job)

    return json.dumps({"PId": pid, "matches": matchedJobs})


@app.route("/user/<aid>/profiles")
def getUserProfile(aid=0):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(
        """
        select * from 
        ((select userId as AId, SurveyProfile as PId from response)
        union
        (select * from accountProfile)) AS userProfiles
        join profile on userProfiles.PId = profile.PId 
        where AId = %(AId)s
        """,
        {"AId": int(aid)},
    )
    return json.dumps({"jobs": cur.fetchall()})


@app.route("/jobs")
def getJobs():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("select ONetId, ONetJob, ONetDescription from onet")
    return json.dumps({"jobs": cur.fetchall()})


@app.route("/surveys")
def getSurveys():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("select Id, ShortName, Name, Description from survey")
    return json.dumps({"surveys": cur.fetchall()})


@app.route("/survey")
def getSurvey():
    cur = mysql.connection.cursor()
    sid = request.args.get("id", type=int)

    cur.execute(
        """
        select q.SurveyId, ShortName, q.Id as QNum, Question, QuestionType
        from survey as s 
        join question as q on s.Id = SurveyId 
        where s.Id = %(sid)s
        """,
        {"sid": sid},
    )
    surveyQ = cur.fetchall()

    cur.execute(
        """select * from questionAcceptableAnswer where SurveyId = %(sid)s order by QuestionId""",
        {"sid": sid},
    )
    questionA = cur.fetchall()

    return createSurvey(surveyQ, questionA)


@app.route("/match")
def getMatch():
    cur = mysql.connection.cursor()
    profile_id = request.json.get("profileId")

    if profile_id is None:
        return {"Error": "ProfileId not provided"}, 500

    profile, survey = getProfile(cur, profile_id=profile_id)
    if profile is None:
        return {"Error": "ProfileId not Found"}, 500
    onet = getONetJobs(cur)
    if onet is None:
        return {"Error": "Internal Error, ONet jobs not found"}, 500

    matches = match_exp_onet(profile, onet)
    print(matches)
    return {"matches": matches}


def createSurvey(surveyQ, questionA):
    json_data = {"surveyId": surveyQ[0][0], "surveyName": surveyQ[0][1], "elements": []}
    i = 0
    questionALen = len(questionA)
    for q in surveyQ:
        # surveyQ of tuple (SId, Name, Number, prompt, type)
        qNum = q[2]
        type = q[4]
        prompt = q[3]

        choices = []
        # questionA of tuple (SurveyId, QNum, AValue, AText, comment)
        while i < questionALen and questionA[i][1] == qNum:
            qA = questionA[i]
            choices.append({"value": int(qA[2]), "text": qA[3]})
            i += 1

        r = createQuestion(qNum, type, prompt, choices)
        json_data["elements"].append(r)
    return json.dumps(json_data)


def createQuestion(num, type, prompt, choices):
    qtype = ["dropdown", "matrix"]
    if type == 1:
        return {
            "name": str(num),
            "type": qtype[type],
            "title": prompt,
            "isRequired": True,
            "columns": choices,
            "rows": [{"value": "", "text": ""}],
        }
    else:
        return {
            "name": str(num),
            "type": qtype[type],
            "title": prompt,
            "isRequired": True,
            "choices": choices,
        }


if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
