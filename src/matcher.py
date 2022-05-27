from utils.sqlconnect import get_connector
import pprint
import pandas as pd
import numpy as np


def _cossim(s, w):
    return np.sum(s * w) / (
        np.sqrt(np.sum(np.square(s))) * np.sqrt(np.sum(np.square(w)))
    )


def _pearson(s, w):
    _s_mean = np.mean(s)
    _w_mean = np.mean(w)
    return np.sum((s - _s_mean) * (w - _w_mean)) / (
        np.sqrt(np.square(np.sum(s - _s_mean)))
        * np.sqrt(np.square(np.sum(w - _w_mean)))
    )


def _weightcos(s, v, w):
    return np.sum(s * v * w) / (
        np.sqrt(np.sum(np.square(s))) * np.sqrt(np.sum(np.square(w))) * np.sum(v)
    )


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
    return results[:10]


def match_desired_onet(job, other_jobs, limit=10):
    pass


def match_exp_onet(job, onet_jobs, limit=10):
    pass


if __name__ == "__main__":
    conn = get_connector()
    cursor = conn.cursor()

    cursor.execute(
        """ SELECT Id, UserId, SurveyId, SurveyProfile, PType, CId, cValue, ImportanceRating FROM response, profile, profileCriteria WHERE response.SurveyProfile = profile.PId and profile.PId = profileCriteria.PId ORDER BY ID, CId; """
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

    profile = {}

    # pprint.pprint(df)
    for i, g in df.groupby("Id"):
        profile[i] = vectorize(g.reset_index())

    pprint.pprint(profile)

    for k in profile.keys():
        pprint.pprint(match_jobs(k, profile[k], profile))
