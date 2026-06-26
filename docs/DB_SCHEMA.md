# Base de Datos — Migraciones y Schema

## Tecnología
- PostgreSQL 16
- SQLAlchemy 2.0 (async)
- Asyncpg (driver)
- Alembic (migraciones)
- Naming convention: `ix_%(column_0_label)s`, `uq_%(table_name)s_%(column_0_name)s`, `ck_%(table_name)s_%(constraint_name)s`, `fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s`, `pk_%(table_name)s`

## Migraciones Principales

### 0001 → 0006 (Setup inicial a modelos ML)
Migraciones base:
- Creación de tablas: `pacientes`, `datos_clinicos`, `predicciones`, `triage`, `recomendaciones`, `intervenciones`, `citas`, `usuarios`
- Modelos ML: RF, CatBoost, SVM para S-2
- Modelos S-3: Ordinal Logistic, Decision Tree
- Vistas: `vista_triage_priorizado`, `vista_perfil_completo`
- Función: `obtener_snapshot_clinico`

### 0007 — Update Datos Clínicos Vars (ÚLTIMA)

**Cambios:**
1. `datos_clinicos.embarazo_multiple` pasa de **BOOLEAN** a **SMALLINT** con default 1
2. Tabla de respaldo creada: `datos_clinicos_backup_0007`
3. Vistas dependientes recreadas:
   - `vista_triage_priorizado`
   - `vista_perfil_completo`
4. Función `obtener_snapshot_clinico` recreada
5. Campos `embarazo_multiple` con 0 pasan a 1 (default)

## Schema de Tablas Clave

### pacientes
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | SERIAL PK | |
| nombres | VARCHAR(100) | |
| apellidos | VARCHAR(100) | |
| dni | VARCHAR(20) UNIQUE | |
| fecha_nacimiento | DATE | Para cálculo de edad (mager) |
| telefono | VARCHAR(20) | |
| email | VARCHAR(100) | |
| direccion | TEXT | |
| seguro | VARCHAR(50) | |
| activo | BOOLEAN | Soft delete |

### datos_clinicos
| Columna | Tipo | Descripción | Auto-computado |
|---------|------|-------------|----------------|
| id | SERIAL PK | | |
| paciente_id | FK → pacientes | | |
| fecha_registro | TIMESTAMP | | |
| edad_gestacional_semanas | INTEGER(4) | | |
| edad_gestacional_dias | INTEGER(6) | | |
| longitud_cervical | FLOAT | mm | |
| parto_prematuro_previo | BOOLEAN | | |
| embarazo_multiple | SMALLINT | 1/2/3 fetos | |
| imc_pre_gestacional | FLOAT | | |
| hipertension | BOOLEAN | | |
| diabetes | BOOLEAN | | |
| preeclampsia | BOOLEAN | | |
| otras_condiciones | BOOLEAN | | |
| infeccion_urinaria | BOOLEAN | | |
| infeccion_vaginal | BOOLEAN | | |
| infeccion_sistemica | BOOLEAN | | |
| num_condiciones_cronicas | INTEGER | **Auto-computado** | ✓ (suma hipertension+diabetes+preeclampsia+otras_condiciones) |
| infeccion_activa | INTEGER | **Auto-computado** | ✓ (suma infeccion_urinaria+infeccion_vaginal+infeccion_sistemica) |

### predicciones (S-2)
| Columna | Tipo |
|---------|------|
| id, paciente_id, datos_clinicos_id | PK + FKs |
| prob_prematuro | FLOAT (0-1) |
| nivel_riesgo | VARCHAR (bajo/medio/alto/crítico) |
| semanas_estimadas | FLOAT |
| algoritmo | VARCHAR |

### triage (S-3)
| Columna | Tipo |
|---------|------|
| id, paciente_id, prediccion_id | PK + FKs |
| nivel_urgencia | VARCHAR (VERDE/AMARILLO/NARANJA/ROJO) |
| score | FLOAT |
| algoritmo | VARCHAR |

### recomendaciones (S-4)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id, paciente_id, prediccion_id | PK + FKs | |
| recomendacion | VARCHAR | slug: `control_prenatal_rutinario`, `seguimiento_estrecho_lc`, `progesterona_vaginal`, `tratar_infeccion`, `vigilancia_hta_multiple`, `derivacion_alto_riesgo` |
| titulo | TEXT | |
| descripcion | TEXT | |
| algoritmo | VARCHAR | `gemini` (IA) o `manual` |
| origen | VARCHAR | `gemini`, `manual` |

## Vistas

### vista_triage_priorizado
Campos: id_triage, paciente_id, nombres, apellidos, dni, nivel_urgencia, score, fecha_ultima_prediccion, prob_consenso, nivel_riesgo, mager, semanas, dplural, parto_previo, cond_cronicas, infecciones, imc, longitud_cervical, fecha_nacimiento, telefono, email
Usa `dc.embarazo_multiple`

### vista_perfil_completo
Campos: paciente_id, nombres, apellidos, dni, fecha_nacimiento, mager, id_dc, edad_gestacional_semanas, longitud_cervical, parto_prematuro_previo, embarazo_multiple, imc_pre_gestacional, cond_cronicas, infecciones, id_prediccion, prob_consenso, nivel_riesgo, semanas_estimadas, fecha_prediccion, id_triage, nivel_urgencia, score, algoritmo_triage, tiene_recomendacion

## Función

### obtener_snapshot_clinico(p_paciente_id)
Retorna: JSON con datos del paciente, datos clínicos, última predicción y último triaje
