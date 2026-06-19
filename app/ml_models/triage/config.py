"""Configuración S-3 — clasificación por nivel de urgencia (basada en Informes_teoricos)."""

from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

CSV_ENTRENAMIENTO = BASE / "datos_limpios" / "natality_entrenamiento.csv"
CSV_LIMPIO = BASE / "datos_limpios" / "natality_limpio_completo.csv"
MODELO_S2 = BASE / "modelos" / "prematuro_logistic.pkl"
MODELO_S3_ARBOL = BASE / "modelos" / "s4_arbol_decision.pkl"
MODELO_S3_ORDINAL = BASE / "modelos" / "s4_logistica_ordinal.pkl"

CAMPOS_ENTRADA = [
    "mager", "rf_ppterm", "dplural", "num_condiciones_cronicas",
    "infeccion_activa", "priorlive", "bmi", "cl_sim_mm", "combgest",
    "rf_ghype",
]
DIR_SALIDA = BASE / "datos_limpios"
DIR_REPORTES = BASE / "reportes_s3"
DIR_TEORIA = BASE / "Informes_teoricos"

X_COLS_S2 = [
    "mager", "rf_ppterm", "dplural", "num_condiciones_cronicas",
    "infeccion_activa", "priorlive", "bmi", "cl_sim_mm", "combgest",
]

FEATURES_S3 = [
    "prob_prematuro",
    "embarazo_multiple",
    "cl_sim_mm",
    "bmi",
    "parto_previo",
    "hipertension_gestacional",
]

NIVELES = ["VERDE", "AMARILLO", "NARANJA", "ROJO"]
NIVEL_A_NUM = {n: i for i, n in enumerate(NIVELES)}

LC_CORTO_MM = 25.0
LC_MODERADO_MM = 30.0
BMI_OPTIMO = 23.5
BMI_BAJO = 18.5
BMI_ALTO = 30.0

PESOS_PUNTAJE = {
    "prob_prematuro": 0.35,
    "parto_previo": 0.20,
    "embarazo_multiple": 0.15,
    "hipertension_gestacional": 0.12,
    "lc_corto": 0.13,
    "bmi_riesgo": 0.05,
}

UMBRALES_PUNTAJE = {
    "ROJO": 0.70,
    "NARANJA": 0.45,
    "AMARILLO": 0.22,
}

# Compatibilidad con nombres anteriores
MODELO_S4_ARBOL = MODELO_S3_ARBOL
MODELO_S4_ORDINAL = MODELO_S3_ORDINAL
FEATURES_S4 = FEATURES_S3
