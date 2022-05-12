import pandas as pd

def ingest_data(filename: str):
	book = pd.ExcelFile(filename, engine='openpyxl')
	for names in book.sheet_names:
		print(pd.read_excel(book, names))


if __name__ == "__main__":
	ingest_data("../data/Data-v01.xlsx",)