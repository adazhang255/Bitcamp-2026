import urllib.request, gzip, shutil
urllib.request.urlretrieve(
    "https://ftp.ebi.ac.uk/pub/databases/spot/pgs/scores/PGS000667/ScoringFiles/PGS000667.txt.gz",
    "weights/depression.txt.gz"
)
with gzip.open("weights/depression.txt.gz", "rb") as f_in, open("weights/depression.txt", "wb") as f_out:
    shutil.copyfileobj(f_in, f_out)