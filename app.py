from flask import Flask
from flask_mysqldb import MySQL
import os
from dotenv import load_dotenv


app = Flask(__name__)
mysql = MySQL(app)

app = Flask(__name__)


# Loads Enviroment Variables from .env file use command: 'touch .env' to create
load_dotenv()
# need to have the following variables in .env file by name
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
PORT = int(os.getenv("PORT"))
DB = os.getenv("MYSQL_DB")

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


@app.route("/")
def dbUsers():
    cur = mysql.connection.cursor()
    cur.execute("select user,host from mysql.user")
    rv = cur.fetchall()
    return str(rv)


if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
