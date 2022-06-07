from cmath import pi
from crypt import methods
import datetime
import MySQLdb
from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from flask_cors import CORS
import json
import os
from src import queries
import jwt
from dotenv import load_dotenv
from functools import wraps
from src.user import User
from src.matcher import match, getONetJobs, getVectorizedProfile, match_desired_onet, match_exp_onet

app = Flask(__name__)
CORS(app)

# Loads Enviroment Variables from .env file use command: 'touch .env' to create
load_dotenv()
# need to have the following variables in .env file by name
app.config['USER_SECRET'] = os.getenv('USER_SECRET')
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

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['USER_SECRET'])
        except:
            return jsonify({'message': 'Invalid token'}), 401
        return f(data, *args, kwargs)
    return decorated
        

@app.route("/")
def dbUsers():
    cur = mysql.connection.cursor()
    cur.execute("select user,host from mysql.user")
    rv = cur.fetchall()
    return str(rv)


@app.route("/profile", methods=['GET', 'POST', 'PATCH'])
#@token_required
def profile():
    conn = mysql.connect
    try:
        if request.method == 'GET':
            pid = request.args.get("pid", type=int)
            if pid == None:
                return {"Error": "pid not provided"}, 400

            return {
                "pid": pid, 
                "results": queries.retrieveProfileCriteria(conn, pid),
                }, 200
            #return getProfile(conn, pid)

        elif request.method == 'POST':
            aid = request.args.get("aid", type=int)
            if aid == None:
                return {"Error": "Profile POST requires an aid"}, 400
            return queries.addDesiredProfile(conn, aid, request.json)

        elif request.method == 'PATCH':
            pid = request.args.get("pid", type=int)
            if pid == None:
                return {"Error": "pid not provided"}, 400
            return queries.updateProfile(conn, pid, request.json)

        else:
            return "{0} not an implemented method".format(request.method)
    finally:
        conn.close()


@app.route("/profile/match", methods=['GET', 'POST'])
#@token_required
def profileMatch(pid=0):
    if request.method == 'GET':
        pid = request.args.get("pid", type=int)
        if pid == None:
            return {"Error": "pid not provided"}, 400
        return queries.getJobMatches(pid)
    elif request.method == 'POST':
        return queries.postJobMatches({"Profile": "Not Actual"})


@app.route("/profile/user", methods=['GET', 'POST'])
#@token_required
def userProfile():
    aid = request.args.get("aid", type=int)
    if aid == None:
            return {"Error": "aid not provided"}, 400
    if request.method == 'GET':
        return queries.getUserProfiles(aid)
    elif request.method == 'POST':
        #for getting matches with profile json templates
        return queries.postUserProfiles(aid, request.json)
    else:
        return "{0} not an implemented method".format(request.method)


@app.route("/profile/template")
#@token_required
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
#@token_required
def getJobs():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("select ONetId, ONetJob, ONetDescription from onet")
    return json.dumps({"jobs": cur.fetchall()})


@app.route("/surveys")
#@token_required
def getSurveys():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("select Id, ShortName, Name, Description from survey")
    return json.dumps({"surveys": cur.fetchall()})
    

@app.route("/survey")
#@token_required
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

    return queries.createSurvey(surveyQ, questionA)


@app.route("/match")
#@token_required
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
    return {"matches": matches}

@app.route("/users/signup", methods=["POST"])
def signup():
    if request.method == "POST":
        user = {}
        user['name'] = request.form['name']
        user['email'] = request.form['email']
        user['password'] = request.form['password']
        user['account_type'] = 'user'
        
        u = User()
        if u.check_user(user['email']):
            return {"Error": "User already exists"}, 500
        else:
            u.create_user(user)
            payload = {'name': user['name'],
                       'email': user['email'],
                       'account_type': user['account_type'],
                       'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)}
            token = jwt.encode(payload, app.config['USER_SECRET'])
            return jsonify({'token': token.decode('UTF-8')})


@app.route("/users/login", methods=["POST"])
def login():
    if request.method == "POST":
        user = {}
        user['email'] = request.form['email']
        user['password'] = request.form['password']
        
        u = User()
        if u.verify_user(user):
            payload = {'email': user['email'],
                       'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)}
            token = jwt.encode(payload, app.config['USER_SECRET'])
            return jsonify({'token': token.decode('UTF-8')})
        else:
            return {"Error": "User not found"}, 500

if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
