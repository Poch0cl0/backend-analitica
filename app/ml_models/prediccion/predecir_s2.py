"""
Predicción S-2 — riesgo de parto prematuro y semanas estimadas.

Algoritmos disponibles:
  - "catboost"      → modelo_catboost.cbm            + semanas_catboost.cbm
  - "mejor"         → modelo_catboost.cbm            + semanas_catboost.cbm       (default)
  - "logistic"      → modelo_regresion_logistica.pkl + semanas_lineal.pkl
  - "random_forest" → modelo_random_forest.pkl       + semanas_random_forest.pkl
  - "svm"           → prematuro_svm.pkl              + semanas_svm.pkl
"""

import warnings
from pathlib import Path
from typing import Literal

import joblib
import numpy as np
import pandas as pd

from app.ml_models.paths import resolve_ml_models_dir

_DIR = resolve_ml_models_dir()

AlgoritmoS2 = Literal["catboost", "mejor", "logistic", "random_forest", "svm"]

CAMPOS_S2 = [
    "mager", "rf_ppterm", "dplural", "num_condiciones_cronicas",
    "infeccion_activa", "priorlive", "bmi", "cl_sim_mm", "combgest",
]

# Mapeo de nombres de campos viejos (CAMPOS_S2) → nuevos nombres de los modelos
_FEATURE_MAP = {
    "num_condiciones_cronicas": "N\u00b0 Cr\u00f3nicas",
    "infeccion_activa": "N\u00b0 Infecciones",
    "cl_sim_mm": "longitud_cervical",
}
_FEATURE_MAP_REV = {v: k for k, v in _FEATURE_MAP.items()}

_ARCHIVOS = {
    "catboost":      ("modelo_catboost.cbm",             "semanas_catboost.cbm"),
    "mejor":         ("modelo_catboost.cbm",             "semanas_catboost.cbm"),
    "logistic":      ("modelo_regresion_logistica.pkl",  "semanas_lineal.pkl"),
    "random_forest": ("modelo_random_forest.pkl",        "semanas_random_forest.pkl"),
    "svm":           ("prematuro_svm.pkl",               "semanas_svm.pkl"),
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


def _preparar_df(
    datos: dict,
    encoders: dict | None = None,
    expected_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Convierte datos a DataFrame numérico. rf_ppterm Y/N → 1/0."""
    if expected_cols is None:
        expected_cols = CAMPOS_S2
    fila = {}
    for col in expected_cols:
        if col in datos:
            fila[col] = datos[col]
        else:
            mapped = _FEATURE_MAP_REV.get(col)
            if mapped and mapped in datos:
                fila[col] = datos[mapped]
            else:
                fila[col] = 0
    if isinstance(fila.get("rf_ppterm"), str):
        if encoders and "rf_ppterm" in encoders:
            fila["rf_ppterm"] = encoders["rf_ppterm"].transform([fila["rf_ppterm"]])[0]
        else:
            fila["rf_ppterm"] = 1 if str(fila["rf_ppterm"]).upper() == "Y" else 0
    return pd.DataFrame([fila])


def _sigmoid(x: float) -> float:
    return float(1 / (1 + np.exp(-x)))


def _extraer_features_modelo(modelo, formato: str) -> list[str] | None:
    """Extrae la lista de features esperadas por el modelo (si está disponible)."""
    if formato == "dict_sklearn":
        return modelo.get("features")
    if formato == "catboost_native" and hasattr(modelo, "feature_names_"):
        return list(modelo.feature_names_)
    return None


def _prob_prematuro(modelo, formato: str, datos: dict) -> float:
    if formato == "dict_sklearn":
        model_obj = modelo.get("model", modelo.get("modelo"))
        encoders = modelo.get("estimator", {}) or modelo.get("encoders", {})
        features = modelo.get("features")
        df = _preparar_df(
            datos,
            encoders if isinstance(encoders, dict) else None,
            expected_cols=features,
        )
        return float(model_obj.predict_proba(df)[0, 1])

    features = _extraer_features_modelo(modelo, formato)
    df = _preparar_df(datos, expected_cols=features)

    if hasattr(modelo, "predict_proba"):
        return float(modelo.predict_proba(df)[0, 1])

    # LinearSVC: aproximar probabilidad con sigmoid sobre decision_function
    score = float(modelo.decision_function(df)[0])
    return _sigmoid(score)


def _pred_semanas(modelo, formato: str, datos: dict) -> float:
    if formato == "dict_sklearn":
        model_obj = modelo.get("model", modelo.get("modelo"))
        encoders = modelo.get("estimator", {}) or modelo.get("encoders", {})
        features = modelo.get("features")
        df = _preparar_df(
            datos,
            encoders if isinstance(encoders, dict) else None,
            expected_cols=features,
        )
        return float(model_obj.predict(df)[0])

    features = _extraer_features_modelo(modelo, formato)
    df = _preparar_df(datos, expected_cols=features)
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


_ALGORITMOS_CONSENSO: tuple[AlgoritmoS2, ...] = ("random_forest", "catboost", "svm")


def _nivel_riesgo(prob: float) -> str:
    if prob >= 0.7:
        return "critico"
    if prob >= 0.5:
        return "alto"
    if prob >= 0.3:
        return "medio"
    return "bajo"


def predecir_s2_consenso(datos: dict) -> dict:
    """Ejecuta RF, CatBoost y SVM; retorna promedio y resultado por modelo."""
    faltantes = [c for c in CAMPOS_S2 if c not in datos]
    if faltantes:
        raise ValueError(f"Faltan campos de entrada para S-2: {faltantes}")

    modelos: dict[str, dict] = {}
    probs: list[float] = []

    for alg in _ALGORITMOS_CONSENSO:
        res = predecir_s2(datos, algoritmo=alg)
        modelos[alg] = {
            "prob_prematuro": res["prob_prematuro"],
            "semanas_estimadas": res["semanas_estimadas"],
        }
        probs.append(res["prob_prematuro"])

    prob_consenso = round(sum(probs) / len(probs), 4)
    semanas_prom = round(
        sum(modelos[a]["semanas_estimadas"] for a in _ALGORITMOS_CONSENSO) / len(_ALGORITMOS_CONSENSO),
        1,
    )

    return {
        "prob_consenso": prob_consenso,
        "prematuro": int(prob_consenso >= 0.5),
        "semanas_estimadas_consenso": semanas_prom,
        "nivel_riesgo": _nivel_riesgo(prob_consenso),
        "modelos": modelos,
    }
