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

    pred['DEPTH'] = pred['DEPTH'].astype(float)
    truth['DEPTH'] = truth['DEPTH'].astype(float)

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

    n_labels = len(present_labels)
    cm = np.zeros((n_labels, n_labels), dtype=int)
    per_class = {}
    prec_list, rec_list, f1_list = [], [], []

    for i, true_lbl in enumerate(present_labels):
        for j, pred_lbl in enumerate(present_labels):
            cm[i, j] = int(np.sum((y_true == true_lbl) & (y_pred == pred_lbl)))

    for label in present_labels:
        tp = np.sum((y_true == label) & (y_pred == label))
        fp = np.sum((y_true != label) & (y_pred == label))
        fn = np.sum((y_true == label) & (y_pred != label))

        prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = float(2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

        per_class[label] = {
            'precision': prec,
            'recall': rec,
            'f1': f1,
        }
        prec_list.append(prec)
        rec_list.append(rec)
        f1_list.append(f1)

    macro_prec = float(np.mean(prec_list)) if prec_list else 0.0
    macro_rec = float(np.mean(rec_list)) if rec_list else 0.0
    macro_f1 = float(np.mean(f1_list)) if f1_list else 0.0
    acc = float(np.mean(y_true == y_pred)) if len(y_true) > 0 else 0.0

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

