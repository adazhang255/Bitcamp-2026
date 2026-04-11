import urllib.request, gzip, shutil, os

os.makedirs("weights", exist_ok=True)

SCORES = {
    "schizophrenia":       "PGS000329",
    "alzheimers":          "PGS000334",
    "bipolar":             "PGS000588",
    "depression":          "PGS000667",
    "adhd":                "PGS000537",
    "autism":              "PGS000478",
    "parkinsons":          "PGS000445",
    "multiple_sclerosis":  "PGS000055",
    "ocd":                 "PGS000401",
    "ptsd":                "PGS000585",
    "anorexia":            "PGS000648",
    "alcohol_use_disorder":"PGS000505",
    "epilepsy":            "PGS000400",
    "tourette":            "PGS000586",
}

BASE = "https://ftp.ebi.ac.uk/pub/databases/spot/pgs/scores"

for name, pgs_id in SCORES.items():
    url = f"{BASE}/{pgs_id}/ScoringFiles/{pgs_id}.txt.gz"
    gz_path = f"weights/{name}.txt.gz"
    out_path = f"weights/{name}.txt"
    
    print(f"Downloading {name} ({pgs_id})...")
    urllib.request.urlretrieve(url, gz_path)
    
    with gzip.open(gz_path, 'rb') as f_in, open(out_path, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    
    os.remove(gz_path)
    print(f"  -> {out_path}")

print("Done!")