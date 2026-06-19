"""
Inferencia S-3: datos de entrada → modelos → urgencia.

Uso desde terminal:
  python predecir_s3.py
  python predecir_s3.py --json paciente.json

Uso desde otro script:
  from app.ml_models.triage.predecir_s3 import predecir_urgencia
  resultado = predecir_urgencia({...})
"""

import argparse
import json
from pathlib import Path

import joblib

from app.ml_models.triage.config import (
    CAMPOS_ENTRADA,
    MODELO_S3_ARBOL,
    MODELO_S3_ORDINAL,
    NIVELES,
)
from app.ml_models.triage.datos import features_s3_desde_paciente
from app.ml_models.triage.metodos import (
    predecir_arbol,
    predecir_logistica_ordinal,
    urgencia_por_puntaje,
)

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
    """Ejecuta S-2 (probabilidad) + S-3 (3 métodos) para un paciente."""
    if not MODELO_S3_ARBOL.exists():
        raise FileNotFoundError(
            f"Modelo S-3 no encontrado: {MODELO_S3_ARBOL}. "
            "Coloque los archivos .pkl en app/ml_models/modelos/"
        )
    if not MODELO_S3_ORDINAL.exists():
        raise FileNotFoundError(
            f"Modelo S-3 no encontrado: {MODELO_S3_ORDINAL}. "
            "Coloque los archivos .pkl en app/ml_models/modelos/"
        )

    X = features_s3_desde_paciente(paciente)
    fila = X.iloc[0]

    res_puntaje = urgencia_por_puntaje(X)
    puntaje = float(res_puntaje["puntaje_s3"].iloc[0])
    urgencia_puntaje = res_puntaje["urgencia_puntaje"].iloc[0]

    arbol = joblib.load(MODELO_S3_ARBOL)
    ordinal = joblib.load(MODELO_S3_ORDINAL)
    urgencia_arbol = predecir_arbol(arbol, X).iloc[0]
    urgencia_ordinal = predecir_logistica_ordinal(ordinal, X).iloc[0]

    return {
        "entrada": {k: paciente[k] for k in CAMPOS_ENTRADA},
        "features_s3": fila.to_dict(),
        "puntaje_s3": round(puntaje, 4),
        "urgencia_puntaje": urgencia_puntaje,
        "urgencia_arbol": urgencia_arbol,
        "urgencia_ordinal": urgencia_ordinal,
        "niveles_posibles": NIVELES,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Clasificación S-3 por urgencia para un paciente")
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
