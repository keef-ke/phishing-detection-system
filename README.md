# AI-Based Phishing Website Detection System
Final Year University Project

## Project Description
A machine learning system that detects phishing URLs in real time using 43
engineered features extracted from URL lexical properties, domain registration
data, and live webpage content.

## Team
- Student: [Nyagilo Byron]
- Supervisor: [MR Muchiri Nyaga]

## Project Timeline
- Week 1: Setup, Research, Literature Review ✅
- Week 2: Data Collection and Preprocessing 
- Week 3: Feature Engineering
- Week 4: ML Model Development
- Week 5: Deep Learning Model
- Week 6: Flask Backend API
- Week 7: Frontend and Testing
- Week 8: Report and Presentation

## Tech Stack
- Language: Python 3.14.5
- ML: Scikit-learn, XGBoost, LightGBM, TensorFlow/Keras
- Backend: Flask + SQLite
- Frontend: HTML5, CSS3 (Bootstrap 5), JavaScript
- Feature Extraction: BeautifulSoup4, Requests, python-whois, dnspython

## How to Run (complete instructions in Week 6)
```bash
conda activate phishing_env
python src/api/app.py
```
Then open http://localhost:5000 in your browser.

## Dataset Sources
- PhishTank: https://www.phishtank.com
- Tranco Top 1M: https://tranco-list.eu
- UCI ML Repository: https://archive.ics.uci.edu
