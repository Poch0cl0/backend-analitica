"""Ejecuta S-3: puntaje ponderado, árbol de decisión y regresión logística ordinal."""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from app.ml_models.triage.config import (
    BASE,
    BMI_ALTO,
    BMI_BAJO,
    DIR_REPORTES,
    DIR_SALIDA,
    FEATURES_S3,
    LC_CORTO_MM,
    NIVEL_A_NUM,
    NIVELES,
)
from app.ml_models.triage.datos import cargar_datos_s3
from app.ml_models.triage.metodos import (
    entrenar_arbol_decision,
    entrenar_logistica_ordinal,
    predecir_arbol,
    predecir_logistica_ordinal,
    urgencia_por_puntaje,
    urgencia_por_reglas_clinicas,
)


def _distribucion(serie: pd.Series) -> pd.DataFrame:
    conteo = serie.value_counts().reindex(NIVELES, fill_value=0)
    pct = (conteo / len(serie) * 100).round(2)
    return pd.DataFrame({"nivel": conteo.index, "conteo": conteo.values, "porcentaje": pct.values})


def ejecutar() -> None:
    DIR_SALIDA.mkdir(exist_ok=True)
    DIR_REPORTES.mkdir(exist_ok=True)

    df = cargar_datos_s3()
    print(f"Pacientes: {len(df)}")
    print("Variables S-3:", FEATURES_S3)

    res_puntaje = urgencia_por_puntaje(df)

    y_ref = urgencia_por_reglas_clinicas(df)
    y_num = y_ref.map(NIVEL_A_NUM)
    X = df[FEATURES_S3]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_num, test_size=0.2, random_state=42, stratify=y_num
    )

    arbol = entrenar_arbol_decision(X_train, y_train)
    urg_arbol_train = predecir_arbol(arbol, X)
    acc_arbol = accuracy_score(y_test, arbol.predict(X_test))
    print(f"\nArbol decision — accuracy test: {acc_arbol:.4f}")

    ordinal = entrenar_logistica_ordinal(X_train, y_train)
    urg_ordinal_train = predecir_logistica_ordinal(ordinal, X)
    acc_ord = accuracy_score(y_test, ordinal.predict(X_test.values))
    print(f"Regresion logistica ordinal — accuracy test: {acc_ord:.4f}")

    salida = df.copy()
    salida = pd.concat([salida, res_puntaje, urg_arbol_train, urg_ordinal_train], axis=1)

    csv_out = DIR_SALIDA / "natality_s3_priorizacion.csv"
    salida.to_csv(csv_out, index=False)

    dist_p = _distribucion(salida["urgencia_puntaje"])
    dist_a = _distribucion(salida["urgencia_arbol"])
    dist_o = _distribucion(salida["urgencia_ordinal"])
    dist_p["metodo"] = "puntaje_ponderado"
    dist_a["metodo"] = "arbol_decision"
    dist_o["metodo"] = "logistica_ordinal"
    pd.concat([dist_p, dist_a, dist_o], ignore_index=True).to_csv(
        DIR_REPORTES / "distribucion_urgencia.csv", index=False
    )

    iguales_pa = (salida["urgencia_puntaje"] == salida["urgencia_arbol"]).mean()
    iguales_po = (salida["urgencia_puntaje"] == salida["urgencia_ordinal"]).mean()
    iguales_ao = (salida["urgencia_arbol"] == salida["urgencia_ordinal"]).mean()
    pd.DataFrame(
        [
            {"comparacion": "puntaje vs arbol", "concordancia": round(iguales_pa, 4)},
            {"comparacion": "puntaje vs ordinal", "concordancia": round(iguales_po, 4)},
            {"comparacion": "arbol vs ordinal", "concordancia": round(iguales_ao, 4)},
        ]
    ).to_csv(DIR_REPORTES / "concordancia_metodos.csv", index=False)

    modelos_dir = BASE / "modelos"
    modelos_dir.mkdir(exist_ok=True)
    joblib.dump(arbol, modelos_dir / "s4_arbol_decision.pkl")
    joblib.dump(ordinal, modelos_dir / "s4_logistica_ordinal.pkl")

    dist_txt = dist_p.to_string(index=False)
    informe = DIR_REPORTES / "informe_s3.md"
    informe.write_text(
        f"""# Informe S-3 — Clasificación por urgencia

## Entradas (6 variables)
- prob_prematuro (regresión logística S-2)
- embarazo_multiple (dplural > 1)
- cl_sim_mm (cuello corto <= {LC_CORTO_MM} mm)
- bmi (IMC; riesgo en < {BMI_BAJO} o > {BMI_ALTO} kg/m2)
- parto_previo (rf_ppterm = Y)
- hipertension_gestacional (rf_ghype = Y)

## Métodos
1. **Puntaje ponderado**
2. **Árbol de decisión** — accuracy test: {acc_arbol:.4f}
3. **Regresión logística ordinal** — accuracy test: {acc_ord:.4f}

## Pacientes
Total: {len(salida)}

## Distribución puntaje ponderado
{dist_txt}

## Concordancia entre métodos
- Puntaje vs árbol: {iguales_pa*100:.1f}%
- Puntaje vs ordinal: {iguales_po*100:.1f}%
- Árbol vs ordinal: {iguales_ao*100:.1f}%
""",
        encoding="utf-8",
    )

    print(f"\nGuardado: {csv_out}")
    print(f"Reportes: {DIR_REPORTES}")


if __name__ == "__main__":
    ejecutar()
