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
            print(f"WARNING: weights file missing for {disorder} — skipping")
            continue
        df = pd.read_csv(
            path,
            sep="\t",
            comment="#",
            usecols=["rsID", "effect_allele", "effect_weight", "allelefrequency_effect"],
            dtype={"rsID": str, "effect_allele": str, "effect_weight": float, "allelefrequency_effect": float},
        )
        _WEIGHTS_CACHE[disorder] = df

_load_weights()


def score_all_disorders(snp_dosages: dict) -> dict:
    results = {}

    for disorder, weights_df in _WEIGHTS_CACHE.items():
        raw_score  = 0.0
        snps_found = 0

        for _, row in weights_df.iterrows():
            rsid   = row["rsID"]
            beta   = row["effect_weight"]
            eaf    = row["allelefrequency_effect"]

            dosage = snp_dosages.get(rsid)

            if dosage is not None:
                snps_found += 1
            else:
                dosage = 2.0 * eaf

            raw_score += dosage * beta

        snps_total = len(weights_df)

        results[disorder] = {
            "raw_score":    round(raw_score, 6),
            "snps_found":   snps_found,
            "snps_total":   snps_total,
            "coverage_pct": round(snps_found / snps_total * 100, 1) if snps_total > 0 else 0.0,
        }

    return results