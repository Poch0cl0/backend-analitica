# Fuentes teóricas S-4

Carpeta: `Informes_teoricos/`

## Variables S-4 y evidencia

| Variable | Umbral / criterio | Fuente |
|----------|-------------------|--------|
| Longitud cervical | ≤ 25 mm = cuello corto (alto riesgo) | SOGC Technical Update No. 467 (2026); Borboa-Olivares et al. 2023 |
| Parto prematuro previo | Antecedente de sPTB = factor de alto riesgo | SOGC 467; Predicting PTB ML (prior preterm birth) |
| Embarazo múltiple | Gestación múltiple asociada a mayor PTB | SOGC 467; KOPEN registry study |
| Hipertensión gestacional | Trastorno hipertensivo en embarazo = mayor riesgo | KOPEN (decision tree); Expert review AI obstetrics |
| IMC | Riesgo ↑ en BMI < 18.5 o > 30; óptimo ~22.5–25.9 kg/m² | Maternal pre-pregnancy BMI meta-analysis (collaboration large datasets) |
| Probabilidad ML | Estratificación por modelo predictivo | Explainable AI Decision Support Tool (Kyparissidis et al.); ML prediction studies |

## Niveles de urgencia (interpretación clínica)

| Nivel | Interpretación | Acción orientativa (informe) |
|-------|----------------|------------------------------|
| ROJO | Riesgo muy alto | Prioridad inmediata / vigilancia estrecha |
| NARANJA | Riesgo alto | Seguimiento reforzado |
| AMARILLO | Riesgo moderado | Vigilancia adicional |
| VERDE | Riesgo bajo | Control prenatal rutinario |

## Métodos S-4 (informe)

1. **Puntaje ponderado** — combina probabilidad del modelo + 5 factores (pesos alineados a importancia clínica en la literatura).
2. **Árbol de decisión** — entrenado con reglas clínicas derivadas de las fuentes anteriores.
3. **Regresión logística ordinal** — modela niveles ordenados VERDE < AMARILLO < NARANJA < ROJO.
