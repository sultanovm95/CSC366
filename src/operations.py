def _delete_experience(conn, user_id, profile_id):
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT account.id, response.id \
            FROM account, response, profile \
            WHERE response.userid=account.id AND profile.pid=surveyProfile AND \
            profile.pid={profile_id};"
            # and account.id={user_id}
    )
    exists = cursor.fetchall()
    print(exists)

    if len(exists) != 0:
        response_id = exists[0][1]

        cursor.execute(f"DELETE FROM answers WHERE responseId={response_id}")
        cursor.execute(f"DELETE FROM response WHERE id={response_id}")
        cursor.execute(f"DELETE FROM profileCriteria WHERE profileCriteria.pid={profile_id}")
        cursor.execute(f"DELETE FROM profile WHERE profile.pid={profile_id}")
        conn.commit()
        return {"deleted": profile_id}
    return {"Error": "User does not own profile id"}


def _delete_desired(conn, user_id, profile_id):
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT * FROM accountProfile WHERE aid={user_id} and pid={profile_id};"
    )
    exists = cursor.fetchall()
    print(exists)
    exists = ((1, 1))

    if len(exists) != 0:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM profileCriteria WHERE profileCriteria.pid={profile_id}")
        cursor.execute(f"DELETE FROM accountProfile WHERE pid={profile_id}")
        cursor.execute(f"DELETE FROM response WHERE surveyProfile={profile_id}")
        cursor.execute(f"DELETE FROM profile WHERE profile.pid={profile_id}")
        conn.commit()
        return {"deleted": profile_id}
    return {"Error": "User does not own profile id"}

def delete_profile(conn, user_id, profile_id):
    cursor = conn.cursor()
    
    cursor.execute(
        f"SELECT ptype FROM profile WHERE pid={profile_id}"
    )
    result = cursor.fetchall()

    if len(result) != 0:
        if result[0][0].lower() == "experience":
            return _delete_experience(conn, user_id, profile_id)
        elif result[0][0].lower() == "desired":
            return _delete_desired(conn, user_id, profile_id)
    return {"Error": "Profile Id not found"}
    
