"""
05_feature_selection.py
Analyze feature importance and remove weak/redundant features.
Saved at: notebooks/05_feature_selection.py
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier

# Ensure output reporting directories exist safely
os.makedirs('reports', exist_ok=True)

# 1. Load data from the correct uppercase directory structure
input_path = 'Dataset/processed/train_features.csv'
if not os.path.exists(input_path):
    raise FileNotFoundError(f"Missing target feature file at '{input_path}'. Run batch extraction first.")

df = pd.read_csv(input_path)
FEATURE_NAMES = [c for c in df.columns if c not in ('url', 'label')]
X = df[FEATURE_NAMES].fillna(-1)
y = df['label']

print("=" * 65)
print("🔍 RUNNING FEATURE SELECTION & VARIANCE ANALYSIS")
print("=" * 65)
print(f"🔹 Initial Input Shape : {X.shape[0]:,} rows x {X.shape[1]} features")
print(f"🔹 Missing Values      : {X.isin([-1]).sum().sum():,} placeholder entries detected\n")

# 2. Train a Fast Random Forest Classifier for Feature Scopes
print("🤖 Computing feature importance weights via Random Forest...")
rf = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
rf.fit(X, y)

importance = pd.Series(rf.feature_importances_, index=FEATURE_NAMES)
importance = importance.sort_values(ascending=False)

print("\n🏆 Top 20 Most Predictive Features:")
print("-" * 45)
print(importance.head(20).round(4).to_string())
print("-" * 45)

# 3. Render and Export Importance Metrics (Skipping blocking GUI windows)
fig, ax = plt.subplots(figsize=(10, 8))
importance.head(25).sort_values().plot(kind='barh', ax=ax, color='#3498db')
ax.set_title('Feature Importance Matrix (Random Forest)', fontsize=13, fontweight='bold')
ax.set_xlabel('Importance Structural Score')
plt.tight_layout()
plt.savefig('reports/feature_importance.png', dpi=150)
plt.close() # Clean closure to avoid memory leaks or thread hanging
print("📊 Diagnostic plot exported to: reports/feature_importance.png")

# 4. Strip Low-Variance / Weak Features
threshold = 0.005
weak_features = importance[importance < threshold].index.tolist()
print(f"\n📉 Features below importance threshold ({threshold}): {len(weak_features)} found")
if weak_features:
    print(f"   Dropped attributes: {weak_features}")

# Build temporary workspace matching retained columns
retained_features = [f for f in FEATURE_NAMES if f not in weak_features]
X_filtered = X[retained_features]

# 5. Multicollinearity Check (Drop highly redundant metrics)
corr_matrix = X_filtered.corr().abs()
upper_triangle = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
highly_correlated = [col for col in upper_triangle.columns if any(upper_triangle[col] > 0.92)]

print(f"\n🔗 Redundant correlated feature groups (> 0.92 correlation coefficient): {len(highly_correlated)} found")
if highly_correlated:
    print(f"   Dropped attributes: {highly_correlated}")

# 6. Save final, lean feature list to disk
final_keep_list = [f for f in retained_features if f not in highly_correlated]
print(f"\n🎯 Final Filtered Feature Matrix Count: {len(final_keep_list)} features retained.")

output_txt_path = 'Dataset/processed/final_feature_names.txt'
os.makedirs(os.path.dirname(output_txt_path), exist_ok=True)

with open(output_txt_path, 'w') as f:
    f.write('\n'.join(final_keep_list))
    
print(f"💾 Feature definition manifest written to: {output_txt_path}")
print("=" * 65)