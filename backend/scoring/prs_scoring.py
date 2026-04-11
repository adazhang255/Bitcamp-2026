# scoring/prs_scorer.py

import pandas as pd
from pathlib import Path

WEIGHTS_DIR = Path("weights")

DISORDER_META = {
    "schizophrenia":        {"label": "Schizophrenia",          "category": "psychiatric"},
    "alzheimers":           {"label": "Alzheimer's disease",    "category": "neurological"},
    "bipolar":              {"label": "Bipolar disorder",       "category": "mood"},
    "depression":           {"label": "Major depression",       "category": "mood"},
    "adhd":                 {"label": "ADHD",                   "category": "neurodevelopmental"},
    "autism":               {"label": "Autism (ASD)",           "category": "neurodevelopmental"},
    "parkinsons":           {"label": "Parkinson's disease",    "category": "neurological"},
    "multiple_sclerosis":   {"label": "Multiple sclerosis",     "category": "neurological"},
    "ocd":                  {"label": "OCD",                    "category": "mood"},
    "ptsd":                 {"label": "PTSD",                   "category": "mood"},
    "anorexia":             {"label": "Anorexia nervosa",       "category": "psychiatric"},
    "alcohol_use_disorder": {"label": "Alcohol use disorder",   "category": "psychiatric"},
    "epilepsy":             {"label": "Epilepsy",               "category": "neurological"},
    "tourette":             {"label": "Tourette syndrome",      "category": "neurodevelopmental"},
}

_WEIGHTS_CACHE: dict[str, pd.DataFrame] = {}

def _load_weights():
    for disorder in DISORDER_META:
        path = WEIGHTS_DIR / f"{disorder}.txt"
        if not path.exists():
            print(f"WARNING: weights file missing for {disorder}")
            continue
        try:
            df = pd.read_csv(
                path,
                sep="\t",
                comment="#",
                dtype=str,
            )

            # normalize column names to lowercase for safety
            df.columns = [c.strip().lower() for c in df.columns]

            # ensure chr_name and chr_position exist
            if "chr_name" not in df.columns or "chr_position" not in df.columns:
                print(f"WARNING: {disorder}.txt missing chr_name/chr_position")
                continue

            if "effect_allele" not in df.columns or "effect_weight" not in df.columns:
                print(f"WARNING: {disorder}.txt missing effect_allele/effect_weight")
                continue

            # normalize chromosome: "01" -> "1", drop any "chr" prefix
            df["chr_name"] = (
                df["chr_name"]
                .str.replace("chr", "", case=False)
                .str.lstrip("0")
                .replace("", "0")
            )
            df["chr_position"] = df["chr_position"].str.strip()
            df["effect_weight"] = pd.to_numeric(df["effect_weight"], errors="coerce")
            df = df.dropna(subset=["effect_weight"])

            _WEIGHTS_CACHE[disorder] = df
            print(f"Loaded {disorder}: {len(df):,} SNPs")

        except Exception as e:
            print(f"ERROR loading {disorder}: {e}")

_load_weights()


def score_all_disorders(snp_dosages: dict) -> dict:
    """
    Input:  {(chr, pos): dosage}
    Output: {disorder: {raw_score, snps_found, snps_total, coverage_pct}}
    """
    results = {}

    for disorder, df in _WEIGHTS_CACHE.items():
        raw_score  = 0.0
        snps_found = 0

        for _, row in df.iterrows():
            key    = (row["chr_name"], row["chr_position"])
            beta   = float(row["effect_weight"])

            dosage = snp_dosages.get(key)

            if dosage is not None:
                snps_found += 1
                raw_score  += dosage * beta
            else:
                # no EAF available — use population mean of 1.0 (dosage = 1)
                # this is conservative: assumes heterozygous as default
                raw_score += 1.0 * beta

        snps_total = len(df)

        results[disorder] = {
            "raw_score":    round(raw_score, 6),
            "snps_found":   snps_found,
            "snps_total":   snps_total,
            "coverage_pct": round(snps_found / snps_total * 100, 1) if snps_total > 0 else 0.0,
        }

    return results