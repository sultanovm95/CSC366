import pandas as pd


def retrieveProfileCriteria(conn, pid):
    cur = conn.cursor()
    cur.execute(
        f"SELECT profile.pid, ptype, pname, criteria.cName, criteria.cid, cvalue, importanceRating \
            FROM profile, profileCriteria, criteria \
            WHERE profileCriteria.PId = profile.PId AND profile.pid = {pid} AND criteria.cid = profileCriteria.cid\
            "
    )
    result = cur.fetchall()
    df = pd.DataFrame(
        result,
        columns=[
            "ProfileId",
            "Type",
            "Name",
            "Criteria",
            "CriteriaId",
            "Value",
            "Importance",
        ],
    )

    print(df.to_dict(orient="records"))
    return df.to_dict(orient="records")
