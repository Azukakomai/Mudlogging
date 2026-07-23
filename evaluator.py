"""
Evaluation Metrics Module — Confusion Matrix & Classification Performance.

Implements the thesis Section "Evaluation Metrics":
  • Multi-class confusion matrix (Gas / Oil / Water / No Show)
  • Per-class Precision, Recall, F1-Score
  • Macro-averaged metrics (equal weight per class)
  • Accuracy

All metrics compare predicted zone labels against ground-truth well test results.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    accuracy_score,
)


# Canonical class order
ZONE_LABELS = ["Gas", "Oil", "Water", "No Show"]


def match_depths(predicted_df: pd.DataFrame, truth_df: pd.DataFrame,
                 tolerance: float = 0.5) -> pd.DataFrame:
    """
    Merge predicted and ground-truth DataFrames on DEPTH using a
    nearest-match join within `tolerance` metres.

    Both DataFrames must contain 'DEPTH' and 'ZONE' columns.
    Returns a merged DataFrame with columns:
        DEPTH, ZONE_PRED, ZONE_TRUE
    """
    pred = predicted_df[['DEPTH', 'ZONE']].copy()
    truth = truth_df[['DEPTH', 'ZONE']].copy()

    pred = pred.rename(columns={'ZONE': 'ZONE_PRED'}).sort_values('DEPTH').reset_index(drop=True)
    truth = truth.rename(columns={'ZONE': 'ZONE_TRUE'}).sort_values('DEPTH').reset_index(drop=True)

    # Use merge_asof for nearest-depth matching
    merged = pd.merge_asof(
        pred, truth,
        on='DEPTH',
        tolerance=tolerance,
        direction='nearest',
    )

    # Drop rows where no truth was matched
    merged = merged.dropna(subset=['ZONE_TRUE']).reset_index(drop=True)

    return merged


def compute_evaluation(predicted_df: pd.DataFrame, truth_df: pd.DataFrame,
                       tolerance: float = 0.5) -> dict:
    """
    Computes all evaluation metrics from the thesis.

    Parameters
    ----------
    predicted_df : DataFrame with 'DEPTH' and 'ZONE' columns (system output).
    truth_df     : DataFrame with 'DEPTH' and 'ZONE' columns (ground truth).
    tolerance    : Maximum depth difference (metres) for matching rows.

    Returns
    -------
    dict with keys:
        'matched_count'  : int — number of depth intervals compared
        'confusion_matrix' : 2D numpy array (rows=true, cols=pred)
        'labels'         : list of class labels used
        'per_class'      : dict[class_name] → {precision, recall, f1}
        'macro_precision': float
        'macro_recall'   : float
        'macro_f1'       : float
        'accuracy'       : float
    """
    merged = match_depths(predicted_df, truth_df, tolerance)

    if len(merged) == 0:
        return {
            'matched_count': 0,
            'confusion_matrix': np.zeros((len(ZONE_LABELS), len(ZONE_LABELS)), dtype=int),
            'labels': ZONE_LABELS,
            'per_class': {z: {'precision': 0.0, 'recall': 0.0, 'f1': 0.0} for z in ZONE_LABELS},
            'macro_precision': 0.0,
            'macro_recall': 0.0,
            'macro_f1': 0.0,
            'accuracy': 0.0,
        }

    y_true = merged['ZONE_TRUE'].values
    y_pred = merged['ZONE_PRED'].values

    # Only include labels that actually appear in the data
    present_labels = sorted(
        set(y_true) | set(y_pred),
        key=lambda x: ZONE_LABELS.index(x) if x in ZONE_LABELS else len(ZONE_LABELS)
    )

    cm = confusion_matrix(y_true, y_pred, labels=present_labels)

    # Per-class metrics
    prec_per = precision_score(y_true, y_pred, labels=present_labels,
                               average=None, zero_division=0)
    rec_per  = recall_score(y_true, y_pred, labels=present_labels,
                            average=None, zero_division=0)
    f1_per   = f1_score(y_true, y_pred, labels=present_labels,
                        average=None, zero_division=0)

    per_class = {}
    for idx, label in enumerate(present_labels):
        per_class[label] = {
            'precision': float(prec_per[idx]),
            'recall':    float(rec_per[idx]),
            'f1':        float(f1_per[idx]),
        }

    # Macro-averaged metrics (thesis specifies macro averaging)
    macro_prec = float(precision_score(y_true, y_pred, labels=present_labels,
                                       average='macro', zero_division=0))
    macro_rec  = float(recall_score(y_true, y_pred, labels=present_labels,
                                    average='macro', zero_division=0))
    macro_f1   = float(f1_score(y_true, y_pred, labels=present_labels,
                                average='macro', zero_division=0))
    acc        = float(accuracy_score(y_true, y_pred))

    return {
        'matched_count':    len(merged),
        'confusion_matrix': cm,
        'labels':           present_labels,
        'per_class':        per_class,
        'macro_precision':  macro_prec,
        'macro_recall':     macro_rec,
        'macro_f1':         macro_f1,
        'accuracy':         acc,
    }
