# FluoroSafe — Fluoride Prediction and Water Safety

A full-stack web application that predicts fluoride concentration in drinking water using machine learning. The platform also provides comprehensive information on WHO/BIS safety limits, health effects of fluoride contamination, and preventive measures — aligned with **UN Sustainable Development Goal 6 (Clean Water and Sanitation)**.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Dataset](#dataset)
- [Model Details](#model-details)
- [License](#license)

---

## Overview

Excess fluoride in drinking water is a global health concern affecting millions. Traditional laboratory testing for fluoride is costly and inaccessible in many regions. FluoroSafe provides a **free, instant alternative** by using machine learning models trained on real sensor data to predict fluoride levels from four basic water quality parameters: pH, Electrical Conductivity (EC), Temperature, and Hardness.

The web interface allows users to input water parameters, receive instant fluoride estimates, and access educational content about fluoride safety — making water quality assessment accessible to everyone.

---

## Features

- **Fluoride Prediction** — Input pH, EC, Temperature, and Hardness to get a fluoride concentration prediction with safety classification (Normal / Borderline / Exceeds).
- **Interactive Water Gauge** — Visual representation of predicted fluoride level against WHO and BIS standards.
- **Remediation Alerts** — Actionable steps displayed when fluoride exceeds safe limits.
- **WHO and BIS Safety Limits** — Visual fluoride scale with international and national drinking water standards.
- **Health Effects Section** — Six detailed cards covering dental fluorosis, skeletal fluorosis, neurological effects, kidney damage, thyroid disruption, and reproductive issues.
- **Safety Precautions** — Practical steps for water treatment, testing, and dietary precautions.
- **Interactive Charts** — Fluoride distribution histogram and health risk vs concentration graph using Chart.js.
- **Animated UI** — Particle background, floating fluoride ions, molecule visualization, scroll-reveal animations, and card hover effects.

---

## Tech Stack

| Component   | Technology                           |
|-------------|--------------------------------------|
| Backend     | Python, Flask                        |
| ML Models   | Scikit-learn, XGBoost, TensorFlow    |
| Frontend    | HTML, CSS, JavaScript                |
| Charts      | Chart.js                             |
| Data        | Pandas, NumPy, OpenPyXL              |
| Fonts       | Google Fonts (Outfit, JetBrains Mono)|

---

## Project Structure

```
FLUORIDE-PROJECT/
├── app.py                          # Flask application with API endpoints
├── requirements.txt                # Python dependencies
├── data/
│   └── Bengaluru_Fluoride_SensorData_500.xlsx  # Sensor dataset
├── model/
│   ├── train.py                    # ML training pipeline (10+ models)
│   ├── fluoride_model.pkl          # Trained model artifact
│   └── results_summary.pkl         # Model comparison results
├── templates/
│   └── index.html                  # Main UI template
└── static/
    ├── css/
    │   └── style.css               # Styles and animations
    └── js/
        └── app.js                  # Frontend logic and charts
```

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/FLUORIDE-PROJECT.git
   cd FLUORIDE-PROJECT
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Train the model (if not already trained):
   ```bash
   python model/train.py
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

---

## Usage

1. Navigate to the **Predict** section on the website.
2. Enter the four water quality parameters (pH, EC, Temperature, Hardness) or use the quick sample presets.
3. Click **Predict Fluoride** to get the result.
4. The water gauge displays the predicted concentration against WHO and BIS limits.
5. If fluoride exceeds safe levels, a remediation alert with actionable steps is shown.

---

## Dataset

- **Source**: Real-time sensor data collected from water monitoring stations.
- **Size**: 500 records with timestamps.
- **Features**: pH, EC (uS/cm), Temperature (deg C), Hardness (mg/L).
- **Target**: Fluoride concentration (mg/L).
- **Engineered Features**: Hour, day of week, and month extracted from timestamps.

---

## Model Details

The training pipeline evaluates multiple models with hyperparameter tuning via GridSearchCV:

**Traditional ML Models**:
- Random Forest, Gradient Boosting, XGBoost, Extra Trees, AdaBoost, SVR, KNN, Ridge, Lasso, ElasticNet

**Deep Learning Models**:
- ANN, LSTM, Hybrid LSTM+ANN

**Best Model**: Extra Trees Regressor
- R2 Score: 0.9834
- MAE: 0.0380
- RMSE: 0.0474

Feature engineering includes polynomial features and time-based features for improved accuracy.

---

## License

This project is for educational and research purposes.
