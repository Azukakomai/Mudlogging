"""
Machine Learning Classifier Module — Hydrocarbon Zone Prediction.
==================================================================
Trains Random Forest and Gradient Boosting classifiers on the
sbkdeep-001_mudlogg.csv dataset. Labels are generated automatically
using the existing expert-rule engine (engine.compute_all), following
the thesis methodology of comparing ML against the deterministic system.

Public API
----------
train_all()           → dict with training metadata (accuracy, classes, etc.)
predict(df, model)    → pd.Series of predicted zone labels (ZONE_ML)
get_feature_importances(model) → list of (feature_name, importance) tuples sorted desc
get_cv_results(model) → dict {accuracy, std, per_class_cv}
MODELS                → dict of available model names → classifier objects
"""

import os
import io
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import cross_validate, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import warnings

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────────────────────────────────────

FEATURE_COLS = [
    "C1", "C2", "C3", "IC4", "NC4", "IC5", "NC5",
    "TG_USED",
    "R1_C1_C2", "R2_C1_C3", "R3_C2_C3",
    "DRYNESS", "WH", "BH", "CH",
    "WBS", "GOW_NOTG", "CARBON_INDEX",
]

ZONE_LABELS = ["Gas", "Oil", "Water", "No Show"]

# Path to training data — resolve relative to this file
_HERE = os.path.dirname(os.path.abspath(__file__))
SBKDEEP_PATH = os.path.join(_HERE, "..", "sbkdeep-001_mudlogg.csv")

# ─────────────────────────────────────────────────────────────────────────────
#  Module-level model registry
# ─────────────────────────────────────────────────────────────────────────────

MODELS = {
    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    ),
    "Gradient Boosting": GradientBoostingClassifier(
        n_estimators=150,
        learning_rate=0.1,
        max_depth=5,
        min_samples_leaf=2,
        random_state=42,
    ),
}

# Training state (populated by train_all())
_trained: dict[str, bool] = {name: False for name in MODELS}
_training_meta: dict = {}
_X_train: np.ndarray | None = None
_y_train: np.ndarray | None = None
_feature_names: list[str] = []
_label_encoder: LabelEncoder = LabelEncoder()


# ─────────────────────────────────────────────────────────────────────────────
#  Training pipeline
# ─────────────────────────────────────────────────────────────────────────────

def _load_and_prepare_sbkdeep() -> tuple[np.ndarray, np.ndarray, list[str]]:
    """
    Load sbkdeep-001_mudlogg.csv, compute features via engine, generate
    zone labels via expert rules, and return (X, y_encoded, feature_names).
    """
    # Import here to avoid circular imports at module level
    from parser import parse_mudlog_file
    from engine import compute_all

    # Load CSV (skip unit row)
    df_raw = pd.read_csv(SBKDEEP_PATH, header=0)
    df_raw.columns = [str(c).strip().upper() for c in df_raw.columns]

    # Drop the units row (first data row often contains "METRES", "PPM", etc.)
    # Detect and skip non-numeric rows
    df_raw = df_raw[pd.to_numeric(df_raw["DEPTH"], errors="coerce").notna()].copy()

    required = ["DEPTH", "C1", "C2", "C3", "IC4", "NC4", "IC5", "NC5"]
    for c in required:
        if c not in df_raw.columns:
            df_raw[c] = 0.0
        df_raw[c] = pd.to_numeric(df_raw[c], errors="coerce").fillna(0.0)

    if "TG" in df_raw.columns:
        df_raw["TG"] = pd.to_numeric(df_raw["TG"], errors="coerce").fillna(0.0)

    df_raw = df_raw.sort_values("DEPTH").reset_index(drop=True)

    # Run expert-rule engine to generate training labels
    computed = compute_all(df_raw)

    # Build feature matrix — replace inf/nan with 0
    available_features = [f for f in FEATURE_COLS if f in computed.columns]
    X = computed[available_features].replace([np.inf, -np.inf], np.nan).fillna(0.0).values.astype(float)

    # Labels
    y_str = computed["ZONE"].values

    return X, y_str, available_features


def train_all() -> dict:
    """
    Train all models on the sbkdeep dataset.
    Returns a metadata dict with training stats.
    Idempotent — safe to call multiple times.
    """
    global _X_train, _y_train, _feature_names, _trained, _training_meta

    X, y_str, feat_names = _load_and_prepare_sbkdeep()
    _feature_names = feat_names

    # Encode labels
    y_enc = _label_encoder.fit_transform(y_str)
    _X_train = X
    _y_train = y_enc

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    meta: dict = {
        "training_samples": len(X),
        "n_features": len(feat_names),
        "feature_names": feat_names,
        "classes": _label_encoder.classes_.tolist(),
        "class_distribution": {
            cls: int((y_str == cls).sum()) for cls in _label_encoder.classes_
        },
        "models": {},
    }

    for model_name, clf in MODELS.items():
        cv_results = cross_validate(
            clf, X, y_enc,
            cv=cv,
            scoring="accuracy",
            return_train_score=True,
            n_jobs=-1,
        )
        clf.fit(X, y_enc)
        _trained[model_name] = True

        meta["models"][model_name] = {
            "cv_accuracy_mean": float(np.mean(cv_results["test_score"])),
            "cv_accuracy_std":  float(np.std(cv_results["test_score"])),
            "train_accuracy":   float(np.mean(cv_results["train_score"])),
        }

    _training_meta = meta
    return meta


# ─────────────────────────────────────────────────────────────────────────────
#  Prediction
# ─────────────────────────────────────────────────────────────────────────────

def predict(df: pd.DataFrame, model_name: str = "Random Forest") -> pd.Series:
    """
    Predict zone labels for a computed DataFrame using the trained model.

    Parameters
    ----------
    df         : DataFrame output from engine.compute_all() — must have FEATURE_COLS
    model_name : One of "Random Forest" or "Gradient Boosting"

    Returns
    -------
    pd.Series of zone label strings aligned to df.index
    """
    if not _trained.get(model_name, False):
        raise RuntimeError(f"Model '{model_name}' is not trained yet. Call train_all() first.")

    clf = MODELS[model_name]
    available = [f for f in _feature_names if f in df.columns]
    X = df[available].replace([np.inf, -np.inf], np.nan).fillna(0.0).values.astype(float)

    y_enc = clf.predict(X)
    y_str = _label_encoder.inverse_transform(y_enc)
    return pd.Series(y_str, index=df.index, name="ZONE_ML")


# ─────────────────────────────────────────────────────────────────────────────
#  Feature importances
# ─────────────────────────────────────────────────────────────────────────────

def get_feature_importances(model_name: str = "Random Forest") -> list[tuple[str, float]]:
    """
    Returns sorted list of (feature_name, importance_score) tuples, descending.
    """
    if not _trained.get(model_name, False):
        return []
    clf = MODELS[model_name]
    importances = clf.feature_importances_
    pairs = sorted(zip(_feature_names, importances), key=lambda x: x[1], reverse=True)
    return pairs


# ─────────────────────────────────────────────────────────────────────────────
#  Training metadata accessor
# ─────────────────────────────────────────────────────────────────────────────

def get_training_meta() -> dict:
    """Return the training metadata dict (populated after train_all())."""
    return _training_meta


def is_trained(model_name: str = "Random Forest") -> bool:
    return _trained.get(model_name, False)
