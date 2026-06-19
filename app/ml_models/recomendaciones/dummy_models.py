"""
Genera modelos dummy S-4 para desarrollo cuando los .pkl reales no están disponibles.
También genera s4_arbol_decision.pkl mínimo si falta (dependencia de S-4).

Uso: python -m app.ml_models.recomendaciones.dummy_models
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier

from app.ml_models.prediccion.dummy_models import generar_modelos_dummy as generar_s2_dummy
from app.ml_models.recomendaciones.config import MODELO_CART, MODELO_RF, RECOMENDACIONES
from app.ml_models.recomendaciones.datos import FEATURES_ML
from app.ml_models.recomendaciones.metodos import guardar_modelos
from app.ml_models.triage.config import MODELO_S3_ARBOL, MODELO_S3_ORDINAL


def _generar_arbol_s3_dummy() -> None:
    if MODELO_S3_ARBOL.exists():
        return
    X = np.array([
        [0.1, 0, 35.0, 22.0, 0, 0],
        [0.5, 1, 20.0, 28.0, 1, 1],
        [0.8, 0, 15.0, 32.0, 1, 0],
        [0.3, 0, 28.0, 24.0, 0, 0],
        [0.6, 1, 22.0, 26.0, 0, 1],
    ], dtype=float)
    y = np.array([0, 2, 3, 1, 2])
    modelo = DecisionTreeClassifier(max_depth=4, random_state=42)
    modelo.fit(X, y)
    MODELO_S3_ARBOL.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(modelo, MODELO_S3_ARBOL)
    print("[OK] s4_arbol_decision.pkl dummy generado")


def _generar_ordinal_s3_dummy() -> None:
    if MODELO_S3_ORDINAL.exists():
        return
    from mord import LogisticAT

    X = np.array([
        [0.1, 0, 35.0, 22.0, 0, 0],
        [0.5, 1, 20.0, 28.0, 1, 1],
        [0.8, 0, 15.0, 32.0, 1, 0],
        [0.3, 0, 28.0, 24.0, 0, 0],
        [0.6, 1, 22.0, 26.0, 0, 1],
        [0.2, 0, 30.0, 23.0, 0, 0],
    ], dtype=float)
    y = np.array([0, 2, 3, 1, 2, 0])
    modelo = LogisticAT(alpha=0.0)
    modelo.fit(X, y)
    MODELO_S3_ORDINAL.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(modelo, MODELO_S3_ORDINAL)
    print("[OK] s4_logistica_ordinal.pkl dummy generado")


def _dataset_sintetico() -> tuple[pd.DataFrame, pd.Series]:
    rows = [
        [0.15, 0, 0, 35.0, 0, 22.0, 0, 0, 0],
        [0.45, 2, 1, 22.0, 0, 21.0, 0, 0, 0],
        [0.65, 3, 0, 18.0, 1, 31.0, 0, 2, 1],
        [0.25, 1, 0, 28.0, 0, 24.0, 1, 0, 0],
        [0.55, 2, 1, 24.0, 1, 29.0, 0, 1, 1],
        [0.10, 0, 0, 32.0, 0, 23.0, 0, 0, 0],
        [0.70, 3, 1, 20.0, 0, 27.0, 0, 0, 0],
        [0.35, 1, 0, 26.0, 0, 25.0, 0, 3, 0],
    ]
    labels = [
        "control_prenatal_rutinario",
        "progesterona_vaginal",
        "derivacion_alto_riesgo",
        "tratar_infeccion",
        "vigilancia_hta_multiple",
        "control_prenatal_rutinario",
        "derivacion_alto_riesgo",
        "vigilancia_hta_multiple",
    ]
    return pd.DataFrame(rows, columns=FEATURES_ML), pd.Series(labels)


def generar_modelos_dummy_s4(destino: Path | None = None) -> None:
    destino = destino or MODELO_CART.parent
    destino.mkdir(parents=True, exist_ok=True)

    generar_s2_dummy(destino)
    _generar_arbol_s3_dummy()
    _generar_ordinal_s3_dummy()

    X, y = _dataset_sintetico()
    le = LabelEncoder()
    le.fit(RECOMENDACIONES)
    y_num = le.transform(y)

    cart = DecisionTreeClassifier(max_depth=6, random_state=42, class_weight="balanced")
    cart.fit(X, y_num)

    rf = RandomForestClassifier(
        n_estimators=50, max_depth=6, random_state=42, class_weight="balanced"
    )
    rf.fit(X, y_num)

    guardar_modelos(cart, le, rf, le)
    print(f"[OK] Modelos S-4 dummy generados en: {destino}")


if __name__ == "__main__":
    generar_modelos_dummy_s4()
