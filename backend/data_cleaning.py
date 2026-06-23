import os
import pandas as pd


def clean_dataset():
    """Clean raw URL dataset and save processed CSV.

    Finds the dataset relative to this file, removes duplicates and NaNs,
    and writes the cleaned CSV to the processed folder.
    """
    print("---Starting dataset cleaning process---")

    # Base dir is two levels up from this file (backend -> project root)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_data_path = os.path.join(base_dir, "dataset", "raw", "legitimate_and_phishing_URL_dataset.csv")
    processed_data_path = os.path.join(base_dir, "dataset", "processed", "cleaned_urls.csv")

    # Check if the raw data file exists before continuing
    if not os.path.exists(raw_data_path):
        print(f"Error: Could not find the raw data file at {raw_data_path}")
        return

    # Load the dataset
    df = pd.read_csv(raw_data_path)
    print("Original Dataset Shape:", df.shape)

    # Drop duplicates and empty rows
    df = df.drop_duplicates().dropna()
    print("Cleaned Dataset Shape:", df.shape)

    # Ensure processed directory exists
    os.makedirs(os.path.dirname(processed_data_path), exist_ok=True)

    # Save cleaned dataset into your processed data folder
    df.to_csv(processed_data_path, index=False)
    print(f"Cleaning completed. Saved to: {processed_data_path}")


if __name__ == "__main__":
    clean_dataset()
