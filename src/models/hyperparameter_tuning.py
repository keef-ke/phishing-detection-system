"""
hyperparameter_tuning.py
Tunes the best model using RandomizedSearchCV.
Typically tunes XGBoost (usually the winner).
Handles missing test splits gracefully by falling back to validation splits.
Saved at: src/models/hyperparameter_tuning.py
"""
import joblib
import os
import sys
import numpy as np
import pandas as pd
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, 
    f1_score, roc_auc_score, make_scorer
)
import xgboost as xgb

# Clean system path injection for root directory imports
sys.path.insert(0, os.path.abspath('.'))
from src.models.preprocess import load_splits, scale, apply_smote

MODELS_DIR = 'models'

def main():
    print("=" * 65)
    print(" 🛠️  HYPERPARAMETER TUNING OPTIMIZATION (XGBoost)")
    print("=" * 65)

    # Load splits via your core preprocess engine
    X_tr, y_tr, X_val, y_val, X_te, y_te, _ = load_splits()
    X_tr_s, X_val_s, X_te_s, scaler = scale(X_tr, X_val, X_te)
    X_tr_s, y_tr = apply_smote(X_tr_s, y_tr)

    # Determine fallback evaluation targets based on file presence
    has_test = X_te_s is not None
    eval_matrix = X_te_s if has_test else X_val_s
    eval_labels = y_te if has_test else y_val
    target_split_name = 'TEST' if has_test else 'VALIDATION'

    # Hyperparameter search space distribution envelope
    param_dist = {
        'n_estimators':     [100, 200, 300, 500],
        'max_depth':        [3, 4, 5, 6, 8],
        'learning_rate':    [0.01, 0.05, 0.1, 0.2],
        'subsample':        [0.6, 0.7, 0.8, 0.9, 1.0],
        'colsample_bytree': [0.6, 0.7, 0.8, 0.9, 1.0],
        'reg_alpha':        [0, 0.1, 0.5, 1.0],
        'reg_lambda':       [0.1, 0.5, 1.0, 2.0],
    }

    base_model = xgb.XGBClassifier(
        use_label_encoder=False,
        eval_metric='logloss',
        random_state=42,
        n_jobs=-1,
    )

    scorer = make_scorer(f1_score)
    search = RandomizedSearchCV(
        base_model, param_dist,
        n_iter=30,              # Try 30 random variations
        scoring=scorer,
        cv=3,                   # 3-Fold cross-validation strategy
        n_jobs=-1,
        random_state=42,
        verbose=2,
    )

    print(f"\n🚀 Launching RandomizedSearchCV (30 iterations, 3-fold CV)...")
    print("⏳ This cross-validation track can take 10 to 30 minutes depending on your CPU cores.\n")
    search.fit(X_tr_s, y_tr)

    print("\n" + "-" * 55)
    print(" 🏆 SEARCH COMPLETION SUMMARY")
    print("-" * 55)
    print(f"🔹 Best Found CV F1 Score: {search.best_score_:.4f}")
    print("🔹 Best Model Hyperparameters:")
    for param_name, param_val in search.best_params_.items():
        print(f"   ▫️ {param_name}: {param_val}")
    print("-" * 55)

    best_model = search.best_estimator_
    y_pred = best_model.predict(eval_matrix)
    y_prob = best_model.predict_proba(eval_matrix)[:, 1]

    print(f"\n🎯 Performance Metrics Assessment ({target_split_name} SET) ──")
    print(f"   ▪️ Accuracy  : {accuracy_score(eval_labels, y_pred) * 100:.2f}%")
    print(f"   ▪️ Precision : {precision_score(eval_labels, y_pred) * 100:.2f}%")
    print(f"   ▪️ Recall    : {recall_score(eval_labels, y_pred) * 100:.2f}%")
    print(f"   ▪️ F1 Score  : {f1_score(eval_labels, y_pred) * 100:.2f}%")
    print(f"   ▪️ AUC-ROC   : {roc_auc_score(eval_labels, y_prob):.4f}")

    # Save tuned model file architecture
    os.makedirs(MODELS_DIR, exist_ok=True)
    output_model_path = f'{MODELS_DIR}/best_model_tuned.pkl'
    joblib.dump(best_model, output_model_path)
    print(f"\n💾 Production deployment model binary saved to: {output_model_path}")
    print("=" * 65)

if __name__ == '__main__':
    main()