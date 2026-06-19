"""Arma entradas S-4 y dataset de entrenamiento."""

import joblib
import pandas as pd

from app.ml_models.recomendaciones.config import (
    CAMPOS_CLINICOS,
    CSV_ENTRENAMIENTO,
    CSV_LIMPIO,
    FEATURES_ENTRADA,
    MODELO_S3_ARBOL,
    URGENCIA_A_NUM,
)
from app.ml_models.recomendaciones.reglas_clinicas import recomendacion_if_then
from app.ml_models.triage.datos import cargar_datos_s3, features_s3_desde_paciente
from app.ml_models.triage.metodos import predecir_arbol

FEATURES_ML = [
    "prob_prematuro",
    "nivel_urgencia_num",
    "parto_previo",
    "cl_sim_mm",
    "hipertension_gestacional",
    "bmi",
    "infeccion_activa",
    "num_condiciones_cronicas",
    "embarazo_multiple",
]


def _es_y(valor) -> int:
    return int(str(valor).strip().upper() == "Y")


def entradas_desde_dict(d: dict) -> dict:
    faltantes = [c for c in FEATURES_ENTRADA if c not in d]
    if faltantes:
        raise ValueError(f"Faltan entradas S-4: {faltantes}")
    return {
        "prob_prematuro": float(d["prob_prematuro"]),
        "nivel_urgencia": str(d["nivel_urgencia"]).upper(),
        "parto_previo": int(d["parto_previo"]),
        "cl_sim_mm": float(d["cl_sim_mm"]),
        "hipertension_gestacional": int(d["hipertension_gestacional"]),
        "bmi": float(d["bmi"]),
        "infeccion_activa": int(d["infeccion_activa"]),
        "num_condiciones_cronicas": int(d["num_condiciones_cronicas"]),
        "embarazo_multiple": int(d["embarazo_multiple"]),
    }


def features_ml(entradas: dict) -> pd.DataFrame:
    urg_num = URGENCIA_A_NUM.get(str(entradas["nivel_urgencia"]).upper(), 0)
    return pd.DataFrame([{
        "prob_prematuro": entradas["prob_prematuro"],
        "nivel_urgencia_num": urg_num,
        "parto_previo": entradas["parto_previo"],
        "cl_sim_mm": entradas["cl_sim_mm"],
        "hipertension_gestacional": entradas["hipertension_gestacional"],
        "bmi": entradas["bmi"],
        "infeccion_activa": entradas["infeccion_activa"],
        "num_condiciones_cronicas": entradas["num_condiciones_cronicas"],
        "embarazo_multiple": entradas["embarazo_multiple"],
    }])


def entradas_desde_paciente(paciente: dict) -> dict:
    faltantes = [c for c in CAMPOS_CLINICOS if c not in paciente]
    if faltantes:
        raise ValueError(f"Faltan campos clínicos: {faltantes}")

    X_s3 = features_s3_desde_paciente(paciente)
    arbol = joblib.load(MODELO_S3_ARBOL)
    urgencia = predecir_arbol(arbol, X_s3).iloc[0]

    return entradas_desde_dict({
        "prob_prematuro": float(X_s3["prob_prematuro"].iloc[0]),
        "nivel_urgencia": urgencia,
        "parto_previo": _es_y(paciente["rf_ppterm"]),
        "cl_sim_mm": float(paciente["cl_sim_mm"]),
        "hipertension_gestacional": _es_y(paciente["rf_ghype"]),
        "bmi": float(paciente["bmi"]),
        "infeccion_activa": int(paciente["infeccion_activa"]),
        "num_condiciones_cronicas": int(paciente["num_condiciones_cronicas"]),
        "embarazo_multiple": int(float(paciente["dplural"]) > 1),
    })


def cargar_dataset_entrenamiento() -> tuple[pd.DataFrame, pd.Series]:
    df_train = pd.read_csv(CSV_ENTRENAMIENTO)
    limpio = pd.read_csv(CSV_LIMPIO, usecols=["rf_ghype"])
    X_s3 = cargar_datos_s3()
    arbol = joblib.load(MODELO_S3_ARBOL)
    urgencias = predecir_arbol(arbol, X_s3)

    entradas_list = []
    for i in range(len(df_train)):
        entradas_list.append(entradas_desde_dict({
            "prob_prematuro": float(X_s3["prob_prematuro"].iloc[i]),
            "nivel_urgencia": urgencias.iloc[i],
            "parto_previo": int(X_s3["parto_previo"].iloc[i]),
            "cl_sim_mm": float(X_s3["cl_sim_mm"].iloc[i]),
            "hipertension_gestacional": int(_es_y(limpio["rf_ghype"].iloc[i])),
            "bmi": float(X_s3["bmi"].iloc[i]),
            "infeccion_activa": int(df_train["infeccion_activa"].iloc[i]),
            "num_condiciones_cronicas": int(df_train["num_condiciones_cronicas"].iloc[i]),
            "embarazo_multiple": int(X_s3["embarazo_multiple"].iloc[i]),
        }))

    X = pd.concat([features_ml(e) for e in entradas_list], ignore_index=True)
    y = pd.Series([recomendacion_if_then(e) for e in entradas_list], name="recomendacion")
    return X, y
