"""
Seeder de datos iniciales — ObstetriCare
Uso: python seeds.py
"""

import asyncio
from datetime import date, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password


# ─────────────────────────────────────────────
# DATOS SEMILLA
# ─────────────────────────────────────────────

ROLES = [
    {"id": 1, "nombre": "admin",      "descripcion": "Administrador del sistema"},
    {"id": 2, "nombre": "medico",     "descripcion": "Médico obstetra"},
    {"id": 3, "nombre": "secretaria", "descripcion": "Secretaria / recepción"},
]

PERMISOS = [
    # admin
    (1, "usuarios",       "leer"),       (1, "usuarios",       "crear"),
    (1, "usuarios",       "actualizar"), (1, "usuarios",       "eliminar"),
    (1, "pacientes",      "leer"),       (1, "pacientes",      "crear"),
    (1, "pacientes",      "actualizar"), (1, "pacientes",      "eliminar"),
    (1, "citas",          "leer"),       (1, "citas",          "crear"),
    (1, "citas",          "actualizar"), (1, "citas",          "eliminar"),
    (1, "datos_clinicos", "leer"),       (1, "datos_clinicos", "crear"),
    (1, "datos_clinicos", "actualizar"),
    (1, "prediccion",     "ejecutar"),
    (1, "triage",         "leer"),       (1, "triage",         "ejecutar"),
    (1, "recomendacion",  "leer"),       (1, "recomendacion",  "ejecutar"),
    (1, "reportes",       "exportar"),
    # medico
    (2, "pacientes",      "leer"),
    (2, "citas",          "leer"),       (2, "citas",          "actualizar"),
    (2, "datos_clinicos", "leer"),       (2, "datos_clinicos", "crear"),
    (2, "datos_clinicos", "actualizar"),
    (2, "prediccion",     "ejecutar"),
    (2, "triage",         "leer"),       (2, "triage",         "ejecutar"),
    (2, "recomendacion",  "leer"),       (2, "recomendacion",  "ejecutar"),
    (2, "reportes",       "exportar"),
    # secretaria
    (3, "pacientes",      "leer"),       (3, "pacientes",      "crear"),
    (3, "pacientes",      "actualizar"), (3, "pacientes",      "eliminar"),
    (3, "citas",          "leer"),       (3, "citas",          "crear"),
    (3, "citas",          "actualizar"), (3, "citas",          "eliminar"),
]

USUARIOS = [
    {
        "email":    "admin@obstetricare.com",
        "password": "Admin123!",
        "nombre":   "Administrador",
        "apellidos":"Sistema",
        "rol_id":   1,
        "activo":   True,
    },
    {
        "email":    "dr.garcia@obstetricare.com",
        "password": "Medico123!",
        "nombre":   "Carlos",
        "apellidos":"García Mendoza",
        "rol_id":   2,
        "activo":   True,
    },
    {
        "email":    "dra.lopez@obstetricare.com",
        "password": "Medico123!",
        "nombre":   "Ana",
        "apellidos":"López Torres",
        "rol_id":   2,
        "activo":   True,
    },
    {
        "email":    "secretaria@obstetricare.com",
        "password": "Secretaria123!",
        "nombre":   "María",
        "apellidos":"Pérez Ruiz",
        "rol_id":   3,
        "activo":   True,
    },
]

CATALOGO_INTERVENCIONES = [
    {"codigo": "INT-001", "nombre": "Progesterona vaginal",                          "categoria": "farmacologica"},
    {"codigo": "INT-002", "nombre": "Cerclaje cervical",                              "categoria": "quirurgica"},
    {"codigo": "INT-003", "nombre": "Control prenatal intensivo",                     "categoria": "seguimiento"},
    {"codigo": "INT-004", "nombre": "Reposo relativo",                                "categoria": "conducta"},
    {"codigo": "INT-005", "nombre": "Corticoides para maduración pulmonar",           "categoria": "farmacologica"},
    {"codigo": "INT-006", "nombre": "Tocolisis",                                      "categoria": "farmacologica"},
    {"codigo": "INT-007", "nombre": "Hospitalización preventiva",                     "categoria": "seguimiento"},
    {"codigo": "INT-008", "nombre": "Control de tensión arterial",                    "categoria": "farmacologica"},
    {"codigo": "INT-009", "nombre": "Evaluación por endocrinología",                  "categoria": "interconsulta"},
    {"codigo": "INT-010", "nombre": "Tamizaje de infecciones de transmisión sexual",  "categoria": "laboratorio"},
]

