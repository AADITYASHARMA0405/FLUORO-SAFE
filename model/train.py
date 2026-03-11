"""
Fluoride Prediction Model - Training Pipeline
Trains traditional ML models + Deep Learning (ANN, LSTM, Hybrid LSTM+ANN),
selects the best, and exports it for production use.
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler, MinMaxScaler, PolynomialFeatures
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor,
    ExtraTreesRegressor,
    StackingRegressor,
)
from sklearn.linear_model import Ridge
from xgboost import XGBRegressor
import joblib

warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import tensorflow as tf
tf.get_logger().setLevel("ERROR")
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import (
    Dense, LSTM, Dropout, BatchNormalization, Input, Concatenate, Reshape
)
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam

# -- Paths ----------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "Bengaluru_Fluoride_SensorData_500 (3).xlsx")
MODEL_DIR = os.path.join(BASE_DIR, "model")
MODEL_PATH = os.path.join(MODEL_DIR, "fluoride_model.pkl")

FEATURES = ["pH", "EC (uS/cm)", "Temperature (degC)", "Hardness (mg/L)"]
FEATURES_ORIG = ["pH", "EC (µS/cm)", "Temperature (°C)", "Hardness (mg/L)"]
TARGET = "Fluoride (mg/L)"

LOOKBACK = 5  # LSTM sequence length


# -- 1. Load & Prepare Data -----------------------------------------------
def load_data():
    df = pd.read_excel(DATA_PATH, engine="openpyxl")
    # Rename columns to ASCII-safe names internally
    col_map = dict(zip(FEATURES_ORIG, FEATURES))
    df = df.rename(columns=col_map)
    print(f"[OK] Loaded dataset: {df.shape[0]} rows, {df.shape[1]} columns")

    # Sort by timestamp for temporal ordering
    df["Date & Time"] = pd.to_datetime(df["Date & Time"])
    df = df.sort_values("Date & Time").reset_index(drop=True)
    print(f"[OK] Sorted by timestamp (earliest: {df['Date & Time'].iloc[0]}, latest: {df['Date & Time'].iloc[-1]})")

    # Extract time-based features
    df["hour"] = df["Date & Time"].dt.hour
    df["day_of_week"] = df["Date & Time"].dt.dayofweek
    df["month"] = df["Date & Time"].dt.month

    # Drop missing values
    all_features = FEATURES + ["hour", "day_of_week", "month"]
    df = df[all_features + [TARGET]].dropna()

    X = df[all_features].values
    y = df[TARGET].values
    return X, y, all_features


# -- 2. Create LSTM sequences ---------------------------------------------
def create_sequences(X, y, lookback=LOOKBACK):
    """Create sliding window sequences for LSTM."""
    Xs, ys = [], []
    for i in range(lookback, len(X)):
        Xs.append(X[i - lookback:i])
        ys.append(y[i])
    return np.array(Xs), np.array(ys)


# -- 3. Traditional ML Models ---------------------------------------------
def train_traditional_models(X_train, X_test, y_train, y_test):
    models_cfg = {
        "Random Forest": {
            "model": RandomForestRegressor(random_state=42),
            "params": {
                "n_estimators": [200, 500],
                "max_depth": [None, 15, 25],
                "min_samples_split": [2, 5],
                "min_samples_leaf": [1, 2],
            },
        },
        "Gradient Boosting": {
            "model": GradientBoostingRegressor(random_state=42),
            "params": {
                "n_estimators": [200, 500],
                "learning_rate": [0.01, 0.05, 0.1],
                "max_depth": [3, 5, 7],
                "subsample": [0.8, 1.0],
            },
        },
        "XGBoost": {
            "model": XGBRegressor(random_state=42, verbosity=0),
            "params": {
                "n_estimators": [200, 500],
                "learning_rate": [0.01, 0.05, 0.1],
                "max_depth": [3, 5, 7],
                "subsample": [0.8, 1.0],
                "colsample_bytree": [0.8, 1.0],
            },
        },
        "Extra Trees": {
            "model": ExtraTreesRegressor(random_state=42),
            "params": {
                "n_estimators": [200, 500],
                "max_depth": [None, 15, 25],
                "min_samples_split": [2, 5],
            },
        },
    }

    results = []
    print("=" * 78)
    print(f"{'MODEL':<24} {'R2 (test)':>10} {'MAE':>10} {'RMSE':>10} {'CV R2 (5f)':>12}")
    print("=" * 78)

    for name, cfg in models_cfg.items():
        sys.stdout.write(f"  Training {name}...")
        sys.stdout.flush()

        grid = GridSearchCV(
            cfg["model"], cfg["params"],
            cv=5, scoring="r2", n_jobs=-1, refit=True,
        )
        grid.fit(X_train, y_train)
        model = grid.best_estimator_

        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="r2")
        cv_mean = cv_scores.mean()

        results.append({
            "name": name, "model": model, "type": "traditional",
            "r2": r2, "mae": mae, "rmse": rmse, "cv_r2": cv_mean,
        })
        print(f"\r  {name:<24} {r2:>10.6f} {mae:>10.6f} {rmse:>10.6f} {cv_mean:>12.6f}")

    return results


# -- 4. ANN Model ---------------------------------------------------------
def build_ann(input_dim):
    model = Sequential([
        Input(shape=(input_dim,)),
        Dense(128, activation="relu"),
        BatchNormalization(),
        Dropout(0.3),
        Dense(64, activation="relu"),
        BatchNormalization(),
        Dropout(0.2),
        Dense(32, activation="relu"),
        BatchNormalization(),
        Dense(16, activation="relu"),
        Dense(1, activation="linear"),
    ])
    model.compile(optimizer=Adam(learning_rate=0.001), loss="mse", metrics=["mae"])
    return model


def train_ann(X_train, X_test, y_train, y_test):
    print("\n  Training ANN...", end="", flush=True)
    model = build_ann(X_train.shape[1])

    callbacks = [
        EarlyStopping(patience=30, restore_best_weights=True, monitor="val_loss"),
        ReduceLROnPlateau(patience=10, factor=0.5, min_lr=1e-6),
    ]
    model.fit(
        X_train, y_train,
        epochs=300, batch_size=16,
        validation_split=0.15,
        callbacks=callbacks,
        verbose=0,
    )

    y_pred = model.predict(X_test, verbose=0).flatten()
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    print(f"\r  {'ANN':<24} {r2:>10.6f} {mae:>10.6f} {rmse:>10.6f} {'N/A':>12}")
    return model, {"name": "ANN", "model": model, "type": "ann", "r2": r2, "mae": mae, "rmse": rmse, "cv_r2": 0}


# -- 5. LSTM Model ---------------------------------------------------------
def build_lstm(lookback, n_features):
    model = Sequential([
        Input(shape=(lookback, n_features)),
        LSTM(64, return_sequences=True),
        Dropout(0.3),
        LSTM(32, return_sequences=False),
        Dropout(0.2),
        Dense(32, activation="relu"),
        BatchNormalization(),
        Dense(16, activation="relu"),
        Dense(1, activation="linear"),
    ])
    model.compile(optimizer=Adam(learning_rate=0.001), loss="mse", metrics=["mae"])
    return model


def train_lstm(X_train_seq, X_test_seq, y_train_seq, y_test_seq, n_features):
    print(f"  Training LSTM (lookback={LOOKBACK})...", end="", flush=True)
    model = build_lstm(LOOKBACK, n_features)

    callbacks = [
        EarlyStopping(patience=30, restore_best_weights=True, monitor="val_loss"),
        ReduceLROnPlateau(patience=10, factor=0.5, min_lr=1e-6),
    ]
    model.fit(
        X_train_seq, y_train_seq,
        epochs=300, batch_size=16,
        validation_split=0.15,
        callbacks=callbacks,
        verbose=0,
    )

    y_pred = model.predict(X_test_seq, verbose=0).flatten()
    r2 = r2_score(y_test_seq, y_pred)
    mae = mean_absolute_error(y_test_seq, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test_seq, y_pred))

    print(f"\r  {'LSTM':<24} {r2:>10.6f} {mae:>10.6f} {rmse:>10.6f} {'N/A':>12}")
    return model, {"name": "LSTM", "model": model, "type": "lstm", "r2": r2, "mae": mae, "rmse": rmse, "cv_r2": 0}


# -- 6. Hybrid LSTM + ANN Model -------------------------------------------
def build_hybrid(lookback, n_features):
    """LSTM branch processes sequences, Dense branch processes current values."""
    # LSTM branch
    lstm_input = Input(shape=(lookback, n_features), name="lstm_input")
    x1 = LSTM(64, return_sequences=True)(lstm_input)
    x1 = Dropout(0.3)(x1)
    x1 = LSTM(32)(x1)
    x1 = Dropout(0.2)(x1)

    # Dense (ANN) branch for current timestep features
    dense_input = Input(shape=(n_features,), name="dense_input")
    x2 = Dense(64, activation="relu")(dense_input)
    x2 = BatchNormalization()(x2)
    x2 = Dropout(0.3)(x2)
    x2 = Dense(32, activation="relu")(x2)

    # Merge
    merged = Concatenate()([x1, x2])
    x = Dense(64, activation="relu")(merged)
    x = BatchNormalization()(x)
    x = Dropout(0.2)(x)
    x = Dense(32, activation="relu")(x)
    x = Dense(16, activation="relu")(x)
    output = Dense(1, activation="linear")(x)

    model = Model(inputs=[lstm_input, dense_input], outputs=output)
    model.compile(optimizer=Adam(learning_rate=0.001), loss="mse", metrics=["mae"])
    return model


def train_hybrid(X_train_seq, X_test_seq, X_train_curr, X_test_curr, y_train_seq, y_test_seq, n_features):
    print(f"  Training Hybrid LSTM+ANN...", end="", flush=True)
    model = build_hybrid(LOOKBACK, n_features)

    callbacks = [
        EarlyStopping(patience=30, restore_best_weights=True, monitor="val_loss"),
        ReduceLROnPlateau(patience=10, factor=0.5, min_lr=1e-6),
    ]
    model.fit(
        [X_train_seq, X_train_curr], y_train_seq,
        epochs=300, batch_size=16,
        validation_split=0.15,
        callbacks=callbacks,
        verbose=0,
    )

    y_pred = model.predict([X_test_seq, X_test_curr], verbose=0).flatten()
    r2 = r2_score(y_test_seq, y_pred)
    mae = mean_absolute_error(y_test_seq, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test_seq, y_pred))

    print(f"\r  {'Hybrid LSTM+ANN':<24} {r2:>10.6f} {mae:>10.6f} {rmse:>10.6f} {'N/A':>12}")
    return model, {"name": "Hybrid LSTM+ANN", "model": model, "type": "hybrid", "r2": r2, "mae": mae, "rmse": rmse, "cv_r2": 0}


# -- 7. Main ---------------------------------------------------------------
def main():
    print("\n" + "=" * 78)
    print("  FLUORIDE PREDICTION - MODEL TRAINING PIPELINE")
    print("  (Traditional ML + LSTM + ANN + Hybrid LSTM+ANN)")
    print("=" * 78 + "\n")

    # Load data (sorted by timestamp)
    X, y, feature_names = load_data()
    n_features = X.shape[1]
    print(f"[OK] Total features: {n_features} ({', '.join(feature_names)})\n")

    # Scale data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # ---- Traditional ML (non-temporal split) ----
    # Use last 20% as test to respect time ordering
    split_idx = int(len(X_scaled) * 0.8)
    X_train_flat = X_scaled[:split_idx]
    X_test_flat = X_scaled[split_idx:]
    y_train_flat = y[:split_idx]
    y_test_flat = y[split_idx:]

    print(f"[OK] Temporal split: {X_train_flat.shape[0]} train / {X_test_flat.shape[0]} test\n")

    # -- Phase 1: Traditional ML --
    print("-- PHASE 1: Traditional ML Models --\n")
    all_results = train_traditional_models(X_train_flat, X_test_flat, y_train_flat, y_test_flat)

    # -- Phase 2: Deep Learning --
    print("\n-- PHASE 2: Deep Learning Models --\n")

    # ANN (uses flat features)
    ann_model, ann_result = train_ann(X_train_flat, X_test_flat, y_train_flat, y_test_flat)
    all_results.append(ann_result)

    # Create LSTM sequences from the FULL scaled data, then split
    X_seq, y_seq = create_sequences(X_scaled, y, lookback=LOOKBACK)
    seq_split_idx = split_idx - LOOKBACK
    X_train_seq = X_seq[:seq_split_idx]
    X_test_seq = X_seq[seq_split_idx:]
    y_train_seq = y_seq[:seq_split_idx]
    y_test_seq = y_seq[seq_split_idx:]

    # Current-timestep features for hybrid (last element of each sequence)
    X_train_curr = X_train_seq[:, -1, :]
    X_test_curr = X_test_seq[:, -1, :]

    print(f"  LSTM sequences: {X_train_seq.shape[0]} train / {X_test_seq.shape[0]} test (lookback={LOOKBACK})")

    # LSTM
    lstm_model, lstm_result = train_lstm(X_train_seq, X_test_seq, y_train_seq, y_test_seq, n_features)
    all_results.append(lstm_result)

    # Hybrid LSTM+ANN
    hybrid_model, hybrid_result = train_hybrid(
        X_train_seq, X_test_seq, X_train_curr, X_test_curr,
        y_train_seq, y_test_seq, n_features
    )
    all_results.append(hybrid_result)

    # -- Find best model --
    print("\n" + "=" * 78)
    best = max(all_results, key=lambda x: x["r2"])
    print(f"\n  >>> BEST MODEL: {best['name']}")
    print(f"      R2   = {best['r2']:.6f}")
    print(f"      MAE  = {best['mae']:.6f}")
    print(f"      RMSE = {best['rmse']:.6f}")
    print("=" * 78 + "\n")

    # Save the best model
    artifact = {
        "model_name": best["name"],
        "model_type": best["type"],
        "scaler": scaler,
        "features": FEATURES,
        "features_display": ["pH", "EC (uS/cm)", "Temperature (degC)", "Hardness (mg/L)"],
        "r2": best["r2"],
        "mae": best["mae"],
        "rmse": best["rmse"],
        "lookback": LOOKBACK,
        "n_features": n_features,
        "feature_names": feature_names,
    }

    if best["type"] == "traditional":
        artifact["model"] = best["model"]
        joblib.dump(artifact, MODEL_PATH)
    elif best["type"] == "ann":
        ann_path = os.path.join(MODEL_DIR, "fluoride_ann.keras")
        best["model"].save(ann_path)
        artifact["keras_model_path"] = "fluoride_ann.keras"
        joblib.dump(artifact, MODEL_PATH)
    elif best["type"] == "lstm":
        lstm_path = os.path.join(MODEL_DIR, "fluoride_lstm.keras")
        best["model"].save(lstm_path)
        artifact["keras_model_path"] = "fluoride_lstm.keras"
        joblib.dump(artifact, MODEL_PATH)
    elif best["type"] == "hybrid":
        hybrid_path = os.path.join(MODEL_DIR, "fluoride_hybrid.keras")
        best["model"].save(hybrid_path)
        artifact["keras_model_path"] = "fluoride_hybrid.keras"
        joblib.dump(artifact, MODEL_PATH)

    print(f"[OK] Model saved to {MODEL_PATH}")
    print(f"     Size: {os.path.getsize(MODEL_PATH) / 1024:.1f} KB\n")

    # Also save all results for the UI to display
    results_summary = []
    for r in sorted(all_results, key=lambda x: x["r2"], reverse=True):
        results_summary.append({
            "name": r["name"], "type": r["type"],
            "r2": round(r["r2"], 6), "mae": round(r["mae"], 6), "rmse": round(r["rmse"], 6),
        })
    joblib.dump(results_summary, os.path.join(MODEL_DIR, "results_summary.pkl"))
    print("[OK] Results summary saved.\n")


if __name__ == "__main__":
    main()
