from utils.sqlconnect import get_connector
import pprint
import pandas as pd


def vectorize(job_criteria):
    pass


def match_desired_onet(job, other_jobs, limit=10):
    pass


def match_exp_onet(job, onet_jobs, limit=10):
    pass


if __name__ == "__main__":
    conn = get_connector()
    cursor = conn.cursor()

    cursor.execute(
        """ SELECT Id, UserId, SurveyId, SurveyProfile, PType, CId, cValue, ImportanceRating FROM response, profile, profileCriteria WHERE response.SurveyProfile = profile.PId = profileCriteria.PId; """
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

    # pprint.pprint(df)
    for i, g in df.groupby("Id"):
        print(g)
