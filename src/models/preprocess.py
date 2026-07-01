"""
preprocess.py  —  Load and preprocess feature CSVs for ML training.
Handles scaling, SMOTE, and train/val/test split loading.
Saved at: src/models/preprocess.py
"""
import os
import sys
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE

# Ensure project root directory is on the path if run standalone
sys.path.insert(0, os.path.abspath('.'))

# Fix path constants to match your actual uppercase directory name
PROCESSED = 'Dataset/processed'
MODELS    = 'models'

def load_splits(feature_names_file='Dataset/processed/final_feature_names.txt'):
    """Load train, val, and test feature CSVs and return balanced X/y arrays."""
    
    # Load selected features generated during selection step
    if os.path.exists(feature_names_file):
        with open(feature_names_file) as f:
            features = [line.strip() for line in f if line.strip()]
    else:
        # Fallback: read first line of training dataset to infer columns
        train_sample_path = f'{PROCESSED}/train_features.csv'
        if not os.path.exists(train_sample_path):
            raise FileNotFoundError(f"Missing base feature map at '{train_sample_path}'. Process data first.")
        df_tmp = pd.read_csv(train_sample_path, nrows=1)
        features = [c for c in df_tmp.columns if c not in ('url', 'label')]

    print(f"🔹 Using {len(features)} optimal features for preprocessing.")

    def _load(split):
        path = f'{PROCESSED}/{split}_features.csv'
        if not os.path.exists(path):
            print(f"⚠️ Warning: Optional split asset file not found at '{path}'.")
            return None, None
        df = pd.read_csv(path)
        df[features] = df[features].fillna(-1)
        return df[features].values, df['label'].values

    X_train, y_train = _load('train')
    X_val,   y_val   = _load('val')
    X_test,  y_test  = _load('test')

    if X_train is None:
        raise FileNotFoundError(f"Critical error: Primary training asset missing at '{PROCESSED}/train_features.csv'")

    # Pretty-print tracking matrix shape details
    test_shape_str = f"Test: {X_test.shape}" if X_test is not None else "Test: [Skipped / Empty]"
    print(f"📊 Matrices -> Train: {X_train.shape} | Val: {X_val.shape if X_val is not None else '[None]'} | {test_shape_str}")
    print(f"⚖️ Train distribution -> Legitimate (0): {(y_train == 0).sum()} | Phishing (1): {(y_train == 1).sum()}")
    
    return X_train, y_train, X_val, y_val, X_test, y_test, features


def scale(X_train, X_val, X_test):
    """Fit standard scaling parameters on training data, transform validation/test splits, and export artifact."""
    os.makedirs(MODELS, exist_ok=True)
    scaler = StandardScaler()
    
    print("⚖️ Fitting StandardScaler weights on the training distribution split...")
    X_train_s = scaler.fit_transform(X_train)
    
    X_val_s = scaler.transform(X_val) if X_val is not None else None
    X_test_s = scaler.transform(X_test) if X_test is not None else None
    
    scaler_output_path = f'{MODELS}/scaler.pkl'
    joblib.dump(scaler, scaler_output_path)
    print(f"💾 Preprocessing artifact saved to: {scaler_output_path}")
    
    return X_train_s, X_val_s, X_test_s, scaler


def apply_smote(X_train, y_train):
    """Apply SMOTE adjustments to balance training targets if distribution disparity exceeds a 1.5:1 boundary."""
    count_0 = (y_train == 0).sum()
    count_1 = (y_train == 1).sum()
    
    ratio = count_0 / max(count_1, 1)
    if ratio > 1.5 or ratio < 0.67:
        print(f"📈 Applying Synthetic Minority Over-sampling (SMOTE). Current ratio is {ratio:.2f}...")
        sm = SMOTE(random_state=42)
        X_res, y_res = sm.fit_resample(X_train, y_train)
        print(f"✨ Post-SMOTE Balance Matrix: {X_res.shape} | Legitimate (0): {(y_res == 0).sum()} | Phishing (1): {(y_res == 1).sum()}")
        return X_res, y_res
        
    print(f"✅ Class values are naturally balanced. Skipping SMOTE transformations (ratio: {ratio:.2f}).")
    return X_train, y_train


if __name__ == '__main__':
    print("=" * 65)
    print("🛠️ EXECUTING PREPROCESSING AND TRANSFORM ENGINE RUN")
    print("=" * 65)
    X_train, y_train, X_val, y_val, X_test, y_test, features = load_splits()
    X_train_s, X_val_s, X_test_s, scaler = scale(X_train, X_val, X_test)
    X_train_s, y_train = apply_smote(X_train_s, y_train)
    print("\n✅ Matrix pipeline adjustments finished successfully!")
    print("=" * 65)