CATALOGO_INTERVENCIONES_S4 = [
    {"codigo": "control_prenatal_rutinario", "nombre": "Control prenatal rutinario",           "categoria": "seguimiento"},
    {"codigo": "seguimiento_estrecho_lc",    "nombre": "Seguimiento estrecho por LC corta",    "categoria": "seguimiento"},
    {"codigo": "progesterona_vaginal",       "nombre": "Progesterona vaginal",                 "categoria": "farmacologica"},
    {"codigo": "tratar_infeccion",           "nombre": "Tratar infección activa",              "categoria": "farmacologica"},
    {"codigo": "vigilancia_hta_multiple",    "nombre": "Vigilancia HTA / embarazo múltiple",   "categoria": "seguimiento"},
    {"codigo": "derivacion_alto_riesgo",     "nombre": "Derivación a alto riesgo",             "categoria": "interconsulta"},
]

PARAMETROS_SISTEMA = [
    {"clave": "umbral_rojo",           "valor": "0.70", "descripcion": "Umbral score S-3 para nivel ROJO"},
    {"clave": "umbral_naranja",        "valor": "0.45", "descripcion": "Umbral score S-3 para nivel NARANJA"},
    {"clave": "umbral_amarillo",       "valor": "0.22", "descripcion": "Umbral score S-3 para nivel AMARILLO"},
    {"clave": "lc_corto_mm",           "valor": "25.0", "descripcion": "Longitud cervical corta en mm (SOGC 467)"},
    {"clave": "lc_moderado_mm",        "valor": "30.0", "descripcion": "Longitud cervical moderada en mm"},
    {"clave": "bmi_bajo",              "valor": "18.5", "descripcion": "BMI bajo (riesgo)"},
    {"clave": "bmi_alto",              "valor": "30.0", "descripcion": "BMI alto (riesgo)"},
    {"clave": "peso_prob_prematuro",   "valor": "0.35", "descripcion": "Peso puntaje S-3: probabilidad prematuro"},
    {"clave": "peso_parto_previo",     "valor": "0.20", "descripcion": "Peso puntaje S-3: parto prematuro previo"},
    {"clave": "peso_embarazo_mult",    "valor": "0.15", "descripcion": "Peso puntaje S-3: embarazo múltiple"},
    {"clave": "peso_hta_gestacional",  "valor": "0.12", "descripcion": "Peso puntaje S-3: hipertensión gestacional"},
    {"clave": "peso_lc_corto",         "valor": "0.13", "descripcion": "Peso puntaje S-3: longitud cervical corta"},
    {"clave": "peso_bmi_riesgo",       "valor": "0.05", "descripcion": "Peso puntaje S-3: BMI en rango de riesgo"},
    {"clave": "duracion_cita_minutos", "valor": "30",   "descripcion": "Duración por defecto de una cita en minutos"},
    {"clave": "version_modelos_ml",    "valor": "1.0",  "descripcion": "Versión de los modelos ML cargados"},
]

