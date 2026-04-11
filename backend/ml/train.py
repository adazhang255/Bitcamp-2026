import numpy as np
import pandas as pd
import joblib
from pathlib import Path
import xgboost as xgb

Path("models").mkdir(exist_ok=True)

DISORDERS = [
    "schizophrenia", "alzheimers", "bipolar", "depression",
    "adhd", "autism", "parkinsons", "multiple_sclerosis",
    "ocd", "ptsd", "anorexia", "alcohol_use_disorder",
    "epilepsy", "tourette",
]

PREVALENCE = {
    "schizophrenia":        0.010,
    "alzheimers":           0.050,
    "bipolar":              0.020,
    "depression":           0.150,
    "adhd":                 0.050,
    "autism":               0.020,
    "parkinsons":           0.010,
    "multiple_sclerosis":   0.003,
    "ocd":                  0.020,
    "ptsd":                 0.070,
    "anorexia":             0.006,
    "alcohol_use_disorder": 0.060,
    "epilepsy":             0.010,
    "tourette":             0.006,
}


def generate_synthetic_data(n_samples=50000):
    X = np.random.normal(loc=50, scale=15, size=(n_samples, len(DISORDERS)))
    X = np.clip(X, 0, 100)

    Y = np.zeros((n_samples, len(DISORDERS)))

    for i, disorder in enumerate(DISORDERS):
        base_prev = PREVALENCE[disorder]
        risk = base_prev * (0.3 + (X[:, i] / 100) * 2.7)
        Y[:, i] = (np.random.rand(n_samples) < risk).astype(int)

    return X, Y


def train():
    print("Generating synthetic training data...")
    X, Y = generate_synthetic_data()

    models = {}

    for i, disorder in enumerate(DISORDERS):
        print(f"Training {disorder}...")
        prevalence = PREVALENCE[disorder]

        clf = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=(1 - prevalence) / prevalence,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=42,
        )
        clf.fit(X, Y[:, i])
        models[disorder] = clf

    joblib.dump(models, "models/classifiers.pkl")
    print("Saved to models/classifiers.pkl")


if __name__ == "__main__":
    train()