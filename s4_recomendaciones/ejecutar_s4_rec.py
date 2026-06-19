"""Entrena CART y Random Forest (etiquetas IF-THEN) y genera reportes."""

import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import DIR_REPORTES, DIR_SALIDA, RECOMENDACIONES
from preparar_datos import cargar_dataset_entrenamiento
from metodos import (
    entrenar_cart,
    entrenar_rf,
    evaluar,
    guardar_modelos,
    importancia_rf,
)


def ejecutar() -> None:
    DIR_SALIDA.mkdir(exist_ok=True)
    DIR_REPORTES.mkdir(exist_ok=True)

    X, y = cargar_dataset_entrenamiento()
    print(f"Pacientes: {len(X)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    cart, le_cart = entrenar_cart(X_train, y_train)
    rf, le_rf = entrenar_rf(X_train, y_train)

    acc_cart = evaluar(cart, le_cart, X_test, y_test)
    acc_rf = evaluar(rf, le_rf, X_test, y_test)
    print(f"CART — accuracy test: {acc_cart:.4f}")
    print(f"Random Forest — accuracy test: {acc_rf:.4f}")

    guardar_modelos(cart, le_cart, rf, le_rf)

    imp = importancia_rf(rf)
    imp.to_csv(DIR_REPORTES / "importancia_variables_rf.csv", index=False)

    dist = y.value_counts().reindex(RECOMENDACIONES, fill_value=0)
    dist.to_csv(DIR_REPORTES / "distribucion_recomendaciones.csv")

    informe = DIR_REPORTES / "informe_s4_recomendaciones.md"
    informe.write_text(
        f"""# Informe S-4 — Recomendaciones clínicas

## Entradas (9)
prob_prematuro, nivel_urgencia (S-3), parto_previo, cl_sim_mm,
hipertension_gestacional, bmi, infeccion_activa, num_condiciones_cronicas, embarazo_multiple

## Métodos
1. **Reglas IF-THEN** — guías clínicas (SOGC 467)
2. **CART** — accuracy test: {acc_cart:.4f}
3. **Random Forest** — accuracy test: {acc_rf:.4f} + importancia de variables

## Recomendaciones posibles
{', '.join(RECOMENDACIONES)}

## Importancia RF (top 5)
{imp.head(5).to_string(index=False)}

## Archivos
- modelos/recomendaciones_cart.pkl
- modelos/recomendaciones_random_forest.pkl
- s4_recomendaciones/predecir_recomendacion.py
""",
        encoding="utf-8",
    )

    csv_out = DIR_SALIDA / "natality_s4_recomendaciones.csv"
    out = X.copy()
    out["recomendacion_if_then"] = y.values
    out["recomendacion_cart"] = le_cart.inverse_transform(cart.predict(X))
    out["recomendacion_rf"] = le_rf.inverse_transform(rf.predict(X))
    out.to_csv(csv_out, index=False)

    print(f"\nGuardado: {csv_out}")
    print(f"Reportes: {DIR_REPORTES}")


if __name__ == "__main__":
    ejecutar()