PACIENTES = [
    {
        "dni": "12345678", "nombre": "Laura", "apellidos": "Sánchez Vega",
        "fecha_nacimiento": date(1995, 3, 14),
        "telefono_principal": "999-111-001", "email": "laura.sanchez@email.com",
    },
    {
        "dni": "23456789", "nombre": "Sofía", "apellidos": "Ramírez Castro",
        "fecha_nacimiento": date(1998, 7, 22),
        "telefono_principal": "999-111-002", "email": "sofia.ramirez@email.com",
    },
    {
        "dni": "34567890", "nombre": "Valentina", "apellidos": "Torres Mora",
        "fecha_nacimiento": date(1990, 11, 5),
        "telefono_principal": "999-111-003", "email": "valentina.torres@email.com",
    },
    {
        "dni": "45678901", "nombre": "Isabella", "apellidos": "Flores Díaz",
        "fecha_nacimiento": date(2000, 1, 30),
        "telefono_principal": "999-111-004", "email": "isabella.flores@email.com",
    },
]

DATOS_CLINICOS = [
    {
        "edad_gestacional_semanas": 32,  "longitud_cervical_mm": 22.5,
        "embarazo_multiple": 2,           "parto_prematuro_previo": True,
        "hipertension_gestacional": False, "bmi": 24.1, "bmi_categoria": "normal",
        "num_condiciones_cronicas": 1,   "infeccion_activa": False,
    },
    {
        "edad_gestacional_semanas": 28,  "longitud_cervical_mm": 18.0,
        "embarazo_multiple": 2,           "parto_prematuro_previo": False,
        "hipertension_gestacional": True, "bmi": 31.5, "bmi_categoria": "obesidad_I",
        "num_condiciones_cronicas": 2,   "infeccion_activa": True,
    },
    {
        "edad_gestacional_semanas": 37,  "longitud_cervical_mm": 35.0,
        "embarazo_multiple": 1,           "parto_prematuro_previo": False,
        "hipertension_gestacional": False, "bmi": 22.0, "bmi_categoria": "normal",
        "num_condiciones_cronicas": 0,   "infeccion_activa": False,
    },
    {
        "edad_gestacional_semanas": 24,  "longitud_cervical_mm": 15.5,
        "embarazo_multiple": 3,           "parto_prematuro_previo": True,
        "hipertension_gestacional": True, "bmi": 35.2, "bmi_categoria": "obesidad_II",
        "num_condiciones_cronicas": 3,   "infeccion_activa": True,
    },
]


# ─────────────────────────────────────────────
# FUNCIONES DE INSERCIÓN
# ─────────────────────────────────────────────

async def seed_roles(db: AsyncSession) -> None:
    count = (await db.execute(text("SELECT COUNT(*) FROM roles"))).scalar()
    if count > 0:
        print("  [SKIP] roles — ya existen datos")
        return
    for r in ROLES:
        await db.execute(
            text("INSERT INTO roles (id, nombre, descripcion) VALUES (:id, :nombre, :descripcion)"),
            r,
        )
    await db.execute(text("SELECT setval('roles_id_seq', (SELECT MAX(id) FROM roles))"))
    print(f"  [OK]   roles — {len(ROLES)} insertados")


async def seed_permisos(db: AsyncSession) -> None:
    count = (await db.execute(text("SELECT COUNT(*) FROM permisos"))).scalar()
    if count == 0:
        for rol_id, modulo, accion in PERMISOS:
            await db.execute(
                text("INSERT INTO permisos (rol_id, modulo, accion) VALUES (:r, :m, :a)"),
                {"r": rol_id, "m": modulo, "a": accion},
            )
        print(f"  [OK]   permisos — {len(PERMISOS)} insertados")
    else:
        print("  [SKIP] permisos base — ya existen datos")
        await seed_permisos_recomendacion(db)


async def seed_permisos_recomendacion(db: AsyncSession) -> None:
    nuevos = [
        (1, "recomendacion", "leer"), (1, "recomendacion", "ejecutar"),
        (2, "recomendacion", "leer"), (2, "recomendacion", "ejecutar"),
    ]
    insertados = 0
    for rol_id, modulo, accion in nuevos:
        result = await db.execute(
            text("""
                INSERT INTO permisos (rol_id, modulo, accion)
                VALUES (:r, :m, :a)
                ON CONFLICT (rol_id, modulo, accion) DO NOTHING
            """),
            {"r": rol_id, "m": modulo, "a": accion},
        )
        if result.rowcount:
            insertados += 1
    if insertados:
        print(f"  [OK]   permisos recomendacion — {insertados} insertados")
    else:
        print("  [SKIP] permisos recomendacion — ya existen")


