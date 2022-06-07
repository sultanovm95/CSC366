import pandas as pd
import numpy as np
from src.utils.sqlconnect import get_connector

def _cossim(s, w):
    size = max(len(s), len(w))
    s = _reshape_vector(s, size)
    w = _reshape_vector(w, size)

    return np.sum(s * w) / (np.sqrt(np.sum(s * s)) * np.sqrt(np.sum(w * w)))


def _pearson(s, w):
    size = max(len(s), len(w))
    s = _reshape_vector(s, size)
    w = _reshape_vector(w, size)

    _s_mean = np.mean(s)
    _w_mean = np.mean(w)
    return np.sum((s - _s_mean) * (w - _w_mean)) / (
        np.sqrt(np.square(np.sum(s - _s_mean)))
        * np.sqrt(np.square(np.sum(w - _w_mean)))
    )


def _weightcos(s, v, w):
    size = max(len(s), len(w))
    s = _reshape_vector(s, size)
    w = _reshape_vector(w, size)

    return np.sum(s * v * w) / (
        np.sqrt(np.sum(np.square(s))) * np.sqrt(np.sum(np.square(w))) * np.sum(v)
    )


def _reshape_vector(v, size):
    return np.resize(np.array(v), size)


def getVectorizedProfile(cursor, profile_id):
    cursor.execute(
        f"SELECT Id, UserId, SurveyId, SurveyProfile, PType, CId, cValue, ImportanceRating \
            FROM response, profile, profileCriteria \
            WHERE response.SurveyProfile = profile.PId AND profile.PId = profileCriteria.PId AND profile.PId = {profile_id}\
            ORDER BY ID, CId; \
        "
    )
    result = cursor.fetchall()

    df = pd.DataFrame(
        result,
        columns=[
            "Id",
            "UserId",
            "SurveyId",
            "SurveyPofile",
            "ProfileType",
            "CId",
            "CValue",
            "ImportanceRating",
        ],
    )

    group = df.groupby("Id")
    profile = group.get_group((list(group.groups)[0]))

    if len(group) != 1:
        return None, None
    return vectorize(profile.reset_index()), profile["SurveyId"]


def getONetJobs(cursor):
    cursor.execute(
        "SELECT ONetId, ONetJob, ONetProfile, CId, CValue, ImportanceRating FROM onet, profile, profileCriteria WHERE onet.ONetProfile = profile.PId AND profile.PId = profileCriteria.PId;"
    )
    onet = cursor.fetchall()
    onet_df = pd.DataFrame(
        onet,
        columns=[
            "ONetId",
            "ONetJob",
            "ONetProfile",
            "CId",
            "CValue",
            "ImportanceRating",
        ],
    )

    group = onet_df.groupby("ONetId")

    if len(group) == 0:
        return None

    onet_profile = {}
    for i, g in group:
        onet_profile[i] = vectorize(g.reset_index())
    return onet_profile


def vectorize(group):
    data = group[["CId", "CValue", "ImportanceRating"]]
    max_cid = data["CId"].max()

    values = np.zeros(shape=max_cid)
    importances = np.ones(shape=max_cid) * 4

    for i, vals in data.iterrows():
        values[i] = vals["CValue"]
        importances[i] = vals["ImportanceRating"]

    np.nan_to_num(values, copy=False)
    np.nan_to_num(importances, copy=False, nan=4)

    return values, importances


def match_jobs(index, job, other_jobs, limit=10):
    results = []
    values, importance = job

    for i in other_jobs:
        if i == index:
            continue
        _vals, _importance = other_jobs[i]
        results.append((i, _cossim(values, _vals)))
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:limit]


def match_desired_onet(job, onet_jobs, limit=10):
    results = []
    values, importance = job

    for i in onet_jobs:
        _vals, _ = onet_jobs[i]
        results.append((i, _weightcos(values, importance, _vals)))
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:limit]


def match_exp_onet(job, onet_jobs, limit=10):
    results = []
    values, importance = job

    for i in onet_jobs:
        _vals, _importance = onet_jobs[i]
        results.append((i, _cossim(values, _vals)))
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:limit]


def match(pid):
    conn = get_connector()
    cursor = conn.cursor()

    cursor.execute(
        """
        select profile.PId, PType, PName, CId, cValue, importanceRating 
        from profile join profileCriteria on profileCriteria.PId = profile.PId
        where profile.PId = %(pid)s; 
        """,
        {"pid": pid},
    )
    result = cursor.fetchall()
    df = pd.DataFrame(
        result,
        columns=[
            "PId",
            "ProfileType",
            "PName",
            "CId",
            "CValue",
            "ImportanceRating",
        ],
    )

    cursor.execute(
        """
        SELECT ONetId, ONetJob, ONetProfile, CId, CValue, ImportanceRating 
        FROM onet, profile, profileCriteria 
        WHERE onet.ONetProfile = profile.PId AND profile.PId = profileCriteria.PId;
        """
    )
    onet = cursor.fetchall()
    onet_df = pd.DataFrame(
        onet,
        columns=[
            "ONetId",
            "ONetJob",
            "ONetProfile",
            "CId",
            "CValue",
            "ImportanceRating",
        ],
    )

    onet_profiles = {}
    for i, g in onet_df.groupby("ONetId"):
        onet_profiles[i] = vectorize(g.reset_index())

    profile = {}
    for i, g in df.groupby("PId"):
        profile[i] = vectorize(g.reset_index())

    k = profile.keys()
    return match_desired_onet(profile[list(k)[0]], onet_profiles) if len(k) > 0 else []


if __name__ == "__main__":
    match(1)
