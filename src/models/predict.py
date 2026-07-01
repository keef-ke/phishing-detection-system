"""
predict.py  —  Standalone Prediction Script
Given any URL, returns: label + confidence + feature values.
Run: python src/models/predict.py --url "http://example.com"
"""
import os
import sys
import argparse
import joblib
import numpy as np

# 1. Dynamically locate the absolute file system path of this specific script
SCRIPT_PATH = os.path.abspath(__file__)          # .../src/models/predict.py
MODELS_FOLDER = os.path.dirname(SCRIPT_PATH)     # .../src/models
SRC_FOLDER = os.path.dirname(MODELS_FOLDER)      # .../src
PROJECT_ROOT = os.path.dirname(SRC_FOLDER)        # C:\phishing\phishing-detection-system

# 2. Inject the absolute project root directly into the highest priority path slot
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 3. Now Python can seamlessly trace the absolute folder pathway from the root down
from src.features.features_pipeline import extract_all_features, FEATURE_NAMES 

MODELS_DIR = 'models'

def load_model_and_scaler():
    """Load the best trained model and scaler from disk."""
    # Prefer tuned model → best ML model → base XGBoost
    for name in ['best_model_tuned.pkl', 'best_ml_model.pkl', 'model_xgboost.pkl']:
        path = os.path.join(MODELS_DIR, name)
        if os.path.exists(path):
            model  = joblib.load(path)
            scaler = joblib.load(os.path.join(MODELS_DIR, 'scaler.pkl'))
            print(f"Loaded model: {name}")
            return model, scaler

    # Try DNN (Uses modern .keras extension)
    dnn_path = os.path.join(MODELS_DIR, 'dnn_model.keras')
    if os.path.exists(dnn_path):
        import keras
        model  = keras.models.load_model(dnn_path)
        scaler = joblib.load(os.path.join(MODELS_DIR, 'scaler.pkl'))
        print("Loaded model: dnn_model.keras")
        return model, scaler

    raise FileNotFoundError("No trained model found in models/. Run training first.")


def predict_url(url, model, scaler, feature_names=None):
    """
    Extract features, scale them, and return prediction result dict.
    """
    if feature_names is None:
        # Matches your exact directory capitalization
        feat_file = 'Dataset/processed/final_feature_names.txt'
        if os.path.exists(feat_file):
            with open(feat_file) as f:
                feature_names = [l.strip() for l in f if l.strip()]
        else:
            feature_names = FEATURE_NAMES

    print(f"\nExtracting features for: {url}")
    raw = extract_all_features(url, include_webpage=True)

    # Build feature vector in correct order
    X = np.array([[raw.get(f, -1) for f in feature_names]])
    X_scaled = scaler.transform(X)

    # Predict
    if hasattr(model, 'predict_proba'):
        prob = model.predict_proba(X_scaled)[0][1]
    else:
        # Keras DNN
        prob = float(model.predict(X_scaled)[0][0])

    label      = 1 if prob >= 0.5 else 0
    label_name = 'PHISHING' if label == 1 else 'LEGITIMATE'
    confidence = round(prob * 100 if label == 1 else (1 - prob) * 100, 2)

    if   prob >= 0.85: risk = 'CRITICAL'
    elif prob >= 0.65: risk = 'HIGH'
    elif prob >= 0.40: risk = 'MEDIUM'
    else:              risk = 'LOW'

    return {
        'url'        : url,
        'prediction' : label_name,
        'confidence' : confidence,
        'risk_level' : risk,
        'raw_score'  : round(prob, 4),
        'features'   : {f: raw.get(f, -1) for f in feature_names},
    }


def print_result(result):
    emoji = '🚨' if result['prediction'] == 'PHISHING' else '✅'
    print("\n" + "="*55)
    print(f"  {emoji}  RESULT: {result['prediction']}")
    print("="*55)
    print(f"  URL        : {result['url']}")
    print(f"  Confidence : {result['confidence']}%")
    print(f"  Risk Level : {result['risk_level']}")
    print(f"  Raw Score  : {result['raw_score']}")
    print("\n  Key Features:")
    key_feats = ['has_https','is_ip_address','suspicious_keyword_cnt',
                 'domain_age_days','has_login_form','has_valid_ssl',
                 'redirect_count','url_length','num_at_symbols']
    for f in key_feats:
        if f in result['features']:
            print(f"    {f:<35}: {result['features'][f]}")
    print("="*55)


def main():
    parser = argparse.ArgumentParser(description='Phishing URL Detector')
    parser.add_argument('--url', required=True, help='URL to check')
    args = parser.parse_args()

    model, scaler = load_model_and_scaler()
    result = predict_url(args.url, model, scaler)
    print_result(result)
    return result


if __name__ == '__main__':
    main()