from cmath import pi
from crypt import methods
import MySQLdb
from utils.sqlconnect import get_connector
from flask import Flask, request
from flask_mysqldb import MySQL
from flask_cors import CORS
import json
import os
from dotenv import load_dotenv

from matcher import match, getONetJobs, getVectorizedProfile, match_desired_onet, match_exp_onet

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


@app.route("/profile", methods=['GET', 'POST'])
def profile():
    if request.method == 'GET':
        pid = request.args.get("pid", type=int)
        if pid == None:
            return {"Error": "pid not provided"}, 400

        return getProfile(pid)
    elif request.method == 'POST':
        return addProfile()
    else:
        return "{0} not an implemented method".format(request.method)

def getProfile(pid):
    cur = mysql.connect.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("select * from profile where %(PId)s", {"PId": pid})
    pro = cur.fetchone()

    cur.execute(
        """
        select criteria.CId, cName, cValue, importanceRating from profileCriteria
        join criteria on criteria.CId = profileCriteria.CId
        where PId = %(PId)s;
        """, 
        {"PId": pid})
    return json.dumps({"PId": pid, "PName": pro["PName"], "Criteria": cur.fetchall()})

def addProfile():
    return "Add profile not implemented yet"    


@app.route("/profile/match", methods=['GET', 'POST'])
def profileMatch(pid=0):
    if request.method == 'GET':
        pid = request.args.get("pid", type=int)
        if pid == None:
            return {"Error": "pid not provided"}, 400
        return getJobMatches(pid)
    elif request.method == 'POST':
        return postJobMatches({"Profile": "Not Actual"})

def getJobMatches(pid):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("select ONetId, ONetJob, ONetDescription from onet")

    matchedJobs = []
    matches = match(pid)
    for m in matches:
        onetId = m[0]
        for job in cur:
            if job["ONetId"] == onetId:
                matchedJobs.append(job)

    return json.dumps({"PId": pid, "matches": matchedJobs})

def postJobMatches(profileJson):
    return "matching based on json post not implemented"

@app.route("/profile/user", methods=['GET', 'POST'])
def userProfile():
    aid = request.args.get("aid", type=int)
    if aid == None:
            return {"Error": "aid not provided"}, 400
    if request.method == 'GET':
        return getUserProfiles(aid)
    elif request.method == 'POST':
        return postUserProfiles(aid)
    else:
        return "{0} not an implemented method".format(request.method)

def getUserProfiles(aid):
    try:
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
            {"AId": aid},
        )
        return json.dumps({"profiles": cur.fetchall()})
    except:
        return "Error: Couldn't GET user Profiles"

def postUserProfiles(aid):
    return "user Profile POST not implemente yet"


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


@app.route("/match")
def getMatch():
    cur = mysql.connection.cursor()
    profile_id = request.json.get("profileId")

    if profile_id is None:
        return {"Error": "ProfileId not provided"}, 500

    profile, survey = getVectorizedProfile(cur, profile_id=profile_id)
    if profile is None:
        return {"Error": "ProfileId not Found"}, 500
    onet = getONetJobs(cur)
    if onet is None:
        return {"Error": "Internal Error, ONet jobs not found"}, 500

    matches = match_exp_onet(profile, onet)
    print(matches)
    return json.dumps({"matches": matches})
    

@app.route("/survey")
def getSurvey():
    cur = mysql.connection.cursor()
    sid = request.args.get("id", type=int)
    if sid == None:
            return {"Error": "survey id not provided"}, 400

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
