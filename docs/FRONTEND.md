# Frontend — Estructura y Componentes

## Stack
- React 19 + TypeScript
- Vite (bundler)
- Tailwind CSS (estilos)
- React Router v7 (ruteo)
- Lucide React (iconos)

## Routing (`App.tsx`)

```
/ → Login
/dashboard → DashboardOverview (SidebarLayout)
/citas → CitasPage (SidebarLayout)
/pacientes → PacientesPage (SidebarLayout)
/pacientes/:id → PacienteDetalle (SidebarLayout)
/triaje → TriajePage (SidebarLayout) [medico/admin]
/recomendaciones → RecommendationsList (SidebarLayout) [medico/admin]
/feedback → FeedbackAnalytics (SidebarLayout) [medico/admin]
/usuarios → UsuariosPage (SidebarLayout) [admin]
```

## SidebarLayout (`components/SidebarLayout.tsx`)

Menú lateral con grupos:
- **PRINCIPAL**: Dashboard, Citas, Pacientes
- **MÓDULOS CLÍNICOS**: Triaje, Recomendaciones, Rendimiento Modelos
- **GESTIÓN**: Usuarios (admin)

Filtra ítems según rol del usuario (`user_role` en localStorage).

## Módulos Principales

### Dashboard (`features/dashboard/`)
- `DashboardOverview.tsx` — Panel principal con KPIs, citas de hoy, calendario
- Atiende query param `?expediente=id` para abrir modal de expediente inteligente
- `handleAtender` usa pipeline completo + abre expediente modal

### Citas (`features/citas/`)
- `CitasPage.tsx` — Listado completo de citas con CRUD
- `CitaDetailModal.tsx` — Modal de detalle de cita
- `AtenderCitaModal.tsx` — Modal para atender cita (datos clínicos)
- `handleAtender` redirige a `/dashboard?expediente=id`

### Pacientes (`features/pacientes/`)
- `PacientesPage.tsx` — Listado de pacientes
- `PacienteDetalle.tsx` — Detalle con tabs: Datos Personales / Datos Clínicos / Citas
- `handleSaveDc` ejecuta pipeline + abre expediente modal
- `handleAtender` ejecuta pipeline + abre expediente modal

### Expediente Inteligente (`features/expediente-inteligente/`)
Modal con 3 tabs:
- **Predicción** (`components/PredictionTab.tsx`): Muestra riesgo, variables clínicas, historial
- **Triaje** (`components/TriageTab.tsx`): Nivel de urgencia, score, acciones
- **Recomendaciones** (`components/RecommendationTab.tsx`): Recomendación generada por Gemini

Hooks:
- `hooks/usePrediccion.ts` — Carga perfil + última predicción + historial
- `hooks/useTriaje.ts` — Carga triaje del paciente
- `hooks/useRecomendaciones.ts` — Carga recomendaciones + genera nuevas

### Triaje (`features/triaje/`)
- `TriajePage.tsx` — Vista completa de priorización por urgencia
- KPIs por nivel, filtro por algoritmo, acciones (PDF, Enviar, Ver clínicos)

### API Client (`services/api.ts`)
Funciones principales:
- `getPacientes`, `createPaciente`, `updatePaciente`
- `getCitas`, `createCita`, `updateCita`, `deleteCita`, `changeCitaEstado`
- `getDatosClinicos`, `createDatosClinicos`, `updateDatosClinicos`
- **`createAndAnalizarDatosClinicos`** — POST + pipeline completo
- **`updateAndAnalizarDatosClinicos`** — PUT + pipeline completo
- `getUltimaPrediccion`, `ejecutarPrediccionConsenso`
- `getTriajeResumen`, `getTriajePriorizados`, `sincronizarTriaje`
- `getRecomendacionesPaciente`, `ejecutarRecomendacionesS4`
- `getDashboardResumen`

## Flujo de "Atender Cita" (3 puntos de entrada)

```
CitasPage                    DashboardOverview             PacienteDetalle
    │                              │                            │
    ▼                              ▼                            ▼
handleAtender()              handleAtender()              handleAtender()
    │                              │                            │
    ▼                              ▼                            ▼
create/updateAndAnalizar()   create/updateAndAnalizar()   create/updateAndAnalizar()
    │                              │                            │
    ▼                              ▼                            ▼
changeCitaEstado('cumplida') changeCitaEstado('cumplida') changeCitaEstado('cumplida')
    │                              │                            │
    ▼                              ▼                            ▼
navigate('/dashboard         setShowExpedienteModal(true) setShowExpedienteModal(true)
  ?expediente=id')                 │                            │
    │                              │                            │
    └──────────────────────────────┴────────────────────────────┘
                                  │
                                  ▼
                  ExpedienteInteligenteModal
                  (Predicción | Triaje | Recomendaciones)
```

## Componentes Compartidos

| Componente | Ubicación | Uso |
|---|---|---|
| `DatosClinicosAtenderForm` | `components/` | Formulario de datos clínicos (usado en 3 lugares) |
| `DcAtenderFormView` | `components/` | Vista del formulario |
| `DcAtenderReadonlyView` | `components/` | Vista solo lectura |
| `SidebarLayout` | `components/` | Layout principal con sidebar |
| `ExpedienteInteligenteModal` | `features/expediente-inteligente/` | Modal de expediente |

## Tipos Importantes

```typescript
interface AnalizarResponse {
  datos_clinicos: DatosClinicosResponse;
  prediccion: {
    prediccion_id: number;
    prob_consenso: number;
    nivel_riesgo: string;
    modelos: ModelosConsenso;
  };
}

interface RecomendacionResponse {
  id: number;
  algoritmo: string;       // 'gemini' | 'manual'
  origen: string;          // 'gemini' | 's4_auto' | 'manual'
  titulo: string;
  descripcion: string;
  estado: string;
  intervencion: { id: number; codigo: string; nombre: string; categoria: string };
  fecha_recomendacion: string;
}
```
