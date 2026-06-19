"""
Inferencia S-4: datos de entrada → modelos → urgencia.

Uso desde terminal:
  python predecir_s4.py
  python predecir_s4.py --json paciente.json

Uso desde otro script:
  from predecir_s4 import predecir_urgencia
  resultado = predecir_urgencia({...})
"""

import argparse
import json
import sys
from pathlib import Path

import joblib

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import CAMPOS_ENTRADA, FEATURES_S4, MODELO_S4_ARBOL, MODELO_S4_ORDINAL, NIVELES
from datos import features_s4_desde_paciente
from metodos import predecir_arbol, predecir_logistica_ordinal, urgencia_por_puntaje

_EJEMPLO = {
    "mager": 28,
    "rf_ppterm": "N",
    "dplural": 1,
    "num_condiciones_cronicas": 0,
    "infeccion_activa": 0,
    "priorlive": 1,
    "bmi": 21.4,
    "cl_sim_mm": 33.09,
    "combgest": 37,
    "rf_ghype": "N",
}


def predecir_urgencia(paciente: dict) -> dict:
    """Ejecuta S-2 (probabilidad) + S-4 (3 métodos) para un paciente."""
    X = features_s4_desde_paciente(paciente)
    fila = X.iloc[0]

    res_puntaje = urgencia_por_puntaje(X)
    puntaje = float(res_puntaje["puntaje_s4"].iloc[0])
    urgencia_puntaje = res_puntaje["urgencia_puntaje"].iloc[0]

    arbol = joblib.load(MODELO_S4_ARBOL)
    ordinal = joblib.load(MODELO_S4_ORDINAL)
    urgencia_arbol = predecir_arbol(arbol, X).iloc[0]
    urgencia_ordinal = predecir_logistica_ordinal(ordinal, X).iloc[0]

    return {
        "entrada": {k: paciente[k] for k in CAMPOS_ENTRADA},
        "features_s4": fila.to_dict(),
        "puntaje_s4": round(puntaje, 4),
        "urgencia_puntaje": urgencia_puntaje,
        "urgencia_arbol": urgencia_arbol,
        "urgencia_ordinal": urgencia_ordinal,
        "niveles_posibles": NIVELES,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Priorización S-4 para un paciente")
    parser.add_argument(
        "--json",
        type=Path,
        help="Archivo JSON con los campos de entrada del paciente",
    )
    args = parser.parse_args()

    if args.json:
        paciente = json.loads(args.json.read_text(encoding="utf-8"))
    else:
        paciente = _EJEMPLO
        print("Sin --json: usando paciente de ejemplo.\n")

    resultado = predecir_urgencia(paciente)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
