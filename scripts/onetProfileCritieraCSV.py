import pandas as pd
import MySQLdb
import os
import glob
from dotenv import load_dotenv

# Loads Enviroment Variables from .env file use command: 'touch .env' to create
load_dotenv()

# PORT for MYSQL
PORT = int(os.getenv("PORT"))
# Either Absolute path to dir, relative path, or nothing
DIRPATH = os.getenv("DIRPATH")
DB = os.getenv("MYSQL_DB")

def creatONetProfileCriteriaCSV(conn):
    print("Ingesting ONet Job Criteria")

    criteria = []
    values = []
    cursor = conn.cursor()
    jobs = conn.cursor()

    for file in glob.glob(DIRPATH + "data/criteria/*.csv"):
        fn = file.split("+")[1]
        criteria.append(fn)

    criteria = list(set(criteria))
    jobs.execute("select ONetId, ONetJob, ONetProfile from onet")

    for c in criteria:
        cName = " ".join(c.split(" (")[0].split("-"))
        print("Ingesting " + cName)
        cursor.execute("SELECT CId FROM criteria WHERE cName = '{0}'".format(cName))
        CId = cursor.fetchone()[0]
        csvFiles = glob.glob(DIRPATH + "data/criteria/+{0}+*.csv".format(c))
        numFiles = len(csvFiles)
        for job in jobs:
            val = 0
            jobC = job[0]
            jobP = job[2]

            for file in csvFiles:
                df = pd.read_csv(file)
                rows = df.iterrows()
                for _, row in rows:
                    if (row["Code"] == jobC):
                        val += int(row[0])
                        
            r = tuple([CId, jobP, val / numFiles, 4])
            values.append(r)

    List_rows = values
    List_columns = ['CId','PId', 'cValue', 'importanceRating']
    df = pd.DataFrame(List_rows)
    df.to_csv('OnetProfileCriteria.csv', index=False, header=List_columns)

    print("ONet Job Criteria done")

#MUST have tables built for this to work
if __name__ == "__main__":
    conn = MySQLdb.connect(host="127.0.0.1", port=PORT, user="root", database=DB)

    creatONetProfileCriteriaCSV(conn)

    conn.close()
