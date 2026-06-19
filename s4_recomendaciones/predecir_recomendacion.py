"""
Inferencia S-4 informe — recomendaciones clínicas.

Uso:
  python predecir_recomendacion.py
  python predecir_recomendacion.py --json paciente.json

Desde backend:
  from predecir_recomendacion import predecir_recomendacion
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import CAMPOS_CLINICOS, FEATURES_ENTRADA, RECOMENDACIONES
from preparar_datos import entradas_desde_dict, entradas_desde_paciente, features_ml
from metodos import cargar_cart, cargar_rf, importancia_rf, predecir_cart, predecir_rf
from reglas import recomendacion_if_then

_EJEMPLO = {
    "mager": 28,
    "rf_ppterm": "Y",
    "dplural": 1,
    "num_condiciones_cronicas": 0,
    "infeccion_activa": 0,
    "priorlive": 1,
    "bmi": 21.4,
    "cl_sim_mm": 22.0,
    "combgest": 37,
    "rf_ghype": "N",
}


def predecir_recomendacion(paciente_o_entradas: dict, *, clinico: bool = True) -> dict:
    """
    clinico=True  → recibe 10 campos clínicos (calcula S-2 + S-3 internamente)
    clinico=False → recibe las 9 entradas S-4 ya calculadas
    """
    if clinico:
        entradas = entradas_desde_paciente(paciente_o_entradas)
    else:
        entradas = entradas_desde_dict(paciente_o_entradas)

    X = features_ml(entradas)
    rec_if = recomendacion_if_then(entradas)

    cart, le_cart = cargar_cart()
    rf, le_rf = cargar_rf()
    rec_cart = predecir_cart(cart, le_cart, X)
    rec_rf = predecir_rf(rf, le_rf, X)

    return {
        "entradas_s4": entradas,
        "recomendacion_if_then": rec_if,
        "recomendacion_cart": rec_cart,
        "recomendacion_random_forest": rec_rf,
        "importancia_variables_rf": importancia_rf(rf).to_dict(orient="records"),
        "recomendaciones_posibles": RECOMENDACIONES,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Recomendaciones S-4 (informe)")
    parser.add_argument("--json", type=Path, help="JSON con campos clínicos")
    parser.add_argument(
        "--entradas",
        action="store_true",
        help="JSON ya trae las 9 entradas S-4 (no campos clínicos)",
    )
    args = parser.parse_args()

    if args.json:
        data = json.loads(args.json.read_text(encoding="utf-8"))
    else:
        data = _EJEMPLO
        print("Sin --json: usando paciente de ejemplo.\n")

    resultado = predecir_recomendacion(data, clinico=not args.entradas)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
