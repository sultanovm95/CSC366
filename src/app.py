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


@app.route("/profile", methods=['GET', 'POST', 'PATCH'])
def profile():
    conn = mysql.connect

    try:
        if request.method == 'GET':
            pid = request.args.get("pid", type=int)
            if pid == None:
                return {"Error": "pid not provided"}, 400
            return getProfile(conn, pid)

        elif request.method == 'POST':
            aid = request.args.get("aid", type=int)
            if aid == None:
                return {"Error": "Profile POST requires an aid"}, 400
            return addDesiredProfile(conn, aid, request.json)

        elif request.method == 'PATCH':
            pid = request.args.get("pid", type=int)
            if pid == None:
                return {"Error": "pid not provided"}, 400
            return updateProfile(conn, pid, request.json)

        else:
            return "{0} not an implemented method".format(request.method)
    finally:
        conn.close()

def getProfile(conn, pid):
    cur = conn.cursor(MySQLdb.cursors.DictCursor)
    try:
        cur.execute("select * from profile where %(PId)s", {"PId": pid})
        pro = cur.fetchone()
        cur.execute(
            """
            select criteria.CId, cName, cValue, importanceRating from profileCriteria
            join criteria on criteria.CId = profileCriteria.CId
            where PId = %(PId)s;
            """, 
            {"PId": pid})

        criteria = cur.fetchall()
        return json.dumps({"PId": pid, "PName": pro["PName"], "Criteria": criteria})
    finally:
        cur.close()

def addDesiredProfile(conn, aid, body):
    try:
        result = addProfile(conn, body, "Desired")
        PId = int(result[0]["PId"])
        cur = conn.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(
            """
            INSERT INTO accountProfile (AId, PId) VALUES (%(AId)s, %(PId)s)
            """,
        {"AId": aid, "PId": PId})

        conn.commit()
        cur.close()
        return result
    except MySQLdb.DatabaseError as e:
        conn.rollback()
        return str(e), 500
    except Exception as e:
        conn.rollback()
        return e.args[0], e.args[1]

def checkProfileBody(body):
    keys = body.keys()
    if 'PName' not in keys:
        raise Exception("'PName' not included in the request", 400)
    if 'PType' not in keys:
        raise Exception("'PType' not included in the request", 400)
    if 'Criteria' not in keys:
        raise Exception("'Criteria' not included in the request", 400)

def addProfile(conn, body, PType):
    cur = conn.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("select max(PId) + 1 as PId from profile")
    r = cur.fetchone()
    PId = r["PId"]
    
    try:
        if PId == None:
            raise Exception("DB couldn't generate a PId", 500)
        
        checkProfileBody(body)
        
        cur.execute(
            """
            INSERT INTO profile (PId, PName, PType) VALUES (%(PId)s, %(PName)s, %(PType)s)
            """, 
            {"PId": PId, "PName": body["PName"], "PType": PType})

        cur.executemany(
            """
            INSERT INTO profileCriteria (CId, PId, cValue, importanceRating) 
            VALUES (%(CId)s, {0}, %(cValue)s, %(importanceRating)s)
            """.format(int(PId))
        , body["Criteria"])

        #Intentionally doesn't commit leave it up to parent call
        return {"PId": int(PId), "Msg": "Successfully added profile {0}".format(PId)}, 201
    except MySQLdb.DatabaseError as e:
        conn.rollback()
        return str(e), 500
    finally:
        cur.close()

def updateProfile(conn, pid, body):

    checkProfileBody(body)

    if body["PType"] != "Desired":
        raise Exception("You can only update desired profiles", 400)
    
    try:
        cur = conn.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(
            """
            UPDATE profile
            SET PName = %(PName)s
            WHERE PId = %(PId)s
            """, 
            {"PId": pid, "PName": body["PName"]})

        cur.executemany(
            """
            UPDATE profileCriteria 
            SET cValue = %(cValue)s, importanceRating = %(importanceRating)s
            WHERE PId = {0} AND CId = %(CId)s
            """.format(int(pid)), 
            body["Criteria"])

        conn.commit()
        return {"Msg": "Successfully updated profile {0}".format(pid)}, 200
    except Exception as e:
        conn.rollback()
        return str(e), 500
    finally:
        cur.close()


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
        #for getting matches with profile json templates
        return postUserProfiles(aid, request.json)
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

def postUserProfiles(aid, body):
    return json.dumps(body)

@app.route("/profile/template")
def getTemplate():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("select * from criteria")
    criterion = cur.fetchall()

    if criterion == None:
        return {"Error": "Couldn't connect to the DB"}, 500

    profileCriteria = []
    for c in criterion:
        cp = {"CId": c["CId"],"cName": c["cName"], "cValue": 0, "importanceRating": 0}
        profileCriteria.append(cp)

    profileTemplate = {"PName": "Template", "PType": "Desired","Criteria": profileCriteria}
    return json.dumps(profileTemplate)


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
