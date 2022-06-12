import pprint
import pandas as pd
import MySQLdb
import json
from src import matcher


def retrieveProfileCriteria(conn, pid):
    cur = conn.cursor(MySQLdb.cursors.DictCursor)
    try:
        cur.execute(
            f"SELECT profile.pid, ptype, pname, criteria.cName, criteria.cid, cvalue, importanceRating \
            FROM profile, profileCriteria, criteria \
            WHERE profileCriteria.PId = profile.PId AND profile.pid = {pid} AND criteria.cid = profileCriteria.cid\
            "
        )
        return json.dumps({"PId": pid, "Criteria": cur.fetchall()})
    finally:
        cur.close()


def getProfile(conn, pid):
    cur = conn.cursor(MySQLdb.cursors.DictCursor)
    try:
        cur.execute("select * from profile where pid=%(PId)s", {"PId": pid})
        pro = cur.fetchone()
        cur.execute(
            """
            select criteria.CId, cName, cValue, importanceRating from profileCriteria
            join criteria on criteria.CId = profileCriteria.CId
            where PId = %(PId)s;
            """,
            {"PId": pid},
        )

        criteria = cur.fetchall()
        return json.dumps(
            {
                "PId": pid,
                "PName": pro["PName"],
                "PType": pro["PType"],
                "Criteria": criteria,
            }
        )
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
            {"AId": aid, "PId": PId},
        )

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
    if "PName" not in keys:
        raise Exception("'PName' not included in the request", 400)
    if "PType" not in keys:
        raise Exception("'PType' not included in the request", 400)
    if "Criteria" not in keys:
        raise Exception("'Criteria' not included in the request", 400)

    def _0to7(value):
        if value > 7:
            return 7
        elif value < 0:
            return 0
        return value

    # Assuming Valid CId
    for c in body["Criteria"]:
        cKeys = c.keys()
        if (
            "cValue" not in cKeys
            or "CId" not in cKeys
            or "importanceRating" not in cKeys
        ):
            raise Exception(
                """
                'Criteria' must have json with 'CId', 'cValue', and 'importanceRating' keys
                """,
                400,
            )
        c["cValue"] = _0to7(c["cValue"])
        c["importanceRating"] = _0to7(c["importanceRating"])


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
            {"PId": PId, "PName": body["PName"], "PType": PType},
        )

        cur.executemany(
            """
            INSERT INTO profileCriteria (CId, PId, cValue, importanceRating) 
            VALUES (%(CId)s, {0}, %(cValue)s, %(importanceRating)s)
            """.format(
                int(PId)
            ),
            body["Criteria"],
        )

        # Intentionally doesn't commit leave it up to parent call
        return {
            "PId": int(PId),
            "Msg": "Successfully added profile {0}".format(PId),
        }, 201
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
            {"PId": pid, "PName": body["PName"]},
        )

        cur.executemany(
            """
            UPDATE profileCriteria 
            SET cValue = %(cValue)s, importanceRating = %(importanceRating)s
            WHERE PId = {0} AND CId = %(CId)s
            """.format(
                int(pid)
            ),
            body["Criteria"],
        )

        conn.commit()
        return {"Msg": "Successfully updated profile {0}".format(pid)}, 200
    except Exception as e:
        conn.rollback()
        return str(e), 500
    finally:
        cur.close()


def getJobMatches(conn, pid):

    try:
        cur = conn.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("select ONetId, ONetJob, ONetDescription from onet")

        matchedJobs = []
        matches = matcher.match(pid)
        for m in matches:
            onetId = m[0]
            for job in cur:
                if job["ONetId"] == onetId:
                    matchedJobs.append(job)

        return json.dumps({"PId": pid, "matches": matchedJobs})
    finally:
        cur.close()


def postJobMatches(conn, profileJson):
    try:
        cur = conn.cursor()
        checkProfileBody(profileJson)
        # matcher.vectorize(profileJson)
        return "matching based on json post not implemented"
    finally:
        cur.close()


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


