"""Carga datos S-4 y probabilidad del modelo S-2 (regresión logística)."""

import joblib
import pandas as pd
from sklearn.preprocessing import LabelEncoder

from config import CAMPOS_ENTRADA, CSV_ENTRENAMIENTO, CSV_LIMPIO, FEATURES_S4, MODELO_S2, X_COLS_S2


def _es_y(serie: pd.Series) -> pd.Series:
    return serie.astype(str).str.strip().str.upper().eq("Y")


def preparar_X_s2(df: pd.DataFrame, encoders: dict) -> pd.DataFrame:
    X = df[X_COLS_S2].copy()
    for col in ["rf_ppterm"]:
        X[col] = encoders[col].transform(df[col].astype(str))
    return X


def calcular_prob_prematuro(df: pd.DataFrame) -> pd.Series:
    paquete = joblib.load(MODELO_S2)
    modelo = paquete["modelo"]
    encoders = paquete["encoders"]
    X = preparar_X_s2(df, encoders)
    return pd.Series(modelo.predict_proba(X)[:, 1], index=df.index, name="prob_prematuro")


def _es_y_valor(valor) -> int:
    return int(str(valor).strip().upper() == "Y")


def features_s4_desde_paciente(paciente: dict) -> pd.DataFrame:
    """Construye la fila de 6 variables S-4 a partir de datos clínicos de entrada."""
    faltantes = [c for c in CAMPOS_ENTRADA if c not in paciente]
    if faltantes:
        raise ValueError(f"Faltan campos de entrada: {faltantes}")

    fila_s2 = {col: paciente[col] for col in X_COLS_S2}
    prob = float(calcular_prob_prematuro(pd.DataFrame([fila_s2])).iloc[0])

    out = pd.DataFrame(
        [
            {
                "prob_prematuro": prob,
                "embarazo_multiple": int(float(paciente["dplural"]) > 1),
                "cl_sim_mm": float(paciente["cl_sim_mm"]),
                "bmi": float(paciente["bmi"]),
                "parto_previo": _es_y_valor(paciente["rf_ppterm"]),
                "hipertension_gestacional": _es_y_valor(paciente["rf_ghype"]),
            }
        ]
    )
    return out[FEATURES_S4]


def cargar_datos_s4() -> pd.DataFrame:
    df = pd.read_csv(CSV_ENTRENAMIENTO)
    limpio = pd.read_csv(CSV_LIMPIO, usecols=["rf_ghype"])

    if len(df) != len(limpio):
        raise ValueError(f"Filas distintas: entrenamiento={len(df)}, limpio={len(limpio)}")

    out = pd.DataFrame(index=df.index)
    out["prob_prematuro"] = calcular_prob_prematuro(df)
    out["embarazo_multiple"] = (pd.to_numeric(df["dplural"], errors="coerce") > 1).astype(int)
    out["cl_sim_mm"] = pd.to_numeric(df["cl_sim_mm"], errors="coerce")
    out["bmi"] = pd.to_numeric(df["bmi"], errors="coerce")
    out["parto_previo"] = _es_y(df["rf_ppterm"]).astype(int)
    out["hipertension_gestacional"] = _es_y(limpio["rf_ghype"]).astype(int)

    return out
