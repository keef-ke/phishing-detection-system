"""
batch_extract.py  —  Batch Feature Extraction Script
Processes every URL in a CSV file multi-threadedly and writes a clean feature matrix.
Saved at: src/features/batch_extract.py
"""
import os
import sys
import argparse
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure project root is visible to Python interpreter across running paths
sys.path.insert(0, os.path.abspath('.'))
from src.features.features_pipeline import extract_all_features, FEATURE_NAMES

CHECKPOINT_EVERY = 200
LOG_EVERY        = 50

def _worker(args):
    """
    Isolated threat worker function executing network and lexical queries.
    Uses unified fallback schemas to maintain input shape dimensions on failure.
    """
    idx, url, label = args
    try:
        # Run full extraction (Lexical + Domain Network + HTML Scraping)
        f = extract_all_features(url, include_webpage=True)
        f['url'], f['label'] = url, label
        return idx, f, None
    except Exception as e:
        # Formulate clean dimension padding using correct type standards on error
        f = {}
        for k in FEATURE_NAMES:
            if 'ratio' in k:
                f[k] = -1.0
            else:
                f[k] = -1
        f['url'], f['label'] = url, label
        return idx, f, str(e)

def run(input_path, output_path, n_workers):
    print("=" * 65)
    print("🚀 STARTING MULTI-THREADED BATCH FEATURE EXTRACTION PIPELINE")
    print("=" * 65)
    print(f"🔹 Input Path  : {input_path}")
    print(f"🔹 Output Path : {output_path}")
    print(f"🔹 Thread Pool : {n_workers} concurrent workers\n")

    if not os.path.exists(input_path):
        print(f"❌ Error: Input target file not found at '{input_path}'")
        return

    df = pd.read_csv(input_path)
    print(f"Total Base Dataset Entries: {len(df):,}")

    # 1. FIX: Track processed data securely to prevent dataset multiplication loops
    historical_rows = []
    done_urls = set()
    
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        try:
            done_df = pd.read_csv(output_path)
            if 'url' in done_df.columns:
                done_urls = set(done_df['url'].astype(str).tolist())
                historical_rows = done_df.to_dict('records')
                print(f"🔄 Checkpoint found! Resuming progress: {len(done_urls):,} processed links skipped.")
        except Exception as e:
            print(f"⚠️ Checkpoint file unreadable ({e}). Starting extraction from scratch.")

    # 2. Filter dataset down to pending operations
    pending = [(i, r['url'], r['label']) for i, r in df.iterrows() if str(r['url']) not in done_urls]
    print(f"Pending Operation Backlog : {len(pending):,} URLs\n")

    if not pending:
        print("✅ Extraction complete. No new URLs to process.")
        return

    start_time = time.time()
    errors = 0
    done_count = 0
    new_rows = []
    
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    # 3. Fire up the high-concurrency worker network
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = {executor.submit(_worker, item): item for item in pending}
        
        for future in as_completed(futures):
            idx, feats, err = future.result()
            if err:
                errors += 1
                
            new_rows.append(feats)
            done_count += 1
            
            # Print periodic streaming logs to console
            if done_count % LOG_EVERY == 0 or done_count == len(pending):
                elapsed = time.time() - start_time
                rate = done_count / elapsed if elapsed > 0 else 0
                eta_min = (len(pending) - done_count) / rate / 60 if rate > 0 else 0
                print(f"  📊 [{done_count:>6}/{len(pending)}]  Errors: {errors:<3}  Rate: {rate:.1f} URL/s  ETA: {eta_min:.1f} min")
                
            # Clean Checkpoint Serialization Fix: Merge historical data with newly calculated entries
            if done_count % CHECKPOINT_EVERY == 0:
                checkpoint_df = pd.DataFrame(historical_rows + new_rows)
                # Re-align column boundaries cleanly
                final_cols = ['url', 'label'] + [c for c in FEATURE_NAMES if c in checkpoint_df.columns]
                checkpoint_df = checkpoint_df.reindex(columns=final_cols)
                checkpoint_df.to_csv(output_path, index=False)
                print("  💾 Safe progression checkpoint saved to disk.")

    # 4. Final compilation and directory writeout
    final_df = pd.DataFrame(historical_rows + new_rows)
    final_cols = ['url', 'label'] + [c for c in FEATURE_NAMES if c in final_df.columns]
    final_df = final_df.reindex(columns=final_cols)
    final_df.to_csv(output_path, index=False)
    
    total_duration = (time.time() - start_time) / 60
    print("-" * 65)
    print(f"✅ Success: Feature matrix compilation finished!")
    print(f"  🔹 Output Location : {output_path}")
    print(f"  🔹 Total Rows Saved : {len(final_df):,}")
    print(f"  🔹 Pipeline Runtime : {total_duration:.2f} minutes")
    print(f"  🔹 Error Failures   : {errors}")
    print("-" * 65)

if __name__ == '__main__':
    run_parser = argparse.ArgumentParser()
    run_parser.add_argument('--input', required=True, help="Path to raw source text url files.")
    run_parser.add_argument('--output', required=True, help="Path where final engineered feature datasets save.")
    run_parser.add_argument('--workers', type=int, default=8, help="Number of concurrent network parsing threads.")
    parsed_args = run_parser.parse_args()
    
    run(parsed_args.input, parsed_args.output, parsed_args.workers)