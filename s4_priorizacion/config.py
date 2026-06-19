"""Configuración S-4 — priorización por urgencia (basada en Informes_teoricos)."""

from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

CSV_ENTRENAMIENTO = BASE / "datos_limpios" / "natality_entrenamiento.csv"
CSV_LIMPIO = BASE / "datos_limpios" / "natality_limpio_completo.csv"
MODELO_S2 = BASE / "modelos" / "prematuro_logistic.pkl"
MODELO_S4_ARBOL = BASE / "modelos" / "s4_arbol_decision.pkl"
MODELO_S4_ORDINAL = BASE / "modelos" / "s4_logistica_ordinal.pkl"

CAMPOS_ENTRADA = [
    "mager", "rf_ppterm", "dplural", "num_condiciones_cronicas",
    "infeccion_activa", "priorlive", "bmi", "cl_sim_mm", "combgest",
    "rf_ghype",
]
DIR_SALIDA = BASE / "datos_limpios"
DIR_REPORTES = BASE / "reportes_s4"
DIR_TEORIA = BASE / "Informes_teoricos"

X_COLS_S2 = [
    "mager", "rf_ppterm", "dplural", "num_condiciones_cronicas",
    "infeccion_activa", "priorlive", "bmi", "cl_sim_mm", "combgest",
]

FEATURES_S4 = [
    "prob_prematuro",
    "embarazo_multiple",
    "cl_sim_mm",
    "bmi",
    "parto_previo",
    "hipertension_gestacional",
]

NIVELES = ["VERDE", "AMARILLO", "NARANJA", "ROJO"]
NIVEL_A_NUM = {n: i for i, n in enumerate(NIVELES)}

# SOGC 467: cuello corto <= 25 mm; BMI meta: riesgo en extremos; ML prob para estratificacion
LC_CORTO_MM = 25.0       # SOGC Technical Update 467
LC_MODERADO_MM = 30.0
BMI_OPTIMO = 23.5        # rango bajo riesgo ~22.5-25.9 (meta BMI-PTB)
BMI_BAJO = 18.5
BMI_ALTO = 30.0

# Puntaje ponderado S-4 (suma = 1.0)
PESOS_PUNTAJE = {
    "prob_prematuro": 0.35,           # modelos ML (Explainable AI tool; prediction studies)
    "parto_previo": 0.20,             # SOGC 467 — previous spontaneous PTB
    "embarazo_multiple": 0.15,        # multiple gestation — literature/KOPEN
    "hipertension_gestacional": 0.12, # gestational hypertension — KOPEN, expert review
    "lc_corto": 0.13,                 # SOGC <= 25 mm short cervix
    "bmi_riesgo": 0.05,               # BMI U-shaped risk (meta-analysis)
}

UMBRALES_PUNTAJE = {
    "ROJO": 0.70,
    "NARANJA": 0.45,
    "AMARILLO": 0.22,
}
