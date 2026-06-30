"""
webpage_features.py  —  HTML Content Feature Extractor
Fetches the webpage and extracts 13 content-based features.
Saved at: src/features/webpage_features.py
"""
import re
import time
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup

TIMEOUT = 10
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}

# Fetching & Parsing Utilities 

def _fetch(url):
    try:
        t0 = time.time()
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        return r, round((time.time() - t0) * 1000)
    except Exception: 
        return None, -1

def _parse(resp):
    if resp is None: 
        return None
    try:    
        return BeautifulSoup(resp.content, 'lxml')
    except Exception: 
        return None

def _domain(url):
    try:
        h = urlparse(url).netloc.lower()
        return h[4:] if h.startswith('www.') else h
    except Exception: 
        return ''

# Feature Extraction Blocks 

def get_http_status(resp):       
    return resp.status_code if resp else -1

def count_redirects(resp):       
    return len(resp.history) if resp else -1

def get_response_time(ms):       
    return int(ms)

def has_login_form(soup):
    if soup is None: 
        return -1
    for form in soup.find_all('form'):
        for inp in form.find_all('input'):
            if inp.get('type', '').lower() == 'password' or 'pass' in inp.get('name', '').lower():
                return 1
    return 0

def get_external_links_ratio(soup, base_url):
    if soup is None: 
        return -1.0
    base = _domain(base_url)
    total = ext = 0
    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        if not href or href.startswith(('#', 'javascript:')): 
            continue
        total += 1
        try:
            if _domain(urljoin(base_url, href)) != base: 
                ext += 1
        except Exception: 
            pass
    return round(ext / total, 4) if total > 0 else 0.0

def has_favicon_external(soup, base_url):
    if soup is None: 
        return -1
    base = _domain(base_url)
    for tag in soup.find_all('link', rel=True):
        # Safety Fix: Cast rel array safely into space-separated string parsing
        rel_list = tag.get('rel', [])
        rel_str = ' '.join(rel_list) if isinstance(rel_list, list) else str(rel_list)
        
        if 'icon' in rel_str.lower():
            href = tag.get('href', '')
            if href.startswith('http') and _domain(href) != base: 
                return 1
    return 0

def has_right_click_disabled(soup):
    if soup is None: 
        return -1
    page = str(soup)
    patterns = [r'oncontextmenu.*return\s+false', r'addEventListener.*contextmenu']
    return 1 if any(re.search(p, page, re.I) for p in patterns) else 0

def has_popup_windows(soup):
    if soup is None: 
        return -1
    return 1 if re.search(r'window\.open\s*\(', str(soup), re.I) else 0

def has_hidden_iframe(soup):
    if soup is None: 
        return -1
    for f in soup.find_all('iframe'):
        style = f.get('style', '').replace(' ', '').lower()
        if ('visibility:hidden' in style or 'display:none' in style
                or str(f.get('width', '1')) == '0' or str(f.get('height', '1')) == '0'):
            return 1
    return 0

def get_empty_anchor_ratio(soup):
    if soup is None: 
        return -1.0
    anchors = soup.find_all('a', href=True)
    if not anchors: 
        return 0.0
    empty = sum(1 for a in anchors if a['href'].strip() in ('#', '', 'javascript:void(0);', 'javascript:void(0)', 'javascript:;'))
    return round(empty / len(anchors), 4)

def has_meta_refresh(soup):
    if soup is None: 
        return -1
    # Safety Fix: Avoid raw key lookup crashes by requiring http-equiv presence explicitly
    for m in soup.find_all('meta', attrs={'http-equiv': True}):
        if m.get('http-equiv', '').lower() == 'refresh': 
            return 1
    return 0

def has_form_action_external(soup, base_url):
    if soup is None: 
        return -1
    base = _domain(base_url)
    for form in soup.find_all('form'):
        action = form.get('action', '').strip()
        if action.startswith('http') and _domain(action) != base: 
            return 1
    return 0

def get_image_external_ratio(soup, base_url):
    if soup is None: 
        return -1.0
    base = _domain(base_url)
    imgs = soup.find_all('img', src=True)
    if not imgs: 
        return 0.0
    ext = sum(1 for i in imgs if i['src'].startswith('http') and _domain(i['src']) != base)
    return round(ext / len(imgs), 4)

# Master Dictionary Compilation 

def extract_webpage_features(url):
    """Returns dict of all 13 webpage content features."""
    resp, ms = _fetch(url)
    soup = _parse(resp)
    
    return {
        'http_status_code':          get_http_status(resp),
        'redirect_count':            count_redirects(resp),
        'response_time_ms':          get_response_time(ms),
        'has_login_form':            has_login_form(soup),
        'external_links_ratio':      get_external_links_ratio(soup, url),
        'favicon_external':          has_favicon_external(soup, url),
        'right_click_disabled':      has_right_click_disabled(soup),
        'has_popup_windows':         has_popup_windows(soup),
        'has_hidden_iframe':         has_hidden_iframe(soup),
        'empty_anchor_ratio':        get_empty_anchor_ratio(soup),
        'meta_refresh_redirect':     has_meta_refresh(soup),
        'form_action_external':      has_form_action_external(soup, url),
        'image_from_external_ratio': get_image_external_ratio(soup, url),
    }

# Local Script Test Loop 

if __name__ == '__main__':
    print("=" * 65)
    print("🧪  RUNNING WEBPAGE HTML FEATURE EXTRACTOR DIAGNOSTIC CHECK")
    print("=" * 65)
    
    test_url = 'https://www.github.com'
    print(f"Scraping DOM tree node architectures for: {test_url}\n")
    
    results = extract_webpage_features(test_url)
    for key, value in results.items():
        print(f"  🔹 {key:<29} : {value}")
        
    print("\n✅ Verification diagnostic successfully executed.")