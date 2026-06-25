# Evaluation Metrics for Phishing Detection

## 1. Accuracy
Formula: (TP + TN) / (TP + TN + FP + FN)
Meaning: Overall percentage of correct predictions

## 2. Precision
Formula: TP / (TP + FP)
Meaning: Of all URLs flagged as phishing, how many truly were?
Importance: HIGH — we don't want to block legitimate sites

## 3. Recall (Sensitivity)
Formula: TP / (TP + FN)
Meaning: Of all actual phishing URLs, how many did we catch?
Importance: HIGHEST — missing a phishing site is dangerous

## 4. F1-Score
Formula: 2 * (Precision * Recall) / (Precision + Recall)
Meaning: Harmonic mean — balances Precision and Recall

## 5. AUC-ROC
Meaning: Area Under the Receiver Operating Characteristic Curve
Range: 0.5 (random) to 1.0 (perfect)
Importance: Shows model performance across all thresholds

## Target Metrics for This Project
- Accuracy  : > 96%
- Precision : > 94%
- Recall    : > 96%   ← most important
- F1 Score  : > 95%
- AUC-ROC   : > 0.97
