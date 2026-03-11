"""
Fluoride Prediction - Flask Backend
Serves the trained ML model via a REST API and renders the web UI.
"""

import os
import json
import numpy as np
import joblib
from datetime import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ── Load Model ───────────────────────────────────────────────────────────
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model")
artifact = joblib.load(os.path.join(MODEL_DIR, "fluoride_model.pkl"))

model = artifact["model"]
scaler = artifact["scaler"]
model_name = artifact["model_name"]
model_r2 = artifact["r2"]
model_mae = artifact["mae"]
model_rmse = artifact["rmse"]
feature_names = artifact["feature_names"]  # ['pH', 'EC', 'Temp', 'Hardness', 'hour', 'day_of_week', 'month']

# Load results summary for UI display
results_path = os.path.join(MODEL_DIR, "results_summary.pkl")
results_summary = joblib.load(results_path) if os.path.exists(results_path) else []

print(f"\n[OK] Loaded model: {model_name}")
print(f"     R2={model_r2:.4f}, MAE={model_mae:.4f}, RMSE={model_rmse:.4f}")
print(f"     Features: {feature_names}\n")


# ── Routes ───────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        ph = float(data["ph"])
        ec = float(data["ec"])
        temperature = float(data["temperature"])
        hardness = float(data["hardness"])

        # Extract time-based features from current time
        now = datetime.now()
        hour = now.hour
        day_of_week = now.weekday()
        month = now.month

        # Build feature vector: [pH, EC, Temp, Hardness, hour, day_of_week, month]
        features = np.array([[ph, ec, temperature, hardness, hour, day_of_week, month]])

        # Scale
        features_scaled = scaler.transform(features)

        # Predict
        prediction = model.predict(features_scaled)[0]
        prediction = max(0, round(float(prediction), 4))

        # BIS classification
        if prediction <= 1.0:
            status = "NORMAL"
            status_label = "Within BIS Limit"
        elif prediction <= 1.5:
            status = "BORDERLINE"
            status_label = "Borderline (BIS Limit)"
        else:
            status = "EXCEEDS"
            status_label = "Exceeds BIS Limit"

        return jsonify({
            "success": True,
            "fluoride": prediction,
            "status": status,
            "status_label": status_label,
            "model_name": model_name,
            "model_r2": round(model_r2, 4),
            "model_mae": round(model_mae, 4),
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/model-info", methods=["GET"])
def model_info():
    return jsonify({
        "model_name": model_name,
        "r2": round(model_r2, 4),
        "mae": round(model_mae, 4),
        "rmse": round(model_rmse, 4),
        "features": feature_names,
        "results": results_summary,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
