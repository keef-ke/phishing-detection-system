"""
feature_pipeline.py  —  Master Feature Extractor
Combines all 3 feature layers into one unified function call.
Saved at: src/features/feature_pipeline.py
"""
from src.features.url_features import extract_url_features
from src.features.domain_features import extract_domain_features
from src.features.webpage_features import extract_webpage_features

# 44 Features Total (22 URL, 9 Domain, 13 Webpage)
FEATURE_NAMES = [
    # URL Lexical Features (22)
    'url_length', 'domain_length', 'num_dots', 'num_hyphens', 'num_at_symbols',
    'num_question_marks', 'num_slashes', 'num_percent_encoding', 'num_digits',
    'num_subdomains', 'has_https', 'is_ip_address', 'url_shortener_used',
    'suspicious_keyword_cnt', 'digit_ratio', 'special_char_ratio',
    'double_slash_in_path', 'num_ampersands', 'path_length', 'has_non_std_port',
    'query_length', 'num_equal_signs',
    
    # Domain Network Features (9)
    'domain_age_days', 'domain_expiry_days', 'registration_length_days',
    'has_dns_a_record', 'has_dns_mx_record', 'dns_nameserver_count',
    'dns_ttl', 'ssl_expiry_days', 'has_valid_ssl',
    
    # Webpage HTML Content Features (13)
    'http_status_code', 'redirect_count', 'response_time_ms', 'has_login_form',
    'external_links_ratio', 'favicon_external', 'right_click_disabled',
    'has_popup_windows', 'has_hidden_iframe', 'empty_anchor_ratio',
    'meta_refresh_redirect', 'form_action_external', 'image_from_external_ratio',
]

def extract_all_features(url, include_webpage=True):
    """
    Extract all features for a single URL.
    Set include_webpage=False to skip HTTP fetches (fast, offline mode).
    
    UPGRADE: Ensures a consistent schema dimension by populating missing keys
    with safe placeholder values when running in offline mode.
    """
    feats = {}
    
    # 1. Inject Lexical and Network Layers
    feats.update(extract_url_features(url))
    feats.update(extract_domain_features(url))
    
    # 2. Inject Content Layer or Apply Fallback Schema
    if include_webpage:
        feats.update(extract_webpage_features(url))
    else:
        # Pad missing webpage slots to ensure a consistent feature array size
        webpage_fallbacks = {
            'http_status_code': -1,
            'redirect_count': -1,
            'response_time_ms': -1,
            'has_login_form': -1,
            'external_links_ratio': -1.0,
            'favicon_external': -1,
            'right_click_disabled': -1,
            'has_popup_windows': -1,
            'has_hidden_iframe': -1,
            'empty_anchor_ratio': -1.0,
            'meta_refresh_redirect': -1,
            'form_action_external': -1,
            'image_from_external_ratio': -1.0,
        }
        feats.update(webpage_fallbacks)
        
    return feats

# ── Local Development Validation Verification Block ────────────────────────────

if __name__ == '__main__':
    print("=" * 65)
    print("🧪  RUNNING MASTER FEATURE PIPELINE DIAGNOSTIC")
    print("=" * 65)
    
    test_url = 'https://www.github.com'
    
    print("\n[Test 1] Running in OFFLINE Mode (Speed optimization)...")
    offline_feats = extract_all_features(test_url, include_webpage=False)
    print(f"  🔹 Extracted Key Count: {len(offline_feats)}")
    print(f"  🔹 Verification: 'has_login_form' value -> {offline_feats['has_login_form']} (Expected: -1)")
    
    print("\n[Test 2] Running in FULL Mode (With HTML parsing)...")
    full_feats = extract_all_features(test_url, include_webpage=True)
    print(f"  🔹 Extracted Key Count: {len(full_feats)}")
    print(f"  🔹 Verification: 'http_status_code' value -> {full_feats['http_status_code']}")
    
    # Cross-check schema alignment
    is_aligned = len(offline_feats) == len(full_feats) == len(FEATURE_NAMES)
    if is_aligned:
        print("\n✅ Success: Dimensions match perfectly across all execution branches!")
    else:
        print("\n❌ Error: Feature schema mismatch detected.")