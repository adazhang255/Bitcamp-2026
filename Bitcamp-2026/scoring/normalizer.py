import json
from pathlib import Path
from scipy import stats

REFERENCE_PATH = Path("data/reference_params.json")

with open(REFERENCE_PATH) as f:
    _REFERENCE = json.load(f)


def to_percentiles(raw_scores: dict) -> dict:
    result = {}

    for disorder, data in raw_scores.items():
        ref = _REFERENCE.get(disorder)

        if ref is None:
            result[disorder] = {**data, "percentile": None, "zscore": None}
            continue

        mean = ref["mean"]
        std  = ref["std"]

        if std == 0:
            zscore     = 0.0
            percentile = 50.0
        else:
            zscore     = (data["raw_score"] - mean) / std
            percentile = round(stats.norm.cdf(zscore) * 100, 1)

        result[disorder] = {
            **data,
            "zscore":     round(zscore, 3),
            "percentile": percentile,
        }

    return result