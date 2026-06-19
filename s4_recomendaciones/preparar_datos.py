"""Arma entradas S-4 y dataset de entrenamiento."""

import importlib.util
import sys
from pathlib import Path

import joblib
import pandas as pd

from config import CAMPOS_CLINICOS, CSV_ENTRENAMIENTO, CSV_LIMPIO, FEATURES_ENTRADA, URGENCIA_A_NUM
from reglas import recomendacion_if_then

BASE = Path(__file__).resolve().parent.parent
MODELO_S3_ARBOL = BASE / "modelos" / "s4_arbol_decision.pkl"

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


def _load_priorizacion():
    """Carga módulos de s4_priorizacion (S-3 informe) sin conflicto de nombres."""
    prior_dir = BASE / "s4_priorizacion"
    config_backup = sys.modules.get("config")
    for fname, alias in [("config.py", "prior_config"), ("datos.py", "prior_datos"), ("metodos.py", "prior_metodos")]:
        path = prior_dir / fname
        spec = importlib.util.spec_from_file_location(alias, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[alias] = mod
        if fname == "config.py":
            sys.modules["config"] = mod
        spec.loader.exec_module(mod)
    datos_mod = sys.modules["prior_datos"]
    metodos_mod = sys.modules["prior_metodos"]
    if config_backup is not None:
        sys.modules["config"] = config_backup
    else:
        # Restaurar config de s4_recomendaciones
        rec_spec = importlib.util.spec_from_file_location("config", Path(__file__).parent / "config.py")
        rec_mod = importlib.util.module_from_spec(rec_spec)
        rec_spec.loader.exec_module(rec_mod)
        sys.modules["config"] = rec_mod
    return datos_mod, metodos_mod


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

    datos_s3, metodos_s3 = _load_priorizacion()
    X_s3 = datos_s3.features_s4_desde_paciente(paciente)
    arbol = joblib.load(MODELO_S3_ARBOL)
    urgencia = metodos_s3.predecir_arbol(arbol, X_s3).iloc[0]

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
    datos_s3, metodos_s3 = _load_priorizacion()

    df_train = pd.read_csv(CSV_ENTRENAMIENTO)
    limpio = pd.read_csv(CSV_LIMPIO, usecols=["rf_ghype"])
    X_s3 = datos_s3.cargar_datos_s4()
    arbol = joblib.load(MODELO_S3_ARBOL)
    urgencias = metodos_s3.predecir_arbol(arbol, X_s3)

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
