# ML Pipeline — Predicción, Triaje y Recomendaciones

## S-2: Predicción de Parto Prematuro (Consenso)

### Modelos
| Modelo | Archivo | Peso en Consenso |
|--------|---------|-----------------|
| Random Forest | `rf_model.pkl` | 0.34 |
| CatBoost | `catboost_model.cbm` | 0.33 |
| SVM | `svm_model.pkl` | 0.33 |

### Variables de Entrada (10)
| Variable | Descripción | Fuente |
|----------|-------------|--------|
| `mager` | Edad materna (calculada) | fecha_nacimiento |
| `semanas` | Edad gestacional | edad_gestacional_semanas |
| `dias` | Días gestacional | edad_gestacional_dias |
| `rf_ppterm` | Parto prematuro previo | parto_prematuro_previo |
| `dplural` | Embarazo múltiple | embarazo_multiple (int) |
| `rf_imc` | IMC pregestacional | imc_pre_gestacional |
| `rf_lc` | Longitud cervical (mm) | longitud_cervical |
| `rf_cc` | Condiciones crónicas | num_condiciones_cronicas (auto) |
| `rf_inf` | Infección activa | infeccion_activa (auto) |
| `dm_edad_gestacional_dias` | Días gestacional (duplicado) | edad_gestacional_dias |

### Salida del Consenso
```json
{
  "prob_consenso": 0.35,
  "nivel_riesgo": "medio",
  "semanas_estimadas": 37.1,
  "modelos": {
    "random_forest": { "prob_prematuro": 0.32, "semanas_estimadas": 37.5 },
    "catboost": { "prob_prematuro": 0.38, "semanas_estimadas": 36.8 },
    "svm": { "prob_prematuro": 0.35, "semanas_estimadas": 37.0 }
  }
}
```

## S-3: Triaje / Priorización

### Modelos
- `modelo_ordinal.pkl` (Ordinal Logistic Regression — Mord)
- `arbol_decision_triage.pkl` (Decision Tree Classifier)
- Puntaje ponderado combinando ambos

### Variables de Entrada
| Variable | Descripción |
|----------|-------------|
| `prob_prematuro` | Probabilidad de consenso S-2 |
| `nivel_riesgo` | Categoría de riesgo S-2 |
| `parto_previo` | Antecedente de parto prematuro |
| `condiciones_cronicas` | Número de condiciones crónicas |
| `infeccion_activa` | Número de infecciones activas |
| `imc` | IMC pregestacional |
| `longitud_cervical` | Longitud cervical (mm) |
| `embarazo_multiple` | Número de fetos (1/2/3) |

### Niveles de Urgencia
| Nivel | Color | Descripción |
|-------|-------|-------------|
| VERDE | 🟢 | Riesgo bajo, control prenatal rutinario |
| AMARILLO | 🟡 | Riesgo moderado, seguimiento estrecho |
| NARANJA | 🟠 | Riesgo alto, intervención temprana |
| ROJO | 🔴 | Riesgo crítico, derivación inmediata |

## S-4: Recomendaciones (Gemini con Fallback)

### Gemini API
- **Modelo**: `gemini-2.0-flash`
- **Endpoint**: `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent`
- **Auth**: API key en `GEMINI_APIKEY` (`.env`)
- **Temperatura**: 0.1 (baja, para respuestas determinísticas)
- **Max tokens**: 1024

### Variables de Entrada al Prompt
| Variable | Rango | Ejemplo |
|----------|-------|---------|
| `prob_prematuro` | 0.0 - 1.0 | 0.35 |
| `nivel_urgencia` | VERDE/AMARILLO/NARANJA/ROJO | AMARILLO |
| `parto_prematuro_previo` | Sí/No | Sí |
| `num_condiciones_cronicas` | 0-4 | 1 |
| `imc_pre_gestacional` | numérico | 28.5 |
| `longitud_cervical_mm` | numérico | 22.0 |
| `infeccion_activa` | 0-3 | 1 |
| `embarazo_multiple` | 1-3 | 1 |

### Slugs de Recomendación (6 posibles)
| Slug | Criterio Clave |
|------|----------------|
| `control_prenatal_rutinario` | Bajo riesgo, sin factores |
| `seguimiento_estrecho_lc` | Longitud cervical < 25mm |
| `progesterona_vaginal` | Parto prematuro previo + LC < 25mm |
| `tratar_infeccion` | Infección activa presente |
| `vigilancia_hta_multiple` | HTA + embarazo múltiple |
| `derivacion_alto_riesgo` | Riesgo crítico + múltiples factores |

### Fallback Rule-Based (IF-THEN)
Cuando Gemini falla (429, timeout, NetworkError), se aplican reglas determinísticas:

```python
if nivel_urgencia == "ROJO" or (prob_prematuro > 0.7 and nivel_riesgo == "critico"):
    → derivacion_alto_riesgo
elif infeccion_activa > 0:
    → tratar_infeccion
elif parto_prematuro_previo and longitud_cervical < 25:
    → progesterona_vaginal
elif longitud_cervical < 25:
    → seguimiento_estrecho_lc
elif condiciones_cronicas > 0 and embarazo_multiple > 1:
    → vigilancia_hta_multiple
else:
    → control_prenatal_rutinario
```

### Retry Estrategia
- **Intento 1**: timeout 15s
- **Intento 2**: timeout 15s (espera 1s tras 429)
- **Intento 3**: timeout 15s (espera 2s tras 429)
- **Fallback**: reglas IF-THEN si todos fallan

### Pipeline Completo
```python
async def ejecutar_pipeline_completo(paciente_id, datos_clinicos_id):
    # 1. Obtener snapshot del paciente
    snapshot = await obtener_snapshot(paciente_id)

    # 2. S-2: Consenso de modelos
    prediccion_db, resultados = await ejecutar_prediccion_consenso(
        paciente_id, datos_clinicos_id, snapshot
    )

    # 3. S-3: Triaje (force=True — siempre re-ejecutar)
    triage_db = await _generar_triage_automatico(
        prediccion_db, resultados, paciente_id, force=True
    )

    # 4. S-4: Recomendación (Gemini + fallback)
    await _generar_recomendaciones_automatico(
        prediccion_db.id, paciente_id,
        resultados.consenso, triage_db.nivel_urgencia, snapshot
    )

    return prediccion_db, resultados
```

## Archivos Relevantes

### Backend
- `backend-analitica/app/services/prediccion_service.py` — S-2 + orquestación pipeline
- `backend-analitica/app/services/triage_service.py` — S-3
- `backend-analitica/app/services/recomendacion_service.py` — S-4 Gemini + fallback
- `backend-analitica/app/services/gemini_service.py` — Cliente Gemini API con retry
- `backend-analitica/app/services/datos_clinicos_service.py` — Auto-computo + validación
- `backend-analitica/app/api/datos_clinicos.py` — Endpoints `/analizar`
- `backend-analitica/app/api/recomendaciones.py` — Endpoint `POST /ejecutar`
- `backend-analitica/app/schemas/recomendacion.py` — Schemas Gemini result
- `backend-analitica/app/core/config.py` — Config + GEMINI_APIKEY

### Frontend
- `frontend-analitica/src/features/expediente-inteligente/components/RecommendationTab.tsx` — UI Gemini badge
- `frontend-analitica/src/features/expediente-inteligente/hooks/useRecomendaciones.ts` — Hook simplificado
- `frontend-analitica/src/services/api.ts` — `createAndAnalizarDatosClinicos`, `updateAndAnalizarDatosClinicos`
