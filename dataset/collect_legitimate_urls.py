"""
collect_legitimate_urls.py
Samples legitimate URLs from the Tranco top-1M domain list.
Usage: Run from project root or dataset directory
"""
import random
import urllib.parse
from pathlib import Path
import pandas as pd

# Dynamic base anchor tracking your project root workspace
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / 'dataset' / 'raw'
OUTPUT_FILE = RAW_DIR / 'legitimate_urls.csv'

SAMPLE_SIZE = 20000
RANDOM_SEED = 42

def is_valid_url(url):
    try:
        r = urllib.parse.urlparse(url)
        return r.scheme in ('http', 'https') and bool(r.netloc)
    except Exception:
        return False

def domain_to_url(domain):
    domain = domain.strip().lower()
    return 'https://' + domain if not domain.startswith('http') else domain

def main():
    # Load Tranco list from dataset/raw/tranco_top1m.csv
    tranco_path = RAW_DIR / 'tranco_top1m.csv'
    if not tranco_path.exists():
        raise FileNotFoundError(
            f"Missing source file at: {tranco_path}\n"
            "Please ensure 'tranco_top1m.csv' is placed inside your dataset/raw folder."
        )

    # Tranco CSV files typically do not have a header row
    df = pd.read_csv(tranco_path, header=None, names=['rank', 'domain'])
    domains = df['domain'].tolist()
    print(f"Loaded {len(domains):,} domains from Tranco")

    # Seed the generator to make sure your data split is perfectly reproducible
    random.seed(RANDOM_SEED)
    random.shuffle(domains)
    
    urls = []
    for d in domains:
        u = domain_to_url(d)
        if is_valid_url(u):
            urls.append(u)
        if len(urls) >= SAMPLE_SIZE:
            break

    print(f"Sampled {len(urls):,} legitimate URLs")
    
    # Notice the label here is 0 (legitimate), whereas PhishTank used 1 (phishing)
    out = pd.DataFrame({'url': urls, 'label': 0})
    out.to_csv(OUTPUT_FILE, index=False)
    
    print(f"🎉 Saved successfully to: {OUTPUT_FILE}")
    print("\nSample Output preview:")
    print("-" * 30)
    print(out.head(3).to_string())

if __name__ == '__main__':
    main()