async def seed_usuarios(db: AsyncSession) -> list[int]:
    count = (await db.execute(text("SELECT COUNT(*) FROM usuarios"))).scalar()
    if count > 0:
        print("  [SKIP] usuarios — ya existen datos")
        rows = await db.execute(text("SELECT id FROM usuarios ORDER BY id"))
        return [r[0] for r in rows.fetchall()]
    ids: list[int] = []
    for u in USUARIOS:
        datos = {**u, "password_hash": hash_password(u["password"])}
        datos.pop("password")
        result = await db.execute(
            text("""
                INSERT INTO usuarios (email, password_hash, nombre, apellidos, rol_id, activo)
                VALUES (:email, :password_hash, :nombre, :apellidos, :rol_id, :activo)
                RETURNING id
            """),
            datos,
        )
        ids.append(result.scalar())
    print(f"  [OK]   usuarios — {len(USUARIOS)} insertados  ids={ids}")
    return ids


async def seed_catalogo(db: AsyncSession) -> None:
    count = (await db.execute(text("SELECT COUNT(*) FROM catalogo_intervenciones"))).scalar()
    if count == 0:
        for item in CATALOGO_INTERVENCIONES:
            await db.execute(
                text("""
                    INSERT INTO catalogo_intervenciones (codigo, nombre, categoria)
                    VALUES (:codigo, :nombre, :categoria)
                """),
                item,
            )
        print(f"  [OK]   catalogo_intervenciones — {len(CATALOGO_INTERVENCIONES)} insertados")
    else:
        print("  [SKIP] catalogo_intervenciones — ya existen datos base")
    await seed_catalogo_s4(db)


async def seed_catalogo_s4(db: AsyncSession) -> None:
    insertados = 0
    for item in CATALOGO_INTERVENCIONES_S4:
        result = await db.execute(
            text("""
                INSERT INTO catalogo_intervenciones (codigo, nombre, categoria)
                VALUES (:codigo, :nombre, :categoria)
                ON CONFLICT (codigo) DO NOTHING
            """),
            item,
        )
        if result.rowcount:
            insertados += 1
    if insertados:
        print(f"  [OK]   catalogo_intervenciones S-4 — {insertados} insertados")
    else:
        print("  [SKIP] catalogo_intervenciones S-4 — ya existen")


async def seed_parametros(db: AsyncSession) -> None:
    count = (await db.execute(text("SELECT COUNT(*) FROM parametros_sistema"))).scalar()
    if count > 0:
        print("  [SKIP] parametros_sistema — ya existen datos")
        return
    for p in PARAMETROS_SISTEMA:
        await db.execute(
            text("""
                INSERT INTO parametros_sistema (clave, valor, descripcion)
                VALUES (:clave, :valor, :descripcion)
            """),
            p,
        )
    print(f"  [OK]   parametros_sistema — {len(PARAMETROS_SISTEMA)} insertados")


async def seed_pacientes(db: AsyncSession, usuario_ids: list[int]) -> list[int]:
    count = (await db.execute(text("SELECT COUNT(*) FROM pacientes"))).scalar()
    if count > 0:
        print("  [SKIP] pacientes — ya existen datos")
        rows = await db.execute(text("SELECT id FROM pacientes ORDER BY id"))
        return [r[0] for r in rows.fetchall()]
    # usuario_ids[1]=dr. García, usuario_ids[2]=dra. López
    medicos = [usuario_ids[1], usuario_ids[1], usuario_ids[2], usuario_ids[2]]
    ids: list[int] = []
    for i, p in enumerate(PACIENTES):
        result = await db.execute(
            text("""
                INSERT INTO pacientes
                    (dni, nombre, apellidos, fecha_nacimiento,
                     telefono_principal, email, medico_asignado_id)
                VALUES
                    (:dni, :nombre, :apellidos, :fecha_nacimiento,
                     :telefono_principal, :email, :medico_asignado_id)
                RETURNING id
            """),
            {
                **p,
                "medico_asignado_id": medicos[i],
            },
        )
        ids.append(result.scalar())
    print(f"  [OK]   pacientes — {len(PACIENTES)} insertados  ids={ids}")
    return ids


