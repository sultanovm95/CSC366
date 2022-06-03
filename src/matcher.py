from src.utils.sqlconnect import get_connector
import pprint
import pandas as pd
import numpy as np

def _cossim(s, w):
    size = max(len(s), len(w))
    s = _reshape_vector(s, size)
    w = _reshape_vector(w, size)

    return np.sum(s * w) / (
        np.sqrt(np.sum(np.square(s))) * np.sqrt(np.sum(np.square(w)))
    )


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


def vectorize(group):
    data = group[["CId", "CValue", "ImportanceRating"]]
    max_cid = data["CId"].max()
    # print(data)
    values = np.zeros(shape=max_cid)
    importances = np.ones(shape=max_cid) * 4

    for i, vals in data.iterrows():
        values[i] = vals["CValue"]
        importances[i] = vals["ImportanceRating"]

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
        """, {"pid": pid}
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
        ],)

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
        ],)

    onet_profiles = {}
    for i, g in onet_df.groupby("ONetId"):
        onet_profiles[i] = vectorize(g.reset_index())

    profile = {}
    for i, g in df.groupby("PId"):
        profile[i] = vectorize(g.reset_index())

    k = profile.keys()
    return match_desired_onet(profile[list(k)[0]], onet_profiles) if len(k) else []

if __name__ == "__main__":
    match(1)
