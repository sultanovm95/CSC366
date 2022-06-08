import datetime
import MySQLdb
from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from flask_cors import CORS
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import os
import jwt
from src import operations, queries
from dotenv import load_dotenv
from functools import wraps
from src.user import User
from src.matcher import (
    match,
    getONetJobs,
    getVectorizedProfile,
    match_desired_onet,
    match_exp_onet,
)

app = Flask(__name__)
CORS(app)

# Loads Enviroment Variables from .env file use command: 'touch .env' to create
load_dotenv()
# need to have the following variables in .env file by name
app.config["USER_SECRET"] = os.getenv("USER_SECRET")
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
        token = request.args.get("token")
        if not token:
            return jsonify({"message": "Token is missing!"}), 401
        try:
            data = jwt.decode(token, app.config["USER_SECRET"])
        except:
            return jsonify({"message": "Invalid token"}), 401
        return f(data, *args, kwargs)

    return decorated


@app.route("/")
def dbUsers():
    cur = mysql.connection.cursor()
    cur.execute("select user,host from mysql.user")
    rv = cur.fetchall()
    return str(rv)


@app.route("/criteria_values")
def getCriteriaValues():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(
        "select CId,cName,cDescription,4 as cValue,4 as importanceRating from criteria"
    )
    return json.dumps({"criteria": cur.fetchall()})


@app.route("/profile", methods=["GET", "POST", "PATCH"])
@token_required
def profile():
    conn = mysql.connect
    try:
        if request.method == "GET":
            pid = request.args.get("pid", type=int)
            if pid == None:
                return {"Error": "pid not provided"}, 400

            return queries.getProfile(conn, pid), 200
            # return getProfile(conn, pid)

        elif request.method == "POST":
            aid = request.args.get("aid", type=int)
            if aid == None:
                return {"Error": "Profile POST requires an aid"}, 400
            return queries.addDesiredProfile(conn, aid, request.json)

        elif request.method == "PATCH":
            pid = request.args.get("pid", type=int)
            if pid == None:
                return {"Error": "pid not provided"}, 400
            return queries.updateProfile(conn, pid, request.json)

        else:
            return "{0} not an implemented method".format(request.method)
    finally:
        conn.close()


@app.route("/profile/match", methods=["GET", "POST"])
@token_required
def profileMatch(pid=0):

    conn = mysql.connect
    try:
        if request.method == "GET":
            pid = request.args.get("pid", type=int)
            if pid == None:
                return {"Error": "pid not provided"}, 400
            return queries.getJobMatches(conn, pid)
        elif request.method == "POST":
            return queries.postJobMatches(conn, {"Profile": "Not Actual"})
    finally:
        conn.close()


@app.route("/profile/user", methods=["GET", "POST"])
@token_required
def userProfile():
    conn = mysql.connect
    try:
        aid = request.args.get("aid", type=int)
        if aid == None:
            return {"Error": "aid not provided"}, 400
        if request.method == "GET":
            return queries.getUserProfiles(conn, aid)
        elif request.method == "POST":
            # for getting matches with profile json templates
            return queries.postUserProfiles(conn, aid, request.json)
        else:
            return "{0} not an implemented method".format(request.method)
    except Exception as e:
        return str(e), 500
    finally:
        conn.close()


@app.route("/profile/template")
@token_required
def profileTemplate():
    conn = mysql.connect
    try:
        if request.method == "GET":
            return json.dumps(queries.getTemplate(conn))
    except Exception as e:
        return str(e), 500
    finally:
        conn.close()


@app.route("/jobs")
# @token_required
def getJobs():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("select ONetId, ONetJob, ONetDescription from onet")
    return json.dumps({"jobs": cur.fetchall()})


@app.route("/surveys")
@token_required
def getSurveys():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("select Id, ShortName, Name, Description from survey")
    return json.dumps({"surveys": cur.fetchall()})


@app.route("/survey")
@token_required
def survey():
    conn = mysql.connect
    try:
        if request.method == "GET":
            sid = request.args.get("sid", type=int)
            if sid == None:
                return {"Error": "survey sid not provided"}, 400
            return queries.getSurvey(conn, sid)
        else:
            return "{0} not an implemented method".format(request.method)
    except Exception as e:
        return str(e), 500
    finally:
        conn.close()


@app.route("/response", methods=["GET", "POST"])
@token_required
def response():
    conn = mysql.connect
    try:
        aid = request.args.get("aid", type=int)
        if aid == None:
            return {"Error": "Account aid not provided"}, 400
        if request.method == "GET":
            return queries.getResponse(conn, aid)
        elif request.method == "POST":
            body = request.json
            if body == None:
                return {"Error": "No response payload sent"}, 400
            return queries.addResponse(conn, aid, body)
    except MySQLdb.DatabaseError as e:
        return str(e), 500
    finally:
        conn.close()


@app.route("/match")
@token_required
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
        user["name"] = request.json["firstName"] + " " + request.json["lastName"]
        user["email"] = request.json["email"]
        user["password"] = request.json["password"]
        user["account_type"] = "user"

        u = User()
        if u.check_user(user):
            return {"Error": "User already exists"}, 500
        else:
            u.create_user(user)
            payload = {
                "name": user["name"],
                "email": user["email"],
                "account_type": user["account_type"],
                "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),
            }
            token = jwt.encode(payload, app.config["USER_SECRET"])
            return jsonify({"token": token.decode("UTF-8")}), 201


@app.route("/users/login", methods=["POST"])
def login():
    if request.method == "POST":
        user = {}
        user["email"] = request.form["email"]
        user["password"] = request.form["password"]

        u = User()
        if u.verify_user(user):
            payload = {
                "email": user["email"],
                "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),
            }
            token = jwt.encode(payload, app.config["USER_SECRET"])
            return jsonify({"token": token.decode("UTF-8")})
        else:
            return {"Error": "User not found"}, 500

@app.route("/delete", methods=["POST"])
# @jwt_required()
def delete():
    if request.method == "POST":
        curr_user = 1
        # curr_user = get_jwt_identity()
        profile_id = request.json.get("pid")

        if profile_id:
            result = operations.delete_profile(mysql.connection, curr_user, profile_id=profile_id)

            if result == -1:
                return {"Error": "UserId doesn't own profileId"}

            return {"delete": profile_id}
        return {"Error", "ProfileId not found"}, 500
    return {"Error": "Post request only"}, 500

if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
