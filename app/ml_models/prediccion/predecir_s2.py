"""
Predicción S-2 — riesgo de parto prematuro y semanas estimadas.

Algoritmos disponibles:
  - "catboost"      → prematuro_catboost.cbm      + semanas_catboost.cbm
  - "mejor"         → prematuro_mejor_modelo.pkl  + semanas_mejor_modelo.pkl   (CatBoost, default)
  - "logistic"      → prematuro_logistic.pkl       + semanas_lineal.pkl
  - "random_forest" → prematuro_random_forest.pkl  + semanas_random_forest.pkl
  - "svm"           → prematuro_svm.pkl            + semanas_svm.pkl
"""

import warnings
from pathlib import Path
from typing import Literal

import joblib
import numpy as np
import pandas as pd

from app.core.config import settings

_DIR = Path(settings.ML_MODELS_PATH)

AlgoritmoS2 = Literal["catboost", "mejor", "logistic", "random_forest", "svm"]

CAMPOS_S2 = [
    "mager", "rf_ppterm", "dplural", "num_condiciones_cronicas",
    "infeccion_activa", "priorlive", "bmi", "cl_sim_mm", "combgest",
]

_ARCHIVOS = {
    "catboost":      ("prematuro_catboost.cbm",      "semanas_catboost.cbm"),
    "mejor":         ("prematuro_mejor_modelo.pkl",   "semanas_mejor_modelo.pkl"),
    "logistic":      ("prematuro_logistic.pkl",       "semanas_lineal.pkl"),
    "random_forest": ("prematuro_random_forest.pkl",  "semanas_random_forest.pkl"),
    "svm":           ("prematuro_svm.pkl",            "semanas_svm.pkl"),
}

_NOMBRES_DISPLAY = {
    "catboost":      "CatBoost",
    "mejor":         "CatBoost (mejor modelo)",
    "logistic":      "Regresión Logística",
    "random_forest": "Random Forest",
    "svm":           "SVM (LinearSVC)",
}


def _cargar(nombre: str):
    path = _DIR / nombre
    if not path.exists():
        raise FileNotFoundError(
            f"Modelo no encontrado: {nombre}. Colóquelo en {_DIR}"
        )
    if path.suffix == ".cbm":
        from catboost import CatBoostClassifier, CatBoostRegressor
        if "semanas" in nombre:
            m = CatBoostRegressor()
        else:
            m = CatBoostClassifier()
        m.load_model(str(path))
        return m, "catboost_native"

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pkg = joblib.load(path)

    if isinstance(pkg, dict):
        return pkg, "dict_sklearn"
    return pkg, "direct_sklearn"


def _preparar_df(datos: dict, encoders: dict | None = None) -> pd.DataFrame:
    """Convierte datos a DataFrame numérico. rf_ppterm Y/N → 1/0."""
    fila = {k: datos[k] for k in CAMPOS_S2}
    if isinstance(fila.get("rf_ppterm"), str):
        if encoders and "rf_ppterm" in encoders:
            fila["rf_ppterm"] = encoders["rf_ppterm"].transform([fila["rf_ppterm"]])[0]
        else:
            fila["rf_ppterm"] = 1 if str(fila["rf_ppterm"]).upper() == "Y" else 0
    return pd.DataFrame([fila])[CAMPOS_S2]


def _sigmoid(x: float) -> float:
    return float(1 / (1 + np.exp(-x)))


def _prob_prematuro(modelo, formato: str, datos: dict) -> float:
    if formato == "dict_sklearn":
        encoders = modelo.get("estimator", {}) or modelo.get("encoders", {})
        df = _preparar_df(datos, encoders if isinstance(encoders, dict) else None)
        return float(modelo["modelo"].predict_proba(df)[0, 1])

    df = _preparar_df(datos)

    if hasattr(modelo, "predict_proba"):
        return float(modelo.predict_proba(df)[0, 1])

    # LinearSVC: aproximar probabilidad con sigmoid sobre decision_function
    score = float(modelo.decision_function(df)[0])
    return _sigmoid(score)


def _pred_semanas(modelo, formato: str, datos: dict) -> float:
    if formato == "dict_sklearn":
        encoders = modelo.get("estimator", {}) or modelo.get("encoders", {})
        df = _preparar_df(datos, encoders if isinstance(encoders, dict) else None)
        return float(modelo["modelo"].predict(df)[0])

    df = _preparar_df(datos)
    return float(modelo.predict(df)[0])


def predecir_s2(datos: dict, algoritmo: AlgoritmoS2 = "mejor") -> dict:
    """
    Predice riesgo de parto prematuro y semanas estimadas.

    Args:
        datos:     dict con los 9 campos de CAMPOS_S2.
        algoritmo: nombre del algoritmo a usar (ver módulo docstring).
    Returns:
        dict con prob_prematuro, prematuro, semanas_estimadas, algoritmo_usado.
    """
    faltantes = [c for c in CAMPOS_S2 if c not in datos]
    if faltantes:
        raise ValueError(f"Faltan campos de entrada para S-2: {faltantes}")

    if algoritmo not in _ARCHIVOS:
        raise ValueError(
            f"Algoritmo '{algoritmo}' no reconocido. "
            f"Opciones: {list(_ARCHIVOS.keys())}"
        )

    archivo_pre, archivo_sem = _ARCHIVOS[algoritmo]

    modelo_pre, fmt_pre = _cargar(archivo_pre)
    prob = _prob_prematuro(modelo_pre, fmt_pre, datos)

    modelo_sem, fmt_sem = _cargar(archivo_sem)
    semanas = _pred_semanas(modelo_sem, fmt_sem, datos)

    return {
        "prob_prematuro":    round(prob, 4),
        "prematuro":         int(prob >= 0.5),
        "semanas_estimadas": round(semanas, 1),
        "algoritmo_usado":   _NOMBRES_DISPLAY[algoritmo],
        "archivo_modelo":    archivo_pre,
    }