def getUserProfiles(conn, aid):
    try:
        cur = conn.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(
            """SELECT AId, profile.PId as PId, PType, PName, AnswerDate as date
                FROM
                    ((select userId as AId, SurveyProfile as PId from response)
                UNION
                    (select * from accountProfile)) AS userProfiles
            JOIN profile on userProfiles.PId = profile.PId
            LEFT JOIN response on response.UserId = userProfiles.aid AND response.SurveyProfile = profile.PId
            where AId = %(AId)s
            """,
            {"AId": aid}
        )
        # where AId = {aid}
        data = cur.fetchall()
        
        for d in data:
            if d["date"]:
                d["date"] = d["date"].strftime("%d %B, %Y")

        return json.dumps({"AId": aid, "profiles": data})
    except:
        return "Error: Couldn't GET user Profiles"
    finally:
        cur.close()


def postUserProfiles(conn, aid, body):
    return json.dumps(body)


def getTemplate(conn):
    cur = conn.cursor(MySQLdb.cursors.DictCursor)
    try:
        cur.execute("select * from criteria")
        criterion = cur.fetchall()
        if criterion == None:
            return {"Error": "Couldn't connect to the DB"}, 500

        profileCriteria = []
        for c in criterion:
            cp = {
                "CId": c["CId"],
                "cName": c["cName"],
                "cValue": 0,
                "importanceRating": 4,
            }
            profileCriteria.append(cp)

        profileTemplate = {
            "PName": "Template",
            "PType": "Desired",
            "Criteria": profileCriteria,
        }
        return profileTemplate
    finally:
        cur.close()


def getSurvey(conn, sid):
    try:
        cur = conn.cursor()
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
    finally:
        cur.close()


def createQuestion(num, type, prompt, choices):
    qtype = ["dropdown", "matrix"]
    return {
        "name": str(num),
        "type": "dropdown",
        "title": prompt,
        "isRequired": True,
        "choices": choices,
    }


def getResponse(conn, aid):
    try:
        cur = conn.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("select * from response where UserId = %(AId)s", {"AId": aid})
        return json.dumps({"AId": aid, "Responses": cur.fetchall()})
    finally:
        cur.close()


def generateResponseProfile(conn, qMap):
    profile = getTemplate(conn)
    for c in profile["Criteria"]:
        cName = c["cName"]
        cValue = 0
        cnt = 0
        for q in qMap:
            # maybe check same with qMap[a]["qNum"] == a
            if q["ProfileCharacteristic"] == cName and "cValue" in q:
                cValue += q["cValue"]
                cnt += 1
        if cnt > 0:
            c["cValue"] = cValue / cnt

    return profile


def addResponse(conn, aid, body):

    # body = {"usedId": "123ABC", "SId": 1, "answers": {1: 10, 2: 1, 3: 3, 4: 3, 5: 2, 6: 1, 7: 2}}
    try:
        sid = body["SId"]
        cur = conn.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(
            """
            select Id as qNum, ProfileCharacteristic 
            from question 
            where SurveyId = %(SId)s
            """,
            {"SId": sid},
        )

        qMap = cur.fetchall()
        answers = body["answers"]

        for q in qMap:
            q["cValue"] = 0

        for key in answers:
            qNum = int(key)
            qMap[qNum]["cValue"] = answers[key]

        profile = generateResponseProfile(conn, qMap)
        pid = addProfile(conn, profile, "Experience")[0]["PId"]

        cur.execute("select max(Id + 1) as RId from response")
        rid = cur.fetchone()["RId"]

        cur.execute(
            """
        INSERT INTO response (Id, UserId, SurveyId, SurveyProfile, AnswerDate) 
        VALUES (%(RId)s, %(AId)s, %(SId)s, %(PId)s, NOW())
        """,
            {"RId": rid, "AId": aid, "SId": sid, "PId": pid},
        )

        cur.executemany(
            """
        INSERT INTO answers (QuestionId, ResponseId, AnswerValue) 
        VALUES (%(qNum)s, {0}, %(cValue)s)
        """.format(
                rid
            ),
            qMap,
        )

        conn.commit()
        return {"Msg": "Successfully added survey response"}, 201

    except MySQLdb.DatabaseError as e:
        conn.rollback()
        return str(e), 500
    finally:
        cur.close()
