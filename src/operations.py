import profile


def delete_profile(conn, user_id, profile_id):
    cursor = conn.cursor()

    cursor.execute(
        f"SELECT account.id, response.surveyProfile, profile.pid \
            FROM account, response, profile \
            WHERE response.userid=account.id AND profile.pid=surveyProfile AND \
            account.id={user_id} and profile.pid={profile_id};"
    )
    
    exists = cursor.fetchall()
    print(exists)
    if len(exists) != 0:
        return profile_id
    return -1
