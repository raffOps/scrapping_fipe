import sys
import subprocess
import os
from datetime import datetime

from google.cloud import storage
import pandas as pd

if os.getenv("BUCKET"):
    BUCKET = os.getenv("BUCKET")

else:
    BUCKET = "fipe-teste"


def extract_fipe(year=2018, months=[4]):
    files = []
    for month in months:
        subprocess.run(["scrapy", "runspider", "FIPE.py",
                        "-a", f"year={year}", "-a", f"month={month}",
                        "-o", f"{year}-{month}.csv"])

        files.append(f"{year}-{month}.csv")
    return files


def upload_fipe(year=2018, files=["2018-4.csv"]):
    dfs = []
    for file in files:
        dfs.append(pd.read_csv(file))

    df = pd.concat(dfs)
    filename = f"{year}.parquet"
    df.to_parquet(path=filename, compression="gzip")

    storage_client = storage.Client.from_service_account_json(json_credentials_path="./key.json",
                                                              project="rjr-a3data-hackathon")
    bucket = storage_client.get_bucket(bucket_or_name=BUCKET)
    blob = bucket.blob(filename)
    blob.upload_from_filename(filename)


if __name__ == "__main__":
    if len(sys.argv) == 2: # entire year
        year = int(sys.argv[1])
        months = list(range(1, datetime.now().month)) # year and month
    elif len(sys.argv) == 3:
        year = int(sys.argv[1])
        months = [int(sys.argv[2])]
    else: # default
        year = 2018
        months = [4]

    #files = extract_fipe(year, months)
    upload_fipe(year)

