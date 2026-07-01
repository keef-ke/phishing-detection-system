"""
train_ml_models.py
Trains 6 classical ML classifiers, evaluates each, and saves results.
Handles missing test splits gracefully.
Saved at: src/models/train_ml_models.py
"""
import os
import sys
import time
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.linear_model  import LogisticRegression
from sklearn.tree          import DecisionTreeClassifier
from sklearn.ensemble      import RandomForestClassifier
from sklearn.svm           import SVC
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix, roc_curve
)
import xgboost  as xgb
import lightgbm as lgb

# Clean system path injection for root directory imports
sys.path.insert(0, os.path.abspath('.'))
from src.models.preprocess import load_splits, scale, apply_smote

MODELS_DIR = 'models'
REPORTS    = 'reports'
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(REPORTS, exist_ok=True)

# Define classifiers 
CLASSIFIERS = {
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
    'Decision Tree':       DecisionTreeClassifier(max_depth=12, random_state=42),
    'Random Forest':       RandomForestClassifier(n_estimators=150, n_jobs=-1, random_state=42),
    'SVM':                 SVC(kernel='rbf', probability=True, random_state=42),
    'XGBoost':             xgb.XGBClassifier(n_estimators=200, learning_rate=0.1,
                                              use_label_encoder=False,
                                              eval_metric='logloss', random_state=42),
    'LightGBM':            lgb.LGBMClassifier(n_estimators=200, learning_rate=0.05,
                                               random_state=42, verbose=-1),
}


def evaluate(model, X, y, split_name):
    """Compute all metrics for one model on one split."""
    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1]
    return {
        'split'    : split_name,
        'accuracy' : round(accuracy_score(y, y_pred) * 100, 2),
        'precision': round(precision_score(y, y_pred) * 100, 2),
        'recall'   : round(recall_score(y, y_pred) * 100, 2),
        'f1'       : round(f1_score(y, y_pred) * 100, 2),
        'auc_roc'  : round(roc_auc_score(y, y_prob), 4),
    }


def plot_confusion_matrix(model, name, X_eval, y_eval, split_name):
    """Generate and save confusion matrix plots to disk."""
    cm = confusion_matrix(y_eval, model.predict(X_eval))
    fig, ax = plt.subplots(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Legit', 'Phishing'],
                yticklabels=['Legit', 'Phishing'], ax=ax)
    ax.set_title(f'Confusion Matrix ({split_name}) — {name}', fontweight='bold')
    ax.set_xlabel('Predicted')
    ax.set_ylabel('Actual')
    plt.tight_layout()
    safe_name = name.replace(' ', '_').lower()
    plt.savefig(f'{REPORTS}/cm_{safe_name}_{split_name}.png', dpi=150)
    plt.close()


def plot_roc_curves(roc_data, split_name):
    """Plot overlaid ROC curves for visual analysis."""
    fig, ax = plt.subplots(figsize=(8, 6))
    for name, (fpr, tpr, auc) in roc_data.items():
        ax.plot(fpr, tpr, label=f"{name} (AUC={auc:.3f})", linewidth=1.8)
    ax.plot([0, 1], [0, 1], 'k--', label='Random Chance')
    ax.set_title(f'ROC Curves — All Models ({split_name})', fontsize=13, fontweight='bold')
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.legend(fontsize=9)
    plt.tight_layout()
    plt.savefig(f'{REPORTS}/roc_curves_all_{split_name}.png', dpi=150)
    plt.close()
    print(f"📊 Global performance plots exported to: {REPORTS}/roc_curves_all_{split_name}.png")


def main():
    print("=" * 65)
    print(" 🤖 EXECUTING MULTI-CLASSIFIER TRAINING WORKSPACE")
    print("=" * 65)

    # Load & preprocess data splits dynamically
    X_tr, y_tr, X_val, y_val, X_te, y_te, features = load_splits()
    X_tr_s, X_val_s, X_te_s, scaler = scale(X_tr, X_val, X_te)
    X_tr_s, y_tr = apply_smote(X_tr_s, y_tr)

    # Determine fallback evaluation targets if test split is absent
    has_test = X_te_s is not None
    eval_matrix = X_te_s if has_test else X_val_s
    eval_labels = y_te if has_test else y_val
    target_split_name = 'test' if has_test else 'val'

    print(f"\n🎯 Primary performance logging directed to target split: [{target_split_name.upper()}]")

    results = []
    roc_data = {}

    # Train each classifier sequentially
    for name, clf in CLASSIFIERS.items():
        print(f"\n{'-' * 55}")
        print(f"🚀 Training Architecture: {name}")
        t0 = time.time()
        clf.fit(X_tr_s, y_tr)
        train_time = round(time.time() - t0, 1)
        print(f"✅ Training finalized in {train_time}s")

        # Core evaluation evaluations
        val_metrics = evaluate(clf, X_val_s, y_val, 'val')
        print(f"   🔹 Val  — Acc: {val_metrics['accuracy']}% | F1: {val_metrics['f1']}% | AUC: {val_metrics['auc_roc']:.4f}")
        
        if has_test:
            test_metrics = evaluate(clf, X_te_s, y_te, 'test')
            print(f"   🔹 Test — Acc: {test_metrics['accuracy']}% | F1: {test_metrics['f1']}% | AUC: {test_metrics['auc_roc']:.4f}")
            primary_metrics = test_metrics
        else:
            primary_metrics = val_metrics

        # Append metrics data for performance table
        results.append({'Model': name, **primary_metrics, 'train_time_s': train_time})

        # Render performance metrics visualizations
        plot_confusion_matrix(clf, name, eval_matrix, eval_labels, target_split_name)

        # Collect evaluation metrics arrays for ROC mapping
        y_prob = clf.predict_proba(eval_matrix)[:, 1]
        fpr, tpr, _ = roc_curve(eval_labels, y_prob)
        roc_data[name] = (fpr, tpr, primary_metrics['auc_roc'])

        # Serialize optimized classifier files to disk
        safe_name = name.replace(' ', '_').lower()
        joblib.dump(clf, f'{MODELS_DIR}/model_{safe_name}.pkl')
        print(f"💾 Model binary written to: models/model_{safe_name}.pkl")

    # Compile and export cross-model spreadsheet 
    results_df = pd.DataFrame(results).sort_values('f1', ascending=False)
    results_df.to_csv(f'{REPORTS}/model_comparison.csv', index=False)
    
    print("\n" + "=" * 65)
    print(f" 🏆 COMPARISON ANALYSIS MATRIX (Sorted by F1 on {target_split_name.upper()})")
    print("=" * 65)
    print(results_df.to_string(index=False))
    print("=" * 65)

    # Plot comprehensive ROC graph curves
    plot_roc_curves(roc_data, target_split_name)

    # Extract and isolate the highest performing pipeline variant
    best_name = results_df.iloc[0]['Model']
    best_clf = CLASSIFIERS[best_name]
    joblib.dump(best_clf, f'{MODELS_DIR}/best_ml_model.pkl')
    print(f"\n👑 Top Performing Algorithm Selection: {best_name}")
    print(f"💾 Absolute champion model configuration pinned to: models/best_ml_model.pkl\n")


if __name__ == '__main__':
    main()