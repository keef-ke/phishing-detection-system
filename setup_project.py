"""
setup_project.py
Run this script to verify your full project environment is correct.
Usage: python setup_project.py
"""

import os
import sys

# Matches your exact VS Code directory structure
FOLDERS = [
    "database/dataset/raw", 
    "database/dataset/processed", 
    "database/dataset/exports",
    "notebooks", 
    "src", 
    "frontend", 
    "models", 
    "reports", 
    "tests"
]

# Using 'dnspython' (the modern package) instead of 'dns'
REQUIRED_LIBS = [
    "numpy", "pandas", "scikit-learn", "matplotlib", "seaborn",
    "xgboost", "flask", "requests", "bs4", "tldextract", 
    "whois", "dnspython", "shap", "joblib"
]

def check_python():
    major, minor, micro = sys.version_info[:3]
    print(f"Python {major}.{minor}.{micro} ", end="")
    if major < 3 or minor < 9:
        print("❌ Need 3.9+")
        sys.exit(1)
    print("✅")

def check_folders():
    for f in FOLDERS:
        exists = os.path.isdir(f)
        print(f"  {'✅' if exists else '❌'} {f}")
        if not exists:
            os.makedirs(f, exist_ok=True)
            print(f"     → Created automatically")

def check_libraries():
    missing = []
    for lib in REQUIRED_LIBS:
        try:
            # Map standard installation names to their python script import names
            if lib == "scikit-learn":
                import_name = "sklearn"
            elif lib == "dnspython":
                import_name = "dns"
            else:
                import_name = lib
                
            __import__(import_name)
            print(f"  ✅ {lib}")
        except ImportError:
            print(f"  ❌ {lib} MISSING")
            missing.append(lib)
    return missing

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  Project Environment Verification")
    print("="*55)
    
    print("\n[1] Python version:")
    check_python()
    
    print("\n[2] Folder structure:")
    check_folders()
    
    print("\n[3] Required libraries:")
    missing = check_libraries()
    
    print("\n" + "="*55)
    if missing:
        print(f"⚠️  Missing libraries detected! Run this to fix:")
        print(f"pip install {' '.join(missing)}")
    else:
        print("🎉 All checks passed! Your environment is perfect.")
    print("="*55)