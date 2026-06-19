"""Configuración S-4 informe — recomendaciones clínicas (Informes_teoricos / SOGC 467)."""

from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

CSV_ENTRENAMIENTO = BASE / "datos_limpios" / "natality_entrenamiento.csv"
CSV_LIMPIO = BASE / "datos_limpios" / "natality_limpio_completo.csv"
DIR_SALIDA = BASE / "datos_limpios"
DIR_REPORTES = BASE / "reportes_s4_rec"

MODELO_S2 = BASE / "modelos" / "prematuro_logistic.pkl"
MODELO_S3_ARBOL = BASE / "modelos" / "s4_arbol_decision.pkl"
MODELO_CART = BASE / "modelos" / "recomendaciones_cart.pkl"
MODELO_RF = BASE / "modelos" / "recomendaciones_random_forest.pkl"

# Campos clínicos completos (para armar S-2 + S-3 + S-4)
CAMPOS_CLINICOS = [
    "mager", "rf_ppterm", "dplural", "num_condiciones_cronicas",
    "infeccion_activa", "priorlive", "bmi", "cl_sim_mm", "combgest", "rf_ghype",
]

# 9 entradas del informe para S-4 (recomendaciones)
FEATURES_ENTRADA = [
    "prob_prematuro",
    "nivel_urgencia",
    "parto_previo",
    "cl_sim_mm",
    "hipertension_gestacional",
    "bmi",
    "infeccion_activa",
    "num_condiciones_cronicas",
    "embarazo_multiple",
]

RECOMENDACIONES = [
    "control_prenatal_rutinario",
    "seguimiento_estrecho_lc",
    "progesterona_vaginal",
    "tratar_infeccion",
    "vigilancia_hta_multiple",
    "derivacion_alto_riesgo",
]

NIVELES_URGENCIA = ["VERDE", "AMARILLO", "NARANJA", "ROJO"]
URGENCIA_A_NUM = {n: i for i, n in enumerate(NIVELES_URGENCIA)}

LC_CORTO_MM = 25.0
LC_MODERADO_MM = 30.0
BMI_ALTO = 30.0
BMI_BAJO = 18.5
