"""Configuración S-4 — recomendaciones clínicas (SOGC 467)."""

from pathlib import Path

from app.ml_models.paths import resolve_ml_models_dir

BASE = Path(__file__).resolve().parent.parent
_MODELS = resolve_ml_models_dir()

CSV_ENTRENAMIENTO = BASE / "datos_limpios" / "natality_entrenamiento.csv"
CSV_LIMPIO = BASE / "datos_limpios" / "natality_limpio_completo.csv"
DIR_SALIDA = BASE / "datos_limpios"
DIR_REPORTES = BASE / "reportes_s4_rec"

MODELO_S2 = _MODELS / "prematuro_logistic.pkl"
MODELO_S3_ARBOL = _MODELS / "s4_arbol_decision.pkl"
MODELO_CART = _MODELS / "recomendaciones_cart.pkl"
MODELO_RF = _MODELS / "recomendaciones_random_forest.pkl"

CAMPOS_CLINICOS = [
    "mager", "rf_ppterm", "dplural", "num_condiciones_cronicas",
    "infeccion_activa", "priorlive", "bmi", "cl_sim_mm", "combgest", "rf_ghype",
]

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
