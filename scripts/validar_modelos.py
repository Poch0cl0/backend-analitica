#!/usr/bin/env python3
"""Valida presencia de artefactos ML e inferencia S-2/S-3/S-4."""

from __future__ import annotations

import sys
from pathlib import Path

# Raíz del repo en sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ml_models.paths import resolve_ml_models_dir

_PACIENTE = {
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

_ARCHIVOS_REQUERIDOS = [
    "prematuro_logistic.pkl",
    "semanas_lineal.pkl",
    "prematuro_random_forest.pkl",
    "semanas_random_forest.pkl",
    "prematuro_catboost.cbm",
    "semanas_catboost.cbm",
    "prematuro_svm.pkl",
    "semanas_svm.pkl",
    "s4_arbol_decision.pkl",
    "s4_logistica_ordinal.pkl",
    "recomendaciones_cart.pkl",
    "recomendaciones_random_forest.pkl",
]


def _verificar_archivos(models_dir: Path) -> list[str]:
    faltantes = [name for name in _ARCHIVOS_REQUERIDOS if not (models_dir / name).exists()]
    if faltantes:
        print(f"[FAIL] Archivos faltantes en {models_dir}:")
        for name in faltantes:
            print(f"  - {name}")
    else:
        print(f"[OK] Todos los archivos requeridos presentes en {models_dir}")
    return faltantes


def _probar_s2() -> bool:
    try:
        from app.ml_models.prediccion.predecir_s2 import predecir_s2_consenso

        r = predecir_s2_consenso(_PACIENTE)
        assert "prob_consenso" in r and "modelos" in r
        print(f"[OK] S-2 consenso — prob_consenso={r['prob_consenso']}, nivel={r['nivel_riesgo']}")
        return True
    except Exception as exc:
        print(f"[FAIL] S-2 consenso — {exc}")
        return False


def _probar_s3() -> bool:
    try:
        from app.ml_models.triage.predecir_s3 import predecir_urgencia

        r = predecir_urgencia(_PACIENTE)
        assert "urgencia_arbol" in r
        print(f"[OK] S-3 triaje — urgencia_arbol={r['urgencia_arbol']}")
        return True
    except Exception as exc:
        print(f"[FAIL] S-3 triaje — {exc}")
        return False


def _probar_s4() -> bool:
    try:
        from app.ml_models.recomendaciones.predecir_s4 import predecir_recomendacion

        r = predecir_recomendacion(_PACIENTE, clinico=True)
        assert "recomendacion_if_then" in r
        print(f"[OK] S-4 recomendaciones — if_then={r['recomendacion_if_then']}")
        return True
    except Exception as exc:
        print(f"[FAIL] S-4 recomendaciones — {exc}")
        return False


def main() -> int:
    models_dir = resolve_ml_models_dir()
    print(f"Directorio de modelos: {models_dir}\n")

    faltantes = _verificar_archivos(models_dir)
    print()

    ok_s2 = _probar_s2()
    ok_s3 = _probar_s3()
    ok_s4 = _probar_s4()

    print()
    if faltantes or not (ok_s2 and ok_s3 and ok_s4):
        print("Validación FALLIDA")
        return 1
    print("Validación EXITOSA")
    return 0


if __name__ == "__main__":
    sys.exit(main())
