# API Endpoints Reference

## Autenticación

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/auth/login` | Iniciar sesión |
| POST | `/api/auth/register` | Registrar usuario |
| GET | `/api/auth/me` | Perfil del usuario actual |

## Pacientes

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/pacientes` | Listar pacientes (paginado) |
| POST | `/api/pacientes` | Crear paciente |
| GET | `/api/pacientes/{id}` | Obtener paciente |
| PUT | `/api/pacientes/{id}` | Actualizar paciente |
| GET | `/api/pacientes/{id}/perfil` | Perfil completo con datos clínicos + predicción + triaje |

## Datos Clínicos

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/datos-clinicos/{paciente_id}` | Obtener datos clínicos |
| POST | `/api/datos-clinicos/{paciente_id}` | Crear datos clínicos |
| PUT | `/api/datos-clinicos/{paciente_id}` | Actualizar datos clínicos |
| **POST** | `/api/datos-clinicos/{paciente_id}/analizar` | **Crear + ejecutar pipeline completo (S-2+S-3+S-4)** |
| **PUT** | `/api/datos-clinicos/{paciente_id}/analizar` | **Actualizar + ejecutar pipeline completo (S-2+S-3+S-4)** |

## Citas

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/citas` | Listar citas (filtro por fecha) |
| POST | `/api/citas` | Crear cita |
| GET | `/api/citas/{id}` | Obtener cita con detalle |
| PUT | `/api/citas/{id}` | Actualizar cita |
| DELETE | `/api/citas/{id}` | Cancelar cita |
| PATCH | `/api/citas/{id}/estado` | Cambiar estado (programada/en_atencion/cumplida/cancelada) |

## Predicción (S-2)

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/s2/predict` | Ejecutar modelo S-2 individual |
| POST | `/api/s2/consenso` | Ejecutar consenso S-2 (RF + CatBoost + SVM) |
| GET | `/api/s2/ultima/{paciente_id}` | Última predicción del paciente |
| GET | `/api/s2/historial/{paciente_id}` | Historial de predicciones |
| POST | `/api/s2/feedback` | Enviar feedback sobre predicción |

## Triaje (S-3)

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/s3/predict` | Ejecutar modelo S-3 individual |
| GET | `/api/triage/priorizados` | Listar pacientes priorizados por nivel |
| POST | `/api/triage/sincronizar` | Sincronizar triaje para todos los pacientes elegibles |
| GET | `/api/triage/resumen` | Conteo de pacientes por nivel de urgencia |

## Recomendaciones (S-4) — Gemini

| Método | Ruta | Descripción |
|--------|------|-------------|
| **POST** | `/api/recomendaciones/ejecutar/{paciente_id}/{prediccion_id}` | **Generar recomendación vía Gemini (con fallback)** |
| GET | `/api/recomendaciones` | Listar recomendaciones (paginado, con filtros) |
| GET | `/api/recomendaciones/paciente/{paciente_id}` | Recomendaciones de un paciente |
| GET | `/api/recomendaciones/{id}` | Obtener recomendación |
| POST | `/api/recomendaciones/manual` | Crear recomendación manual |
| PUT | `/api/recomendaciones/{id}` | Actualizar recomendación |
| DELETE | `/api/recomendaciones/{id}` | Cancelar recomendación |

## Dashboard

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/dashboard/resumen` | KPIs del dashboard |

## Reportes

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/reportes/paciente/{id}` | Exportar reporte de paciente (PDF) |
| POST | `/api/reportes/paciente/{id}/enviar` | Enviar reporte por email |

## Intervenciones (Catálogo)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/intervenciones` | Listar catálogo de intervenciones |
| GET | `/api/intervenciones/{id}` | Obtener intervención |

## Formato de Respuesta para Pipeline Completo

### POST/PUT /api/datos-clinicos/{id}/analizar

```json
{
  "datos_clinicos": { "... campos de DatosClinicos ..." },
  "prediccion": {
    "prediccion_id": 123,
    "prob_consenso": 0.35,
    "nivel_riesgo": "medio",
    "modelos": {
      "random_forest": { "prob_prematuro": 0.32, "semanas_estimadas": 37.5 },
      "catboost": { "prob_prematuro": 0.38, "semanas_estimadas": 36.8 },
      "svm": { "prob_prematuro": 0.35, "semanas_estimadas": 37.0 }
    }
  }
}
```

### POST /api/recomendaciones/ejecutar/{id}/{prediccion_id}

```json
{
  "paciente_id": 1,
  "paciente_nombre": "Ana Pérez García",
  "prediccion_id": 123,
  "prob_prematuro": 0.35,
  "nivel_urgencia": "AMARILLO",
  "recomendacion_gemini": {
    "recomendacion_id": 456,
    "recomendacion": "seguimiento_estrecho_lc",
    "titulo": "Seguimiento estrecho por longitud cervical corta",
    "descripcion": "Paciente con longitud cervical de 22mm...",
    "intervencion": {
      "id": 3,
      "codigo": "seguimiento_estrecho_lc",
      "nombre": "Seguimiento estrecho por longitud cervical corta",
      "categoria": "monitoreo"
    }
  }
}
```
