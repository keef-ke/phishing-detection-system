"""
app.py  —  Phishing Detection Flask API
Endpoints:
  POST /predict        → analyse a URL
  GET  /history        → last 50 detections
  GET  /stats          → aggregate statistics
  GET  /health         → server health check
Run: python src/api/app.py
"""
import os, sys, json, time, joblib
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS

# Allow imports from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.features.features_pipeline import extract_all_features, FEATURE_NAMES
from src.api.database import init_db, save_detection, get_history, get_stats

# ── App setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)                     # allow cross-origin requests from the frontend
MODELS_DIR = 'models'

# ── URL result cache (simple in-memory, 24h TTL) ──────────────────────────────
_cache = {}          # { url: (result, timestamp) }
CACHE_TTL = 86400    # 24 hours in seconds


def _get_cached(url):
    if url in _cache:
        result, ts = _cache[url]
        if time.time() - ts < CACHE_TTL:
            return result.copy()  # Return a copy to keep cache data clean
    return None


def _set_cache(url, result):
    _cache[url] = (result.copy(), time.time())


# ── Load model once at startup ────────────────────────────────────────────────
MODEL  = None
SCALER = None
FEATURE_NAMES_FINAL = FEATURE_NAMES

def load_assets():
    global MODEL, SCALER, FEATURE_NAMES_FINAL

    # Load scaler first — it's the source of truth for feature order/count
    scaler_path = os.path.join(MODELS_DIR, 'scaler.pkl')
    if os.path.exists(scaler_path):
        SCALER = joblib.load(scaler_path)
        print("✅ Scaler loaded")
    else:
        raise FileNotFoundError("scaler.pkl not found. Run training first.")

    # Prefer the scaler's own recorded feature names/order if available
    if hasattr(SCALER, 'feature_names_in_'):
        FEATURE_NAMES_FINAL = list(SCALER.feature_names_in_)
        print(f"✅ Using {len(FEATURE_NAMES_FINAL)} feature names from scaler.feature_names_in_")
    else:
        fname_file = 'dataset/processed/final_feature_names.txt'
        if os.path.exists(fname_file):
            with open(fname_file) as f:
                FEATURE_NAMES_FINAL = [l.strip() for l in f if l.strip()]
            print(f"✅ Loaded {len(FEATURE_NAMES_FINAL)} model features from configuration file")
        else:
            raise FileNotFoundError(
                "No scaler.feature_names_in_ and no final_feature_names.txt found. "
                "Cannot determine correct feature order."
            )

    # Hard check: does the feature list length match what the scaler expects?
    expected = getattr(SCALER, 'n_features_in_', None)
    if expected is not None and len(FEATURE_NAMES_FINAL) != expected:
        raise ValueError(
            f"Feature count mismatch: scaler expects {expected} features, "
            f"but FEATURE_NAMES_FINAL has {len(FEATURE_NAMES_FINAL)}. "
            f"Check final_feature_names.txt against training."
        )

    # Load model (prefer tuned → best ML → DNN)
    for name in ['best_model_tuned.pkl', 'best_ml_model.pkl', 'model_xgboost.pkl']:
        path = os.path.join(MODELS_DIR, name)
        if os.path.exists(path):
            MODEL = joblib.load(path)
            print(f"✅ Model loaded: {name}")
            return

    dnn = os.path.join(MODELS_DIR, 'dnn_model.h5')
    if os.path.exists(dnn):
        import tensorflow as tf
        MODEL = tf.keras.models.load_model(dnn)
        print("✅ DNN model loaded")
        return

    raise FileNotFoundError("No model found in models/. Run training scripts first.")


# ── Helper: run inference ─────────────────────────────────────────────────────
def _predict(url):
    raw = extract_all_features(url, include_webpage=True)

    # Build the vector in the EXACT order FEATURE_NAMES_FINAL specifies,
    # and fail loudly if a feature is missing instead of silently using -1
    missing = [f for f in FEATURE_NAMES_FINAL if f not in raw]
    if missing:
        raise KeyError(f"extract_all_features() did not return expected features: {missing}")

    row  = [raw[f] for f in FEATURE_NAMES_FINAL]
    X    = np.array([row])
    X_sc = SCALER.transform(X)

    if hasattr(MODEL, 'predict_proba'):
        prob = float(MODEL.predict_proba(X_sc)[0][1])
    else:
        prob = float(MODEL.predict(X_sc)[0][0])

    label = 'PHISHING' if prob >= 0.5 else 'LEGITIMATE'
    conf  = round(prob*100 if label=='PHISHING' else (1-prob)*100, 2)
    if   prob >= 0.85: risk = 'CRITICAL'
    elif prob >= 0.65: risk = 'HIGH'
    elif prob >= 0.40: risk = 'MEDIUM'
    else:              risk = 'LOW'

    return {
        'url'       : url,
        'prediction': label,
        'confidence': conf,
        'risk_level': risk,
        'raw_score' : round(prob, 4),
        'features'  : {f: raw.get(f,-1) for f in FEATURE_NAMES_FINAL}
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status':'ok','model_loaded': MODEL is not None}), 200


@app.route('/predict', methods=['POST'])
def predict():
    """
    POST /predict
    Body: {"url": "http://example.com"}
    Returns full prediction result JSON.
    """
    # ── Input validation ─────────────────────────────────────────────────
    data = request.get_json(force=True, silent=True)
    if not data or 'url' not in data:
        return jsonify({'error': 'Missing "url" field in request body'}), 400

    url = str(data['url']).strip()
    if not url:
        return jsonify({'error': 'URL cannot be empty'}), 400
    if len(url) > 2000:
        return jsonify({'error': 'URL too long (max 2000 chars)'}), 400
    if not (url.startswith('http://') or url.startswith('https://')):
        return jsonify({'error': 'URL must start with http:// or https://'}), 422

    # ── Check cache ───────────────────────────────────────────────────────
    cached = _get_cached(url)
    if cached:
        cached['from_cache'] = True
        return jsonify(cached), 200

    # ── Run prediction ────────────────────────────────────────────────────
    try:
        result = _predict(url)
    except Exception as e:
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

    # ── Log to database ───────────────────────────────────────────────────
    save_detection(result)
    _set_cache(url, result)
    result['from_cache'] = False

    return jsonify(result), 200


@app.route('/history', methods=['GET'])
def history():
    """GET /history — returns last 50 detections"""
    limit = request.args.get('limit', 50, type=int)
    records = get_history(min(limit, 200))
    return jsonify({'count': len(records), 'records': records}), 200


@app.route('/stats', methods=['GET'])
def stats():
    """GET /stats — aggregate detection statistics"""
    return jsonify(get_stats()), 200


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("\n" + "="*55)
    print("  Phishing Detection API Server")
    print("="*55)
    init_db()
    load_assets()
    print("\n🚀  Server starting on http://localhost:5000\n")
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)