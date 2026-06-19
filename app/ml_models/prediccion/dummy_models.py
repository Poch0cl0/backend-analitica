"""
Genera modelos dummy para desarrollo cuando los .pkl reales no están disponibles.
Uso: python app/ml_models/prediccion/dummy_models.py
"""

import math
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import LabelEncoder


def _modelo_prematuro_dummy() -> dict:
    """Logistic regression entrenada con datos sintéticos representativos."""
    X = np.array([
        [20, 0, 1, 0, 0, 1, 22.0, 35.0, 38],
        [30, 1, 1, 1, 0, 0, 28.0, 22.0, 30],
        [25, 0, 2, 2, 1, 1, 31.0, 18.0, 28],
        [35, 1, 1, 3, 1, 0, 35.0, 15.0, 24],
        [22, 0, 1, 0, 0, 2, 21.0, 38.0, 39],
        [28, 0, 1, 1, 0, 1, 24.0, 30.0, 36],
        [32, 1, 2, 2, 1, 0, 33.0, 20.0, 26],
        [19, 0, 1, 0, 0, 0, 20.5, 37.0, 40],
    ], dtype=float)
    y = np.array([0, 1, 1, 1, 0, 0, 1, 0])

    enc = LabelEncoder().fit(["N", "Y"])
    modelo = LogisticRegression(random_state=42, max_iter=200)
    modelo.fit(X, y)

    return {
        "modelo": modelo,
        "x_cols": ["mager", "rf_ppterm", "dplural", "num_condiciones_cronicas",
                   "infeccion_activa", "priorlive", "bmi", "cl_sim_mm", "combgest"],
        "encoders": {"rf_ppterm": enc},
    }


def _modelo_semanas_dummy() -> dict:
    """Linear regression para estimar semanas de gestación."""
    X = np.array([
        [20, 0, 1, 0, 0, 1, 22.0, 35.0, 38],
        [30, 1, 1, 1, 0, 0, 28.0, 22.0, 30],
        [25, 0, 2, 2, 1, 1, 31.0, 18.0, 28],
        [35, 1, 1, 3, 1, 0, 35.0, 15.0, 24],
        [22, 0, 1, 0, 0, 2, 21.0, 38.0, 39],
        [28, 0, 1, 1, 0, 1, 24.0, 30.0, 36],
        [32, 1, 2, 2, 1, 0, 33.0, 20.0, 26],
        [19, 0, 1, 0, 0, 0, 20.5, 37.0, 40],
    ], dtype=float)
    y = np.array([38.5, 31.0, 28.5, 25.0, 39.0, 36.5, 27.0, 40.0])

    enc = LabelEncoder().fit(["N", "Y"])
    modelo = LinearRegression()
    modelo.fit(X, y)

    return {
        "modelo": modelo,
        "x_cols": ["mager", "rf_ppterm", "dplural", "num_condiciones_cronicas",
                   "infeccion_activa", "priorlive", "bmi", "cl_sim_mm", "combgest"],
        "encoders": {"rf_ppterm": enc},
    }


def generar_modelos_dummy(destino: Path) -> None:
    destino.mkdir(parents=True, exist_ok=True)
    joblib.dump(_modelo_prematuro_dummy(), destino / "prematuro_logistic.pkl")
    joblib.dump(_modelo_semanas_dummy(),   destino / "semanas_lineal.pkl")
    print(f"[OK] Modelos dummy generados en: {destino}")


if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent / "modelos"
    generar_modelos_dummy(base)
