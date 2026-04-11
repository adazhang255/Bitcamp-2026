import json, random
from pathlib import Path

Path("data").mkdir(exist_ok=True)

DISORDERS = [
    "schizophrenia", "alzheimers", "bipolar", "depression",
    "adhd", "autism", "parkinsons", "multiple_sclerosis",
    "ocd", "ptsd", "anorexia", "alcohol_use_disorder",
    "epilepsy", "tourette",
]

def fake_tier(pct):
    if pct >= 90: return "elevated"
    if pct >= 70: return "moderate"
    if pct >= 30: return "average"
    return "below average"

random.seed(42)

results = {}
for d in DISORDERS:
    pct = round(random.gauss(50, 20), 1)
    pct = max(1.0, min(99.0, pct))
    results[d] = {
        "raw_score":        round(random.gauss(0, 1), 4),
        "zscore":           round((pct - 50) / 15, 3),
        "percentile":       pct,
        "snps_found":       random.randint(400000, 650000),
        "snps_total":       1083770,
        "coverage_pct":     round(random.uniform(45, 62), 1),
        "probability":      round(pct * 0.06 + random.uniform(-2, 2), 1),
        "risk_tier":        fake_tier(pct),
        "top_contributors": random.sample(
            [x for x in DISORDERS if x != d], 3
        ),
    }

payload = {"snps_parsed": 612483, "results": results}
Path("data/demo_payload.json").write_text(json.dumps(payload, indent=2))
print("Written to data/demo_payload.json")