# Arquitectura del Sistema

## Visión General

Sistema de Alerta Temprana (SAT) para prevención de parto prematuro.
Arquitectura de microservicios con frontend React + TypeScript y backend FastAPI + PostgreSQL.

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + TS)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │Dashboard │ │  Citas   │ │Pacientes │ │Expediente     │  │
│  │Overview  │ │  Page    │ │  Pages   │ │Inteligente    │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────┬───────┘  │
│                                                  │          │
│  ┌───────────────────────────────────────────────┴───────┐  │
│  │                SidebarLayout + Routing                  │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP (REST)
┌──────────────────────────▼──────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │  Auth    │ │  Citas   │ │Pacientes │ │ DatosClínicos │  │
│  │  API     │ │  API     │ │  API     │ │    API        │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────┬───────┘  │
│                                                  │          │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │          │
│  │  S-2     │ │  S-3     │ │  S-4 (Gemini)    │ │          │
│  │Predicción│ │ Triaje   │ │ Recomendaciones  │◄┘          │
│  └──────────┘ └──────────┘ └──────────────────┘            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │               PostgreSQL (Async + SQLAlchemy)         │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

## Pipeline de Datos (S-2 → S-3 → S-4)

### Flujo Principal
```
Datos Clínicos → S-2 (Consenso ML) → Predicción de Riesgo
                                     → S-3 (Triaje) → Nivel de Urgencia
                                     → S-4 (Gemini) → Recomendación Clínica
```

### S-2: Predicción por Consenso
- **Modelos**: Random Forest, CatBoost, SVM
- **Entrada**: 10 campos clínicos (mager, rf_ppterm, dplural, etc.)
- **Salida**: prob_prematuro (0-1), nivel_riesgo (bajo/medio/alto/crítico), semanas_estimadas
- **Consenso**: promedio ponderado de los 3 modelos

### S-3: Triaje / Priorización
- **Modelos**: Regresión Logística Ordinal + Árbol de Decisión + Puntaje Ponderado
- **Entrada**: Datos S-2 + campos adicionales
- **Salida**: nivel_urgencia (VERDE/AMARILLO/NARANJA/ROJO), score

### S-4: Recomendaciones (Gemini)
- **Motor**: Google Gemini 2.0 Flash API
- **Entrada**: 8 variables clínicas (prob_prematuro, nivel_urgencia, parto_previo, condiciones_crónicas, IMC, longitud_cervical, infecciones, embarazo_múltiple)
- **Salida**: slug de recomendación (1 de 6 posibles) + título + descripción
- **Fallback**: Reglas clínicas determinísticas IF-THEN (basadas en SOGC 467)
- **Reintentos**: 3 intentos con backoff exponencial en caso de 429

## Stack Tecnológico

| Capa | Tecnología |
|---|---|
| Frontend | React 19 + TypeScript + Vite + Tailwind |
| Backend | FastAPI + Python 3.12+ |
| Database | PostgreSQL 16 + Asyncpg + SQLAlchemy 2.0 |
| ML | Scikit-learn, CatBoost, Joblib, Mord |
| IA | Google Gemini 2.0 Flash (REST) |
| Auth | JWT (python-jose + bcrypt) |
| Cache | Redis |
| Reportes | WeasyPrint (PDF), OpenPyXL (Excel) |

## Estructura de Directorios

```
backend-analitica/
├── app/
│   ├── api/                    # Endpoints REST
│   ├── core/                   # Config, DB, Security, Exceptions
│   ├── ml_models/              # Modelos ML (S-2, S-3, S-4 legacy)
│   ├── models/                 # SQLAlchemy ORM models
│   ├── schemas/                # Pydantic schemas
│   └── services/               # Lógica de negocio
├── migrations/                 # Alembic migrations
└── requirements.txt

frontend-analitica/
├── src/
│   ├── components/             # Componentes reutilizables
│   ├── contexts/               # React Contexts (NavContext)
│   ├── features/               # Módulos por funcionalidad
│   │   ├── auth/               # Login/Auth
│   │   ├── citas/              # Gestión de citas
│   │   ├── dashboard/          # Dashboard principal
│   │   ├── expediente-inteligente/  # Modal de expediente
│   │   ├── pacientes/          # CRUD de pacientes
│   │   ├── recomendations/     # Lista global de recomendaciones
│   │   ├── triaje/             # Página de triaje
│   │   └── usuarios/           # Gestión de usuarios
│   └── services/               # API client + funciones
├── public/
└── package.json
```

## Principios de Diseño

1. **Auto-computo**: `num_condiciones_cronicas` e `infeccion_activa` se calculan automáticamente desde campos booleanos individuales en `datos_clinicos_service._auto_computar()`
2. **Edad materna**: Se calcula desde fecha de nacimiento (`_edad_en_anios()`), no se almacena
3. **Pipeline forzado**: El triaje S-3 siempre se re-ejecuta (force=True) en el pipeline completo
4. **Fallback seguro**: Si Gemini falla (429/network), se usan reglas clínicas determinísticas
5. **Redirección**: Al guardar datos clínicos desde cualquier punto, se redirige al Expediente Inteligente
