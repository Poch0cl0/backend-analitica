"""
Inferencia S-4: recomendaciones clínicas (IF-THEN, CART, Random Forest).

Uso desde terminal:
  python -m app.ml_models.recomendaciones.predecir_s4
  python -m app.ml_models.recomendaciones.predecir_s4 --json paciente.json

Uso desde otro script:
  from app.ml_models.recomendaciones.predecir_s4 import predecir_recomendacion
"""

import argparse
import json
from pathlib import Path

from app.ml_models.recomendaciones.config import (
    CAMPOS_CLINICOS,
    MODELO_CART,
    MODELO_RF,
    RECOMENDACIONES,
)
from app.ml_models.recomendaciones.datos import (
    entradas_desde_dict,
    entradas_desde_paciente,
    features_ml,
)
from app.ml_models.recomendaciones.metodos import (
    cargar_cart,
    cargar_rf,
    importancia_rf,
    predecir_cart,
    predecir_rf,
)
from app.ml_models.recomendaciones.reglas_clinicas import recomendacion_if_then

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
    if not MODELO_CART.exists():
        raise FileNotFoundError(
            f"Modelo S-4 no encontrado: {MODELO_CART}. "
            "Coloque los archivos .pkl en app/ml_models/models/"
        )
    if not MODELO_RF.exists():
        raise FileNotFoundError(
            f"Modelo S-4 no encontrado: {MODELO_RF}. "
            "Coloque los archivos .pkl en app/ml_models/models/"
        )

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
    parser = argparse.ArgumentParser(description="Recomendaciones S-4")
    parser.add_argument("--json", type=Path, help="JSON con campos clínicos o entradas S-4")
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
