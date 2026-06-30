"""
url_features.py  —  URL Lexical Feature Extractor
Extracts 22 features from the URL string alone. No network calls needed.
Saved at: src/features/url_features.py
"""
import re
import ipaddress
from urllib.parse import urlparse

# Global lookup structures for extraction optimization
URL_SHORTENERS = {
    'bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly', 'short.to',
    'is.gd', 'buff.ly', 'adf.ly', 'bit.do', 'rb.gy', 'shorte.st',
    'po.st', 'lnkd.in', 'ift.tt', 'dlvr.it', 'cli.gs', 'su.pr', 'bl.ink',
    'snip.ly', 'cutt.ly', 'tiny.cc',
}

SUSPICIOUS_KEYWORDS = [
    'login', 'signin', 'sign-in', 'verify', 'verification', 'secure', 'account',
    'update', 'banking', 'confirm', 'password', 'credential', 'paypal', 'ebay',
    'amazon', 'apple', 'microsoft', 'google', 'facebook', 'instagram', 'free',
    'click', 'alert', 'suspend', 'limited', 'winner', 'prize', 'urgent',
    'important', 'billing', 'invoice', 'support', 'helpdesk', 'customer',
]

# ── Feature Extraction Primatives ─────────────────────────────────────────────

def get_url_length(url):           
    return len(url)

def get_domain_length(url):
    try:    
        return len(urlparse(url).netloc)
    except Exception: 
        return -1

def count_dots(url):               return url.count('.')
def count_hyphens(url):            return url.count('-')
def count_at_symbols(url):         return url.count('@')
def count_question_marks(url):     return url.count('?')
def count_slashes(url):            return url.count('/')
def count_percent_encoding(url):   return url.count('%')
def count_digits(url):             return sum(c.isdigit() for c in url)

def count_subdomains(url):
    try:
        host = urlparse(url).netloc.split(':')[0]
        if host.startswith('www.'): 
            host = host[4:]
        return max(0, len(host.split('.')) - 2)
    except Exception: 
        return -1

def has_https(url):                
    return 1 if url.lower().startswith('https://') else 0

def is_ip_address(url):
    """
    UPGRADE: Added explicit safety guard against malformed text strings 
    where .hostname resolves to None, preventing uncaught AttributeError crashes.
    """
    try:
        host = urlparse(url).hostname
        if not host:
            return 0
        # Strip structural IPv6 brackets if present in the raw network location
        if host.startswith('[') and host.endswith(']'):
            host = host[1:-1]
        ipaddress.ip_address(host)
        return 1
    except ValueError: 
        return 0

def uses_url_shortener(url):
    try:
        host = urlparse(url).netloc.lower().lstrip('www.')
        return 1 if host in URL_SHORTENERS else 0
    except Exception: 
        return 0

def count_suspicious_keywords(url):
    url_lower = url.lower()
    return sum(kw in url_lower for kw in SUSPICIOUS_KEYWORDS)

def get_digit_ratio(url):
    return round(count_digits(url) / len(url), 4) if url else 0.0

def get_special_char_ratio(url):
    if not url: 
        return 0.0
    return round(len(re.findall(r'[^a-zA-Z0-9]', url)) / len(url), 4)

def has_double_slash_in_path(url):
    try:    
        return 1 if '//' in urlparse(url).path else 0
    except Exception: 
        return 0

def count_ampersands(url):         return url.count('&')

def get_path_length(url):
    try:    
        return len(urlparse(url).path)
    except Exception: 
        return -1

def has_non_standard_port(url):
    try:
        port = urlparse(url).port
        return 0 if port is None or port in (80, 443) else 1
    except Exception: 
        return 0

def get_query_length(url):
    try:    
        return len(urlparse(url).query)
    except Exception: 
        return 0

def count_equal_signs(url):        return url.count('=')

# ── Master Dictionary Compilation ─────────────────────────────────────────────

def extract_url_features(url):
    """Master function — returns an ordered dict of all 22 lexical URL features."""
    return {
        'url_length':             get_url_length(url),
        'domain_length':          get_domain_length(url),
        'num_dots':               count_dots(url),
        'num_hyphens':            count_hyphens(url),
        'num_at_symbols':         count_at_symbols(url),
        'num_question_marks':     count_question_marks(url),
        'num_slashes':            count_slashes(url),
        'num_percent_encoding':   count_percent_encoding(url),
        'num_digits':             count_digits(url),
        'num_subdomains':         count_subdomains(url),
        'has_https':              has_https(url),
        'is_ip_address':          is_ip_address(url),
        'url_shortener_used':     uses_url_shortener(url),
        'suspicious_keyword_cnt': count_suspicious_keywords(url),
        'digit_ratio':            get_digit_ratio(url),
        'special_char_ratio':     get_special_char_ratio(url),
        'double_slash_in_path':   has_double_slash_in_path(url),
        'num_ampersands':         count_ampersands(url),
        'path_length':            get_path_length(url),
        'has_non_std_port':       has_non_standard_port(url),
        'query_length':           get_query_length(url),
        'num_equal_signs':        count_equal_signs(url),
    }

# ── Local Development Validation Verification Block ────────────────────────────

if __name__ == '__main__':
    print("=" * 65)
    print("🧪  RUNNING LEXICAL FEATURE EXTRACTOR DIAGNOSTIC CHECK")
    print("=" * 65)
    
    samples = [
        'https://www.google.com',
        'http://192.168.1.1/login/verify?user=1',
        'https://bit.ly/3abcXYZ',
        'http://paypal-secure-update.evil.com/signin',
    ]
    
    for url in samples:
        features = extract_url_features(url)
        print(f"\n🎯 URL: {url}")
        print("-" * 50)
        for feature_name, feature_value in features.items():
            print(f"  🔹 {feature_name:<26} : {feature_value}")
            
    print("\n✅ Verification diagnostic successfully executed.")