async def seed_datos_clinicos(db: AsyncSession, paciente_ids: list[int]) -> None:
    count = (await db.execute(text("SELECT COUNT(*) FROM datos_clinicos"))).scalar()
    if count > 0:
        print("  [SKIP] datos_clinicos — ya existen datos")
        return
    for paciente_id, dc in zip(paciente_ids, DATOS_CLINICOS):
        await db.execute(
            text("""
                INSERT INTO datos_clinicos (
                    paciente_id, edad_gestacional_semanas, longitud_cervical_mm,
                    embarazo_multiple, parto_prematuro_previo, hipertension_gestacional,
                    bmi, bmi_categoria, num_condiciones_cronicas, infeccion_activa
                ) VALUES (
                    :paciente_id, :edad_gestacional_semanas, :longitud_cervical_mm,
                    :embarazo_multiple, :parto_prematuro_previo, :hipertension_gestacional,
                    :bmi, :bmi_categoria, :num_condiciones_cronicas, :infeccion_activa
                )
            """),
            {"paciente_id": paciente_id, **dc},
        )
    print(f"  [OK]   datos_clinicos — {len(DATOS_CLINICOS)} insertados")


async def seed_citas(db: AsyncSession, paciente_ids: list[int], usuario_ids: list[int]) -> None:
    count = (await db.execute(text("SELECT COUNT(*) FROM citas"))).scalar()
    if count > 0:
        print("  [SKIP] citas — ya existen datos")
        return
    hoy = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    citas = [
        {
            "paciente_id": paciente_ids[0], "medico_id": usuario_ids[1],
            "fecha_hora":  hoy + timedelta(days=1),
            "estado": "programada",
        },
        {
            "paciente_id": paciente_ids[1], "medico_id": usuario_ids[1],
            "fecha_hora":  hoy + timedelta(days=1, hours=1),
            "estado": "programada",
        },
        {
            "paciente_id": paciente_ids[2], "medico_id": usuario_ids[2],
            "fecha_hora":  hoy,
            "estado": "cumplida",
        },
        {
            "paciente_id": paciente_ids[3], "medico_id": usuario_ids[2],
            "fecha_hora":  hoy + timedelta(days=2),
            "estado": "programada",
        },
    ]
    for c in citas:
        await db.execute(
            text("""
                INSERT INTO citas (paciente_id, medico_id, fecha_hora, estado)
                VALUES (:paciente_id, :medico_id, :fecha_hora, :estado)
            """),
            c,
        )
    print(f"  [OK]   citas — {len(citas)} insertadas")


# ─────────────────────────────────────────────
# RUNNER PRINCIPAL
# ─────────────────────────────────────────────

async def run_seeds() -> None:
    print("\n=== ObstetriCare Seeder ===\n")
    async with AsyncSessionLocal() as db:
        try:
            await seed_roles(db)
            await seed_permisos(db)
            usuario_ids = await seed_usuarios(db)
            await seed_catalogo(db)
            await seed_parametros(db)
            paciente_ids = await seed_pacientes(db, usuario_ids)
            await seed_datos_clinicos(db, paciente_ids)
            await seed_citas(db, paciente_ids, usuario_ids)
            await db.commit()
            print("\n[OK] Seeder completado exitosamente\n")
        except Exception as exc:
            await db.rollback()
            print(f"\n[ERROR] Seeder fallido: {exc}\n")
            raise


if __name__ == "__main__":
    asyncio.run(run_seeds())
