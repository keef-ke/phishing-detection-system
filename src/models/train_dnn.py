"""
train_dnn.py
Builds and trains a Deep Neural Network using TensorFlow/Keras.
Handles missing test splits gracefully by falling back to validation matrices.
Run: python src/models/train_dnn.py
"""
import os
import sys
import joblib
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
import keras
from keras import layers
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_auc_score
)
import seaborn as sns

# Clean system path injection for root directory imports
sys.path.insert(0, os.path.abspath('.'))
from src.models.preprocess import load_splits, scale, apply_smote

MODELS_DIR = 'models'
REPORTS    = 'reports'
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(REPORTS, exist_ok=True)


def build_model(n_features):
    """4-layer DNN with BatchNormalization and Dropout."""
    model = keras.Sequential([
        layers.Input(shape=(n_features,)),

        layers.Dense(256, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.3),

        layers.Dense(128, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.3),

        layers.Dense(64, activation='relu'),
        layers.Dropout(0.2),

        layers.Dense(32, activation='relu'),

        layers.Dense(1, activation='sigmoid'),   # Binary output
    ], name='PhishingDNN')
    return model


def plot_history(history):
    """Plot optimization trajectory loss and accuracy graphs."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # Loss tracking
    axes[0].plot(history.history['loss'],     label='Train Loss')
    axes[0].plot(history.history['val_loss'], label='Val Loss')
    axes[0].set_title('Loss Curve', fontweight='bold')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Binary Crossentropy')
    axes[0].legend()

    # Accuracy tracking
    axes[1].plot(history.history['accuracy'],     label='Train Acc')
    axes[1].plot(history.history['val_accuracy'], label='Val Acc')
    axes[1].set_title('Accuracy Curve', fontweight='bold')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Accuracy')
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(f'{REPORTS}/dnn_training_curves.png', dpi=150)
    plt.close()
    print("📈 Training curves saved to reports/dnn_training_curves.png")


def plot_cm(y_true, y_pred, title, split_name):
    """Generate visual data mapping for model confusion classification matrix."""
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Oranges',
                xticklabels=['Legit', 'Phishing'],
                yticklabels=['Legit', 'Phishing'], ax=ax)
    ax.set_title(f'Confusion Matrix ({split_name}) — {title}', fontweight='bold')
    ax.set_xlabel('Predicted')
    ax.set_ylabel('Actual')
    plt.tight_layout()
    plt.savefig(f'{REPORTS}/cm_dnn_{split_name}.png', dpi=150)
    plt.close()
    print(f"📊 Confusion matrix saved to reports/cm_dnn_{split_name}.png")


def main():
    print("=" * 65)
    print(" 🧠 DEEP NEURAL NETWORK ARCHITECTURE & OPTIMIZATION")
    print("=" * 65)
    tf.random.set_seed(42)

    # Load splits via your core preprocess engine
    X_tr, y_tr, X_val, y_val, X_te, y_te, features = load_splits()
    X_tr_s, X_val_s, X_te_s, scaler = scale(X_tr, X_val, X_te)
    X_tr_s, y_tr = apply_smote(X_tr_s, y_tr)
    n_features = X_tr_s.shape[1]

    # Verify structural data alignment before execution
    has_test = X_te_s is not None
    eval_matrix = X_te_s if has_test else X_val_s
    eval_labels = y_te if has_test else y_val
    target_split_name = 'TEST' if has_test else 'VALIDATION'

    # Build network graph summary
    model = build_model(n_features)
    model.summary()

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='binary_crossentropy',
        metrics=['accuracy',
                 keras.metrics.AUC(name='auc'),
                 keras.metrics.Precision(name='precision'),
                 keras.metrics.Recall(name='recall')],
    )

    # Training optimization callbacks
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor='val_auc', patience=10, restore_best_weights=True, mode='max'),
        keras.callbacks.ModelCheckpoint(
            f'{MODELS_DIR}/dnn_best.keras',  # Switched extension to standard native .keras
            monitor='val_auc', save_best_only=True, mode='max', verbose=1),
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6, verbose=1),
    ]

    print("\n🚀 Starting training loops and optimization splits...")
    history = model.fit(
        X_tr_s, y_tr,
        validation_data=(X_val_s, y_val),
        epochs=100,
        batch_size=64,
        callbacks=callbacks,
        verbose=1,
    )

    # Render training trajectories to file
    plot_history(history)

    # Run structural metric scoring
    print(f"\n── {target_split_name} Set Evaluation Matrix ──")
    y_prob = model.predict(eval_matrix).ravel()
    y_pred = (y_prob >= 0.5).astype(int)

    print(f"   ▪️ Accuracy  : {accuracy_score(eval_labels, y_pred) * 100:.2f}%")
    print(f"   ▪️ Precision : {precision_score(eval_labels, y_pred) * 100:.2f}%")
    print(f"   ▪️ Recall    : {recall_score(eval_labels, y_pred) * 100:.2f}%")
    print(f"   ▪️ F1 Score  : {f1_score(eval_labels, y_pred) * 100:.2f}%")
    print(f"   ▪️ AUC-ROC   : {roc_auc_score(eval_labels, y_prob):.4f}")

    print(f"\n── Full Classification Report ({target_split_name}) ──")
    print(classification_report(eval_labels, y_pred, target_names=['Legitimate', 'Phishing']))

    plot_cm(eval_labels, y_pred, 'DNN', target_split_name.lower())

    # Export finalized training metrics to disk
    model.save(f'{MODELS_DIR}/dnn_model.keras')
    print(f"\n✅ Production DNN saved successfully to: models/dnn_model.keras\n")


if __name__ == '__main__':
    main()