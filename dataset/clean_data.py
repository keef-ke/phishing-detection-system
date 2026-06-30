"""
clean_data.py
Merges phishing + legitimate URLs, cleans, and splits into train/val/test.
Usage: python dataset/clean_data.py
"""
import urllib.parse
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split

# Dynamic base anchor tracking your project root workspace
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / 'dataset' / 'raw'
PROCESSED_DIR = BASE_DIR / 'dataset' / 'processed'

PHISHING_CSV = RAW_DIR / 'phishing_urls.csv'
LEGIT_CSV = RAW_DIR / 'legitimate_urls.csv'
RANDOM_STATE = 42

def is_valid_url(url):
    try:
        r = urllib.parse.urlparse(str(url))
        return r.scheme in ('http', 'https') and bool(r.netloc)
    except Exception:
        return False

def main():
    print("=" * 55)
    print("  Data Cleaning & Split Pipeline")
    print("=" * 55)

    # Check that source files exist before doing heavy lifting
    if not PHISHING_CSV.exists() or not LEGIT_CSV.exists():
        raise FileNotFoundError(
            f"Missing required input files in {RAW_DIR}.\n"
            f"Please run collect_phishing_urls.py and collect_legitimate_urls.py first!"
        )

    # ── Load ──────────────────────────────────────────────────
    phishing = pd.read_csv(PHISHING_CSV)
    legit = pd.read_csv(LEGIT_CSV)
    df = pd.concat([phishing, legit], ignore_index=True)
    print(f"\nLoaded: phishing={len(phishing):,} | legit={len(legit):,} | total={len(df):,}")

    # ── Clean ─────────────────────────────────────────────────
    before = len(df)
    df['url'] = df['url'].astype(str).str.strip().str.lower().str.rstrip('/')
    df = df.dropna(subset=['url', 'label'])
    df = df[df['url'].apply(is_valid_url)]
    
    # Trim extremely short URLs or massive garbage buffer overflow string links
    lengths = df['url'].str.len()
    df = df[(lengths >= 10) & (lengths <= 2000)]
    
    # Eliminate any duplicates between the two datasets
    df = df.drop_duplicates(subset=['url'])
    df['label'] = df['label'].astype(int)
    
    # Shuffle the combined dataset completely
    df = df.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)
    print(f"After cleaning: {len(df):,} rows (removed {before - len(df):,})")

    counts = df['label'].value_counts()
    print(f"  Legitimate (0): {counts.get(0, 0):,}")
    print(f"  Phishing   (1): {counts.get(1, 0):,}")

    # ── Stratified Split 70/15/15 ─────────────────────────────
    # Stratify makes sure train, val, and test all keep an exact 50/50 balance
    X, y = df['url'], df['label']
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, stratify=y, random_state=RANDOM_STATE)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, stratify=y_temp, random_state=RANDOM_STATE)

    train = pd.DataFrame({'url': X_train, 'label': y_train})
    val = pd.DataFrame({'url': X_val, 'label': y_val})
    test = pd.DataFrame({'url': X_test, 'label': y_test})
    print(f"\nSplit: train={len(train):,} | val={len(val):,} | test={len(test):,}")

    # ── Save ──────────────────────────────────────────────────
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(PROCESSED_DIR / 'combined_clean.csv', index=False)
    train.to_csv(PROCESSED_DIR / 'train.csv', index=False)
    val.to_csv(PROCESSED_DIR / 'val.csv', index=False)
    test.to_csv(PROCESSED_DIR / 'test.csv', index=False)
    
    print(f"\n✅  Files saved cleanly to: {PROCESSED_DIR}/")
    print("    combined_clean.csv | train.csv | val.csv | test.csv")

if __name__ == '__main__':
    main()