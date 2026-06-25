"""Convert UCI ARFF dataset to CSV format"""
import pandas as pd
import os

# Define explicit paths relative to your project structure
input_path = 'dataset/raw/Training Dataset.arff'
output_path = 'dataset/raw/uci_phishing.csv'

# Quick check to ensure the file is where we think it is
if not os.path.exists(input_path):
    raise FileNotFoundError(f"Could not find the ARFF file at: {os.path.abspath(input_path)}")

data_lines = []
in_data_section = False
attributes = []

with open(input_path, 'r') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
            
        if line.lower().startswith('@attribute'):
            parts = line.split()
            # Remove potential quotes around the attribute name (e.g., 'URL_Length' -> URL_Length)
            attr_name = parts[1].strip("'\"")
            attributes.append(attr_name)
            
        elif line.lower().startswith('@data'):
            in_data_section = True
            
        elif in_data_section and not line.startswith('%'):
            data_lines.append(line.split(','))

# Create DataFrame and save
df = pd.DataFrame(data_lines, columns=attributes)
df.to_csv(output_path, index=False)

print(f"Converted successfully! Shape: {df.shape}")
print("\nFirst 3 rows:")
print(df.head(3))