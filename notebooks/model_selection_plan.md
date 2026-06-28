# Model Selection Plan

## Why We Try Multiple Models
Different models have different strengths. We must compare them objectively on the same test set before selecting one for production.

---

## Models to Train

### Traditional Machine Learning (Week 4)
* **Logistic Regression:** Simple baseline, fast, highly interpretable.
* **Decision Tree:** Clear feature splits and easy to visualize.
* **Random Forest:** Ensemble of trees that handles noise and variance well.
* **XGBoost:** Gradient boosting, typically offers peak performance for tabular data.
* **LightGBM:** Highly efficient, faster alternative to XGBoost.
* **SVM (RBF Kernel):** Effective for complex decision boundaries when features are well-scaled.

### Deep Learning (Week 5)
* **Deep Neural Network (DNN):** 4 hidden layers to automatically learn non-linear feature combinations.

---

## Evaluation Protocol

| Stage | Dataset | Purpose |
| :--- | :--- | :--- |
| **Training** | `train.csv` | Initial model fitting and parameter learning. |
| **Validation** | `val.csv` | Hyperparameter tuning and model selection. |
| **Testing** | `test.csv` | Final evaluation (touched only once before deployment). |

### Target Metrics
We will evaluate performance across five key metrics:
* Accuracy
* Precision
* Recall
* F1-Score
* AUC-ROC

---

## Selection Criterion

> **Primary Metric:** The model with the highest **F1-Score** and **Recall** will be selected for production.
> 
> *Note on Project Logic:* Recall is our most critical metric. Missing a phishing site (False Negative) presents a major security risk, whereas a false alarm (False Positive) is simply a minor user inconvenience.