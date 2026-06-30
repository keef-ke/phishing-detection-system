"""
collect_phishing_urls.py
Processes the downloaded PhishTank CSV and saves clean phishing URLs.
Usage: python src/collect_phishing_urls.py (or from root)
"""
import urllib.parse
from pathlib import Path
import pandas as pd

# Dynamic base anchor tracking your exact project root
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / 'dataset' / 'raw'
OUTPUT_FILE = RAW_DIR / 'phishing_urls.csv'
MAX_URLS = 20000

def is_valid_url(url):
    try:
        r = urllib.parse.urlparse(str(url))
        return r.scheme in ('http', 'https') and bool(r.netloc)
    except Exception:
        return False

def clean_url(url):
    return str(url).strip().rstrip('/').lower()

def main():
    # Candidates for PhishTank file names inside dataset/raw/
    candidates = ['phishtank_raw.csv', 'online-valid.csv', 'phishtank.csv']
    df = None
    
    for name in candidates:
        path = RAW_DIR / name
        if path.exists():
            df = pd.read_csv(path, low_memory=False)
            print(f"Loaded {name}: {len(df)} rows")
            break
            
    if df is None:
        raise FileNotFoundError(
            f"No PhishTank CSV found at: {RAW_DIR}\n"
            f"Please ensure one of these files exists: {candidates}"
        )

    # Standardize column headers to lowercase
    df.columns = [c.lower() for c in df.columns]

    # Verify column layout for url tracking
    if 'url' not in df.columns:
        raise KeyError(f"Could not find a 'url' column. Available columns: {list(df.columns)}")

    # Filter for verified phishing records only
    if 'verified' in df.columns:
        df = df[df['verified'].astype(str).str.lower() == 'yes']
        print(f"After 'verified' filter: {len(df)} rows")

    urls = df['url'].dropna().tolist()
    
    # Deduplicate and validate via list comprehension dictionary mapping
    cleaned = list(dict.fromkeys(clean_url(u) for u in urls if is_valid_url(u)))
    cleaned = cleaned[:MAX_URLS]
    print(f"Final clean URLs: {len(cleaned)}")

    # Construct the finalized target DataFrame
    out = pd.DataFrame({'url': cleaned, 'label': 1})
    out.to_csv(OUTPUT_FILE, index=False)
    print(f"🎉 Saved successfully to: {OUTPUT_FILE}")
    print("\nSample Output preview:")
    print("-" * 30)
    print(out.head(3).to_string())

if __name__ == '__main__':
    main()