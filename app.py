from flask import Flask
from flask_mysqldb import MySQL
from flask_cors import CORS
import json
import os
from dotenv import load_dotenv

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

app.config.setdefault("MYSQL_HOST", "localhost")
app.config.setdefault("MYSQL_USER", USER)
app.config.setdefault("MYSQL_PASSWORD", PASSWORD)
app.config.setdefault("MYSQL_DB", DB )
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

@app.route("/survey/URE")
def getSurvey():
    cur = mysql.connection.cursor()

    cur.execute(
        """
        select q.SurveyId, ShortName, q.Id as QNum, Question, QuestionType
        from survey as s 
        join question as q on s.Id = SurveyId 
        where s.ShortName = "URE Experience"
        """)

    #row_headers = [x[0] for x in cur.description]
    rv = cur.fetchall()

    json_data = {"SurveyId" : rv[0][0], "SurveyName" : rv[0][1], "Questions": []}

    for q in rv:
        r = {"QNum": q[2], "QType": q[4], "Question" : q[3]}
        print(r)
        json_data["Questions"].append(r)
    #for result in rv:
    #    json_data.append(dict(zip(row_headers,result)))
    return json.dumps(json_data)

if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
