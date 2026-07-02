"""
test_features.py  —  Unit tests for all feature extraction functions.
Run: pytest tests/test_features.py -v
"""
import sys
import os

# Ensure the root directory is on the path so src can be imported smoothly
sys.path.insert(0, os.path.abspath('.'))

import pytest
from src.features.url_features import extract_url_features

class TestUrlFeatures:
    PHISHING_URL = 'http://paypal-secure.evil.com/login?user=1&pass=x@gmail.com'
    LEGIT_URL    = 'https://www.github.com'

    def test_https_detection(self):
        assert extract_url_features(self.LEGIT_URL)['has_https'] == 1
        assert extract_url_features(self.PHISHING_URL)['has_https'] == 0

    def test_ip_detection(self):
        ip_url = 'http://192.168.1.100/admin/login'
        assert extract_url_features(ip_url)['is_ip_address'] == 1
        assert extract_url_features(self.LEGIT_URL)['is_ip_address'] == 0

    def test_url_shortener(self):
        short = 'https://bit.ly/abc123'
        assert extract_url_features(short)['url_shortener_used'] == 1
        assert extract_url_features(self.LEGIT_URL)['url_shortener_used'] == 0

    def test_at_symbol(self):
        assert extract_url_features(self.PHISHING_URL)['num_at_symbols'] >= 1
        assert extract_url_features(self.LEGIT_URL)['num_at_symbols'] == 0

    def test_suspicious_keywords(self):
        f = extract_url_features(self.PHISHING_URL)
        assert f['suspicious_keyword_cnt'] >= 1

    def test_url_length_is_positive(self):
        f = extract_url_features(self.LEGIT_URL)
        assert f['url_length'] > 0

    def test_returns_all_keys(self):
        f = extract_url_features(self.LEGIT_URL)
        expected_keys = [
            'url_length', 'domain_length', 'num_dots', 'num_hyphens', 'num_at_symbols',
            'num_question_marks', 'num_slashes', 'num_percent_encoding', 'num_digits',
            'num_subdomains', 'has_https', 'is_ip_address', 'url_shortener_used',
            'suspicious_keyword_cnt', 'digit_ratio', 'special_char_ratio',
            'double_slash_in_path', 'num_ampersands', 'path_length', 'has_non_std_port',
            'query_length', 'num_equal_signs'
        ]
        for key in expected_keys:
            assert key in f, f"Missing feature: {key}"

    def test_digit_ratio_range(self):
        f = extract_url_features(self.LEGIT_URL)
        assert 0.0 <= f['digit_ratio'] <= 1.0

    def test_special_char_ratio_range(self):
        f = extract_url_features(self.LEGIT_URL)
        assert 0.0 <= f['special_char_ratio'] <= 1.0

    def test_non_standard_port(self):
        url = 'http://evil.com:8080/login'
        assert extract_url_features(url)['has_non_std_port'] == 1
        assert extract_url_features(self.LEGIT_URL)['has_non_std_port'] == 0