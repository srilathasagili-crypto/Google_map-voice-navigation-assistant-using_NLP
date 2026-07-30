"""
Intent classification module.
Trains TF-IDF + SVM (primary) and TF-IDF + Logistic Regression (baseline comparison)
on labeled voice-command style text, and saves the best model + vectorizer.
"""

import os
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

from preprocess import preprocess

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "intents.csv")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")


def load_data():
    df = pd.read_csv(DATA_PATH)
    df["clean_text"] = df["text"].apply(preprocess)
    return df


def train_and_compare():
    df = load_data()

    X_train, X_test, y_train, y_test = train_test_split(
        df["clean_text"], df["intent"],
        test_size=0.2, random_state=42, stratify=df["intent"]
    )

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    results = {}

    # Baseline: Logistic Regression
    log_reg = LogisticRegression(max_iter=1000)
    log_reg.fit(X_train_vec, y_train)
    lr_preds = log_reg.predict(X_test_vec)
    lr_acc = accuracy_score(y_test, lr_preds)
    results["logistic_regression"] = {
        "model": log_reg,
        "accuracy": lr_acc,
        "report": classification_report(y_test, lr_preds, zero_division=0),
    }

    # Primary model: SVM
    svm = SVC(kernel="linear", probability=True)
    svm.fit(X_train_vec, y_train)
    svm_preds = svm.predict(X_test_vec)
    svm_acc = accuracy_score(y_test, svm_preds)
    results["svm"] = {
        "model": svm,
        "accuracy": svm_acc,
        "report": classification_report(y_test, svm_preds, zero_division=0),
    }

    print("=" * 60)
    print("Logistic Regression (baseline) — Accuracy: {:.2%}".format(lr_acc))
    print(results["logistic_regression"]["report"])
    print("=" * 60)
    print("SVM (primary model) — Accuracy: {:.2%}".format(svm_acc))
    print(results["svm"]["report"])
    print("=" * 60)

    # Pick the better performing model to deploy in the pipeline
    best_name = "svm" if svm_acc >= lr_acc else "logistic_regression"
    best_model = results[best_name]["model"]
    print(f"Selected model for deployment: {best_name}")

    # Confusion matrix for the deployed model — key evaluation artifact
    labels = sorted(df["intent"].unique())
    best_preds = svm_preds if best_name == "svm" else lr_preds
    cm = confusion_matrix(y_test, best_preds, labels=labels)
    print("\nConfusion Matrix ({}):".format(best_name))
    print("Labels:", labels)
    for row_label, row in zip(labels, cm):
        print(f"  {row_label:20s} {row}")

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(best_model, os.path.join(MODEL_DIR, "intent_classifier.pkl"))
    joblib.dump(vectorizer, os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl"))
    print(f"Saved model + vectorizer to {MODEL_DIR}/")

    return best_model, vectorizer


class IntentClassifier:
    """Loads the trained model for inference in the main pipeline."""

    def __init__(self, confidence_threshold: float = 0.35):
        model_path = os.path.join(MODEL_DIR, "intent_classifier.pkl")
        vec_path = os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl")
        self.model = joblib.load(model_path)
        self.vectorizer = joblib.load(vec_path)
        self.confidence_threshold = confidence_threshold

    def predict(self, text: str):
        clean = preprocess(text)
        vec = self.vectorizer.transform([clean])
        pred = self.model.predict(vec)[0]

        # probability/confidence — SVC needs probability=True (set during training)
        if hasattr(self.model, "predict_proba"):
            proba = self.model.predict_proba(vec)[0]
            confidence = max(proba)
        else:
            confidence = 1.0  # fallback if model has no probability output

        if confidence < self.confidence_threshold:
            return {"intent": "unknown", "confidence": float(confidence)}

        return {"intent": pred, "confidence": float(confidence)}


if __name__ == "__main__":
    train_and_compare()
