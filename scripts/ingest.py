import pandas as pd

sheet_ingest_func = {
    "Surveys": 0,
    "Users": 0,
    "Survey Questions New": 0,
    "QuestionResponses": 0,
    "Survey Questions": 0,
    "URE Experience": 0,
    "Work Experience": 0,
    "Work Profile ": 0,
    "Work Profile-copy-values": 0,
    "Work Preferences": 0,
    "Definitions": 0,
}


def ingest_data(filename: str):
    """
    Ingest data from a csv file, returning the dataframes

    Parameters
    ----------
        filename : str
            path to .xlxs file

    Returns
    -------
        results : list of dict
            list of sheetnames with assicated dataframe for data

    Warns
    -----
        any sheets that can't be converted into a dataframe will be printed out for reformatting
    """
    book = pd.ExcelFile(filename, engine="openpyxl")
    results = {}

    for names in book.sheet_names:
        try:
            results[names] = pd.read_excel(book, names)
        except:  # noqa: E722
            print(f"{filename}:{names} failed to load due to formatting")
    return results


if __name__ == "__main__":
    sheets = ingest_data(
        "../data/Data-v03.xlsx",
    )

    for keys in sheets.keys():
        print(keys, sheet_ingest_func.get(keys))
