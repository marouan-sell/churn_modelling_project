from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request


APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
MODEL_DIR = PROJECT_ROOT / "models"

MODEL_PATH = MODEL_DIR / "best_model_classifier.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"
FEATURE_COLUMNS_PATH = MODEL_DIR / "feature_columns.pkl"
MODEL_NAME_PATH = MODEL_DIR / "best_model_name.pkl"

TREE_MODELS = {"Random Forest", "Decision Tree"}
MODEL_ACCURACY = "95.77%"
MODEL_ROC_AUC = "95.13%"


app = Flask(__name__)


def load_artifacts() -> dict[str, Any]:
    """Load model artifacts once at application startup."""
    return {
        "model": joblib.load(MODEL_PATH),
        "scaler": joblib.load(SCALER_PATH),
        "feature_columns": joblib.load(FEATURE_COLUMNS_PATH),
        "model_name": joblib.load(MODEL_NAME_PATH),
    }


ARTIFACTS = load_artifacts()
model = ARTIFACTS["model"]
scaler = ARTIFACTS["scaler"]
feature_columns = ARTIFACTS["feature_columns"]
model_name = str(ARTIFACTS["model_name"])


def build_customer_frame(payload: dict[str, Any]) -> tuple[str, pd.DataFrame]:
    """Convert the JSON request payload into the raw model input frame."""
    client_name = str(payload.get("client_name", "Client")).strip() or "Client"
    gender_fr = str(payload["Gender"])

    data = pd.DataFrame([{
        "CreditScore": int(payload["CreditScore"]),
        "Geography": str(payload["Geography"]),
        "Gender": "Male" if gender_fr == "Homme" else "Female",
        "Age": int(payload["Age"]),
        "Tenure": int(payload["Tenure"]),
        "Balance": float(payload["Balance"]),
        "NumOfProducts": int(payload["NumOfProducts"]),
        "HasCrCard": int(payload["HasCrCard"]),
        "IsActiveMember": int(payload["IsActiveMember"]),
        "EstimatedSalary": float(payload["EstimatedSalary"]),
    }])

    return client_name, data


def engineer_features(data: pd.DataFrame) -> pd.DataFrame:
    """Apply the same feature engineering used during notebook training."""
    data = data.copy()
    data["BalanceIsZero"] = (data["Balance"] == 0).astype(int)
    data["Age_NumOfProducts"] = data["Age"] * data["NumOfProducts"]
    data["BalancePerProduct"] = data["Balance"] / data["NumOfProducts"].replace(0, 1)
    data["SalaryPerAge"] = data["EstimatedSalary"] / data["Age"].replace(0, np.nan)
    data["CreditScorePerAge"] = data["CreditScore"] / data["Age"].replace(0, np.nan)
    data["Active_Age"] = data["IsActiveMember"] * data["Age"]
    data["Inactive_Age"] = (1 - data["IsActiveMember"]) * data["Age"]
    data["HighProducts"] = (data["NumOfProducts"] >= 3).astype(int)
    data["GermanyHighBalance"] = (
        (data["Geography"] == "Germany")
        & (data["Balance"] > data["Balance"].median())
    ).astype(int)
    return data


def prepare_features(data: pd.DataFrame) -> pd.DataFrame | np.ndarray:
    """Encode, align, and optionally scale input features for inference."""
    data_encoded = pd.get_dummies(engineer_features(data), drop_first=True)
    data_encoded = data_encoded.replace([np.inf, -np.inf], np.nan).fillna(0)
    data_encoded = data_encoded.reindex(columns=feature_columns, fill_value=0)

    if any(tree_name in model_name for tree_name in TREE_MODELS):
        return data_encoded

    return scaler.transform(data_encoded.to_numpy())


def risk_from_probability(probability: float) -> tuple[str, str]:
    if probability < 40:
        return "Risque faible", "low"
    if probability < 70:
        return "Risque moyen", "medium"
    return "Risque élevé", "high"


@app.route("/")
def index():
    return render_template("index.html", model_name=model_name)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "model": model_name})


@app.route("/predict", methods=["POST"])
def predict():
    try:
        payload = request.get_json(force=True)
        client_name, customer_data = build_customer_frame(payload)
        data_prepared = prepare_features(customer_data)

        prediction = int(model.predict(data_prepared)[0])
        probability = round(float(model.predict_proba(data_prepared)[0][1]) * 100, 1)
        risk_level, risk_tier = risk_from_probability(probability)

        label = (
            "Client susceptible de quitter la banque"
            if prediction == 1
            else "Client susceptible de rester"
        )

        return jsonify({
            "success": True,
            "client_name": client_name,
            "prediction": prediction,
            "label": label,
            "probability": probability,
            "risk_level": risk_level,
            "risk_tier": risk_tier,
            "model_used": model_name,
            "model_accuracy": MODEL_ACCURACY,
            "model_roc_auc": MODEL_ROC_AUC,
            "probability_label": "Probabilité de quitter",
        })

    except KeyError as exc:
        return jsonify({"success": False, "error": f"Champ manquant : {exc}"}), 400
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
