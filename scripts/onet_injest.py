import pandas as pd
import glob

if __name__ == "__main__":
    for file in glob.glob("../data/onet/*.txt"):
        print(pd.read_csv(file, delimiter="\t"))
