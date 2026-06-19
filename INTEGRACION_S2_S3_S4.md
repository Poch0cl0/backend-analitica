# Integración S-2, S-3 y S-4 — Backend + Frontend

> **Importante — nombres de carpetas vs informe**
>
> | Carpeta en el código | Módulo del informe |
> |----------------------|-------------------|
> | `s4_priorizacion/` | **S-3** — Priorización por urgencia |
> | `s4_recomendaciones/` | **S-4** — Recomendaciones clínicas |
>
> La carpeta se llama `s4_priorizacion` por historial del repo, pero en el **informe es S-3**.

---

## Carpetas que debes recibir

**Backend integrado (FastAPI):** todos los artefactos en `app/ml_models/models/`  
Variable: `ML_MODELS_PATH=app/ml_models/models` (ver `.env.example`).

**Scripts legacy en raíz del repo** (si aún los usas aparte):

```
s4_priorizacion/      ← S-3 priorización (informe)
s4_recomendaciones/   ← S-4 recomendaciones (informe)
modelos/              ← .pkl en raíz (solo scripts legacy)
```

Validar inferencia en el backend integrado:

```bash
python scripts/validar_modelos.py
```

---

## S-2 — Predicción (prematuro + semanas)

**Entrada:** 9 campos clínicos (`mager`, `rf_ppterm`, `dplural`, `num_condiciones_cronicas`, `infeccion_activa`, `priorlive`, `bmi`, `cl_sim_mm`, `combgest`)

**Modelos** (ruta integrada `app/ml_models/models/`):
- `prematuro_logistic.pkl` → probabilidad + clase prematuro
- `semanas_lineal.pkl` → semanas estimadas

**Salida:**
```json
{ "prob_prematuro": 0.47, "prematuro": 0, "semanas_estimadas": 38.2 }
```

---

## S-3 — Priorización por urgencia (carpeta `s4_priorizacion/`)

**Entrada:** 10 campos (9 de S-2 + `rf_ghype`)

**Archivos:**
| Archivo | Uso |
|---------|-----|
| `app/ml_models/triage/predecir_s3.py` | Punto de entrada integrado |
| `app/ml_models/models/prematuro_logistic.pkl` | Probabilidad |
| `app/ml_models/models/s4_arbol_decision.pkl` | Árbol → niveles ROJO/NARANJA/AMARILLO/VERDE |
| `app/ml_models/models/s4_logistica_ordinal.pkl` | Ordinal → número 0–3 |
| `s4_priorizacion/config.py` + `metodos.py` | Puntaje ponderado → número |

**Código:**
```python
from predecir_s4 import predecir_urgencia
r = predecir_urgencia({ ... 10 campos clínicos ... })
```

**Salida:**
```json
{
  "puntaje_s4": 0.16,
  "urgencia_puntaje": "VERDE",
  "urgencia_arbol": "NARANJA",
  "urgencia_ordinal": "NARANJA"
}
```

**Para S-4 (recomendaciones) usar:** `r["urgencia_arbol"]` como nivel de urgencia.

---

## S-4 — Recomendaciones clínicas (carpeta `s4_recomendaciones/`)

**Entrada (9 campos):**

| Campo | Origen |
|-------|--------|
| `prob_prematuro` | S-2 |
| `nivel_urgencia` | S-3 → `urgencia_arbol` |
| `parto_previo` | `rf_ppterm` Y/N → 0/1 |
| `cl_sim_mm` | Longitud cervical |
| `hipertension_gestacional` | `rf_ghype` Y/N → 0/1 |
| `bmi` | IMC |
| `infeccion_activa` | 0/1 |
| `num_condiciones_cronicas` | número |
| `embarazo_multiple` | `dplural > 1` → 0/1 |

**Archivos:**
| Archivo | Método |
|---------|--------|
| `app/ml_models/recomendaciones/predecir_s4.py` | Punto de entrada integrado |
| `app/ml_models/recomendaciones/reglas_clinicas.py` | IF-THEN (sin .pkl) |
| `app/ml_models/models/recomendaciones_cart.pkl` | CART |
| `app/ml_models/models/recomendaciones_random_forest.pkl` | Random Forest |
| `prematuro_logistic.pkl` + `s4_arbol_decision.pkl` en `models/` | Solo si entras con campos clínicos |

**Opción A — Campos clínicos (calcula S-2 + S-3 solo):**
```python
from predecir_recomendacion import predecir_recomendacion
r = predecir_recomendacion({ ... 10 campos clínicos ... })
```

**Opción B — 9 entradas ya calculadas:**
```python
r = predecir_recomendacion({ ... 9 entradas ... }, clinico=False)
```

**Salida:**
```json
{
  "recomendacion_if_then": "progesterona_vaginal",
  "recomendacion_cart": "progesterona_vaginal",
  "recomendacion_random_forest": "progesterona_vaginal",
  "importancia_variables_rf": [ ... ]
}
```

**Recomendaciones posibles:**
`control_prenatal_rutinario`, `seguimiento_estrecho_lc`, `progesterona_vaginal`, `tratar_infeccion`, `vigilancia_hta_multiple`, `derivacion_alto_riesgo`

---

## Flujo completo backend

```
POST /api/predict
  → S-2 (prob + semanas)
  → S-3 predecir_urgencia() 
  → S-4 predecir_recomendacion()
  → JSON unificado al frontend
```

## Endpoints sugeridos

| Endpoint | Entrada | Salida |
|----------|---------|--------|
| `POST /api/s2/predict` | 9 campos | prob, prematuro, semanas |
| `POST /api/s3/predict` | 10 campos | puntaje + urgencias |
| `POST /api/s4/predict` | 10 campos clínicos | 3 recomendaciones + importancia RF |

## Dependencias

```
pandas, scikit-learn, joblib, mord
```

## Probar en terminal

```bash
cd s4_priorizacion && python predecir_s4.py
cd s4_recomendaciones && python predecir_recomendacion.py
```

## Entrenar modelos S-4 (solo una vez, local)

```bash
cd s4_recomendaciones && python ejecutar_s4_rec.py
```

Genera `app/ml_models/models/recomendaciones_cart.pkl` y `recomendaciones_random_forest.pkl`.
