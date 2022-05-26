import MySQLdb
import os
from dotenv import load_dotenv

# Loads Enviroment Variables from .env file use command: 'touch .env' to create
load_dotenv()

# PORT for MYSQL
PORT = int(os.getenv("PORT"))
# Either Absolute path to dir, relative path, or nothing
DIRPATH = os.getenv("DIRPATH")
DB = os.getenv("MYSQL_DB")


def get_connector():
    conn = MySQLdb.connect(host="127.0.0.1", port=PORT, user="root", database=DB)
    return conn
