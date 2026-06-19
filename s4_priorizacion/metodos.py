"""Reglas clínicas y métodos S-4 (Informes_teoricos)."""

import pandas as pd
from mord import LogisticAT
from sklearn.tree import DecisionTreeClassifier

from config import (
    BMI_ALTO,
    BMI_BAJO,
    LC_CORTO_MM,
    LC_MODERADO_MM,
    NIVELES,
    PESOS_PUNTAJE,
    UMBRALES_PUNTAJE,
)


def _num_a_nivel(num: int) -> str:
    return NIVELES[int(num)]


def _puntaje_fila(row: pd.Series) -> float:
    lc_corto = 1.0 if row["cl_sim_mm"] <= LC_CORTO_MM else 0.0
    bmi_riesgo = 1.0 if (row["bmi"] < BMI_BAJO or row["bmi"] > BMI_ALTO) else 0.0
    return (
        PESOS_PUNTAJE["prob_prematuro"] * row["prob_prematuro"]
        + PESOS_PUNTAJE["parto_previo"] * row["parto_previo"]
        + PESOS_PUNTAJE["embarazo_multiple"] * row["embarazo_multiple"]
        + PESOS_PUNTAJE["hipertension_gestacional"] * row["hipertension_gestacional"]
        + PESOS_PUNTAJE["lc_corto"] * lc_corto
        + PESOS_PUNTAJE["bmi_riesgo"] * bmi_riesgo
    )


def _puntaje_a_nivel(puntaje: float) -> str:
    if puntaje >= UMBRALES_PUNTAJE["ROJO"]:
        return "ROJO"
    if puntaje >= UMBRALES_PUNTAJE["NARANJA"]:
        return "NARANJA"
    if puntaje >= UMBRALES_PUNTAJE["AMARILLO"]:
        return "AMARILLO"
    return "VERDE"


def urgencia_por_puntaje(df: pd.DataFrame) -> pd.DataFrame:
    puntajes = df.apply(_puntaje_fila, axis=1)
    niveles = puntajes.apply(_puntaje_a_nivel)
    return pd.DataFrame({"puntaje_s4": puntajes, "urgencia_puntaje": niveles}, index=df.index)


def urgencia_por_reglas_clinicas(df: pd.DataFrame) -> pd.Series:
    """Etiqueta de referencia segun Informes_teoricos (SOGC 467, BMI meta, ML)."""
    niveles = []
    for _, r in df.iterrows():
        p = r["prob_prematuro"]
        lc = r["cl_sim_mm"]
        pp = r["parto_previo"]
        mult = r["embarazo_multiple"]
        gh = r["hipertension_gestacional"]
        bmi_r = r["bmi"] < BMI_BAJO or r["bmi"] > BMI_ALTO

        if (
            p >= 0.60
            or (lc <= LC_CORTO_MM and (pp == 1 or p >= 0.35))
            or (pp == 1 and mult == 1)
            or (gh == 1 and lc <= LC_MODERADO_MM and p >= 0.30)
            or (mult == 1 and p >= 0.45)
        ):
            niveles.append("ROJO")
        elif (
            p >= 0.40
            or pp == 1
            or lc <= LC_CORTO_MM
            or mult == 1
            or (gh == 1 and p >= 0.25)
            or (bmi_r and p >= 0.30)
        ):
            niveles.append("NARANJA")
        elif p >= 0.20 or lc <= LC_MODERADO_MM or gh == 1 or mult == 1 or bmi_r:
            niveles.append("AMARILLO")
        else:
            niveles.append("VERDE")

    return pd.Series(niveles, index=df.index, name="urgencia_referencia")


def entrenar_arbol_decision(
    X: pd.DataFrame, y_num: pd.Series, random_state: int = 42
) -> DecisionTreeClassifier:
    modelo = DecisionTreeClassifier(max_depth=4, random_state=random_state, class_weight="balanced")
    modelo.fit(X, y_num)
    return modelo


def predecir_arbol(modelo: DecisionTreeClassifier, X: pd.DataFrame) -> pd.Series:
    pred = modelo.predict(X)
    return pd.Series([_num_a_nivel(v) for v in pred], index=X.index, name="urgencia_arbol")


def entrenar_logistica_ordinal(X: pd.DataFrame, y_num: pd.Series) -> LogisticAT:
    modelo = LogisticAT(alpha=0.0)
    modelo.fit(X.values, y_num.values)
    return modelo


def predecir_logistica_ordinal(modelo: LogisticAT, X: pd.DataFrame) -> pd.Series:
    pred = modelo.predict(X.values)
    return pd.Series([_num_a_nivel(v) for v in pred], index=X.index, name="urgencia_ordinal")
