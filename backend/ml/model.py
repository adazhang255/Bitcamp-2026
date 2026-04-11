import joblib
import shap
import numpy as np
from pathlib import Path

DISORDERS = [
    "schizophrenia", "alzheimers", "bipolar", "depression",
    "adhd", "autism", "parkinsons", "multiple_sclerosis",
    "ocd", "ptsd", "anorexia", "alcohol_use_disorder",
    "epilepsy", "tourette",
]

RISK_TIERS = [
    (90, "elevated"),
    (70, "moderate"),
    (30, "average"),
    (0,  "below average"),
]

def _get_tier(percentile: float) -> str:
    for threshold, label in RISK_TIERS:
        if percentile >= threshold:
            return label
    return "below average"

_MODEL_PATH = Path("models/classifiers.pkl")
_MODELS = None

def _load_models():
    global _MODELS
    if not _MODEL_PATH.exists():
        raise FileNotFoundError(
            "models/classifiers.pkl not found. "
            "Run `python ml/train.py` first."
        )
    _MODELS = joblib.load(_MODEL_PATH)

_load_models()


def predict_with_explanation(percentile_scores: dict) -> dict:
    if _MODELS is None:
        raise RuntimeError("Models not loaded.")

    x = np.array([[
        percentile_scores[d]["percentile"] or 50.0
        for d in DISORDERS
    ]])

    results = {}

    for i, disorder in enumerate(DISORDERS):
        model = _MODELS[disorder]

        prob = float(model.predict_proba(x)[0][1])
        explainer  = shap.TreeExplainer(model)
        shap_vals  = explainer.shap_values(x)[0]
        top_idx    = np.argsort(np.abs(shap_vals))[::-1][:3]
        top_contributors = [DISORDERS[j] for j in top_idx]

        pct = percentile_scores[disorder]["percentile"] or 50.0

        results[disorder] = {
            **percentile_scores[disorder],
            "probability":       round(prob * 100, 1),
            "risk_tier":         _get_tier(pct),
            "top_contributors":  top_contributors,
        }

    return results