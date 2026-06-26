# Changelog — Todas las Modificaciones Realizadas

## Sesión: Pipeline Completo + Gemini + Triaje Sidebar + Redirección

### Migración Base de Datos
| Archivo | Cambio |
|---------|--------|
| `migrations/versions/0007_update_datos_clinicos_vars.py` | `embarazo_multiple` BOOLEAN → SMALLINT default 1; recrea vistas y función dependientes |

### Backend — Modelos
| Archivo | Cambio |
|---------|--------|
| `backend-analitica/app/models/datos_clinicos.py` | `embarazo_multiple: Mapped[int]` con `SmallInteger` en vez de `Boolean` |

### Backend — Schemas
| Archivo | Cambio |
|---------|--------|
| `backend-analitica/app/schemas/datos_clinicos.py` | `embarazo_multiple: int = Field(1, ge=1, le=3)` |
| `backend-analitica/app/schemas/recomendacion.py` | Nuevo `RecomendacionGeminiResult`, actualizado `RecomendacionEjecutadaResponse` |

### Backend — Services
| Archivo | Cambio |
|---------|--------|
| `backend-analitica/app/services/datos_clinicos_service.py` | Nuevo `_auto_computar()` suma condiciones crónicas e infecciones desde booleanos |
| `backend-analitica/app/services/prediccion_service.py` | `dplural` usa `int(dc.embarazo_multiple)`; nuevo `ejecutar_pipeline_completo()` (S-2+S-3+S-4); `_generar_triage_automatico` con parámetro `force`; nuevo `_generar_recomendaciones_automatico` |
| `backend-analitica/app/services/gemini_service.py` | **NUEVO** — cliente Gemini API REST con retry exponencial, prompt con criterios estrictos, temperatura 0.1 |
| `backend-analitica/app/services/recomendacion_service.py` | **REWRITE** — Gemini con fallback rule-based determinístico; guarda una recomendación con `algoritmo="gemini"`, `origen="gemini"`; función `_fallback_recomendacion()` con reglas IF-THEN |

### Backend — API
| Archivo | Cambio |
|---------|--------|
| `backend-analitica/app/api/datos_clinicos.py` | `PUT /{id}/analizar` ejecuta pipeline completo; nuevo `POST /{id}/analizar` (crear + analizar) |
| `backend-analitica/app/api/recomendaciones.py` | Endpoint `POST /ejecutar/{paciente_id}/{prediccion_id}` usa Gemini |

### Backend — Core
| Archivo | Cambio |
|---------|--------|
| `backend-analitica/app/core/config.py` | Agregado `GEMINI_APIKEY` |

### Backend — Seeds
| Archivo | Cambio |
|---------|--------|
| `backend-analitica/app/seed/seeds.py` | `embarazo_multiple` cambiado a valores enteros 1/2/3 |

### Frontend — API Client
| Archivo | Cambio |
|---------|--------|
| `frontend-analitica/src/services/api.ts` | Nuevas: `createAndAnalizarDatosClinicos`, `updateAndAnalizarDatosClinicos`; nueva interfaz `AnalizarResponse` |

### Frontend — Features
| Archivo | Cambio |
|---------|--------|
| `frontend-analitica/src/features/dashboard/DashboardOverview.tsx` | Lee `?expediente=id` y abre modal; `handleAtender` usa pipeline + abre modal |
| `frontend-analitica/src/features/citas/CitasPage.tsx` | `handleAtender` usa pipeline + redirige a `/dashboard?expediente=id` |
| `frontend-analitica/src/features/pacientes/PacienteDetalle.tsx` | `handleSaveDc` y `handleAtender` usan pipeline + abren modal |
| `frontend-analitica/src/features/expediente-inteligente/components/RecommendationTab.tsx` | Simplificado: sin selector de modelos, badge "Generado por IA" |
| `frontend-analitica/src/features/expediente-inteligente/hooks/useRecomendaciones.ts` | Simplificado: sin filtro por algoritmo |

### Frontend — Routing
| Archivo | Cambio |
|---------|--------|
| `frontend-analitica/src/components/SidebarLayout.tsx` | Agregado ítem "Triaje" en "MÓDULOS CLÍNICOS" |
| `frontend-analitica/src/App.tsx` | Ruta `/triaje` protegida para `medico`/`administrador` |
