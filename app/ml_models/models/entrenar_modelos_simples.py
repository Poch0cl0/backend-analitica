"""
Entrena 2 modelos simples (S-2 complementario) y guarda en app/ml_models/models/.

1. Prematuro → Regresión LOGÍSTICA  → prematuro_logistic.pkl
   Salida: probabilidad 0–1 (para S-4 y explicación en informe)

2. Semanas   → Regresión LINEAL     → semanas_lineal.pkl
   Salida: semanas estimadas 17–47 (mismo script, fácil de explicar)

Ejecutar:  python -m app.ml_models.models.entrenar_modelos_simples
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

BASE = Path(__file__).resolve().parent.parent
CSV = BASE / "datos_limpios" / "natality_entrenamiento.csv"
OUT = Path(__file__).resolve().parent

X_COLS = [
    "mager", "rf_ppterm", "dplural", "num_condiciones_cronicas",
    "infeccion_activa", "priorlive", "bmi", "cl_sim_mm", "combgest",
]
ENCODE_COLS = ["rf_ppterm"]


def preparar_X(df: pd.DataFrame, encoders: dict | None = None) -> tuple[pd.DataFrame, dict]:
    X = df[X_COLS].copy()
    encoders = encoders or {}
    for col in ENCODE_COLS:
        if col not in encoders:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            encoders[col] = le
        else:
            X[col] = encoders[col].transform(X[col].astype(str))
    return X, encoders


def _guardar(nombre: str, modelo, encoders: dict) -> Path:
    ruta = OUT / nombre
    joblib.dump({"modelo": modelo, "encoders": encoders, "x_cols": X_COLS}, ruta)
    return ruta


def main() -> None:
    df = pd.read_csv(CSV)
    X, encoders = preparar_X(df)

    # --- 1. Prematuro (regresión logística → probabilidad) ---
    y_pre = df["prematuro"].astype(int)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y_pre, test_size=0.2, random_state=42, stratify=y_pre
    )

    log_pre = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)
    log_pre.fit(X_tr, y_tr)
    pred = log_pre.predict(X_te)
    prob = log_pre.predict_proba(X_te)[:, 1]

    print("=== 1. Prematuro — Regresión logística ===")
    print("Accuracy:", round(accuracy_score(y_te, pred), 4))
    print("F1:", round(f1_score(y_te, pred, zero_division=0), 4))
    print("Prob. ejemplo:", np.round(prob[:3], 4))
    r1 = _guardar("prematuro_logistic.pkl", log_pre, encoders)
    print("Guardado:", r1.name, "(predict_proba -> S-4)\n")

    # --- 2. Semanas (regresión lineal → semanas) ---
    y_sem = df["oegest_comb"].astype(float)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y_sem, test_size=0.2, random_state=42)

    lin_sem = LinearRegression()
    lin_sem.fit(X_tr, y_tr)
    pred_sem = lin_sem.predict(X_te)

    print("=== 2. Semanas — Regresión lineal ===")
    print("MAE:", round(mean_absolute_error(y_te, pred_sem), 4), "semanas")
    print("RMSE:", round(np.sqrt(mean_squared_error(y_te, pred_sem)), 4), "semanas")
    print("R2:", round(r2_score(y_te, pred_sem), 4))
    r2 = _guardar("semanas_lineal.pkl", lin_sem, encoders)
    print("Guardado:", r2.name)

    print("\nListo. Archivos en app/ml_models/models/:")
    print("  - prematuro_logistic.pkl  (probabilidad prematuro -> S-4)")
    print("  - semanas_lineal.pkl      (semanas estimadas -> S-2 informe)")


if __name__ == "__main__":
    main()
