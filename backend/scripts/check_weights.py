# scripts/check_weights.py

from pathlib import Path
import pandas as pd

EXPECTED = [
    "schizophrenia", "alzheimers", "bipolar", "depression",
    "adhd", "autism", "parkinsons", "multiple_sclerosis",
    "ocd", "ptsd", "anorexia", "alcohol_use_disorder",
    "epilepsy", "tourette",
]

REQUIRED_COLS = {"chr_name", "chr_position", "effect_allele", "effect_weight"}

print("Checking weights/...\n")

all_ok = True
for name in EXPECTED:
    path = Path(f"weights/{name}.txt")
    if not path.exists():
        print(f"  MISSING  {name}.txt")
        all_ok = False
        continue

    try:
        df = pd.read_csv(path, sep="\t", comment="#", nrows=5)
        cols = {c.strip().lower() for c in df.columns}
        missing = REQUIRED_COLS - cols

        if missing:
            print(f"  BAD COLS {name}.txt — missing: {missing}")
            all_ok = False
        else:
            full = pd.read_csv(path, sep="\t", comment="#")
            print(f"  OK       {name}.txt — {len(full):,} SNPs")

    except Exception as e:
        print(f"  ERROR    {name}.txt — {e}")
        all_ok = False

print()
print("All good!" if all_ok else "Fix the issues above before running the server.")