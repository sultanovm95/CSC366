from flask import Flask, request
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

@app.route("/survey")
def getSurvey():
    cur = mysql.connection.cursor()
    sid = request.args.get('id', type = int)

    cur.execute(
        """
        select q.SurveyId, ShortName, q.Id as QNum, Question, QuestionType
        from survey as s 
        join question as q on s.Id = SurveyId 
        where s.Id = %(sid)s
        """, 
        {'sid': sid})
    surveyQ = cur.fetchall()

    cur.execute(
        """select * from questionAcceptableAnswer where SurveyId = %(sid)s order by QuestionId""", 
        {'sid': sid})
    questionA = cur.fetchall()

    return createSurvey(surveyQ, questionA)

def createSurvey(surveyQ, questionA):
    json_data = {"surveyId" : surveyQ[0][0], "surveyName" : surveyQ[0][1], "elements": []}
    i = 0
    questionALen = len(questionA)
    for q in surveyQ:
        #surveyQ of tuple (SId, Name, Number, prompt, type)
        qNum = q[2]
        type = q[4]
        prompt = q[3]

        choices = [] 
        #questionA of tuple (SurveyId, QNum, AValue, AText, comment)
        while i < questionALen and questionA[i][1] == qNum:
            qA = questionA[i]
            choices.append({"value": int(qA[2]), "text": qA[3]})
            i += 1
        
        r = createQuestion(qNum, type, prompt, choices)
        json_data["elements"].append(r)
    return json.dumps(json_data)

def createQuestion(num, type, prompt, choices):
    qtype = ["dropdown", "matrix"]
    if(type == 1):
        return {"name": str(num), "type": qtype[type], "title" : prompt, "isRequired" : True, 
                "columns": choices, "rows": [{"value": "", "text": ""}]}
    else:
        return {"name": str(num), "type": qtype[type], "title" : prompt, "isRequired" : True,
                "choices": choices}
    
if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
