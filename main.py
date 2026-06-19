"""ObstetriCare API — FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    auth,
    citas,
    contactos,
    dashboard,
    datos_clinicos,
    intervenciones,
    pacientes,
    prediccion,
    recomendaciones,
    reportes,
    s2,
    s3,
    s4,
    triage,
    usuarios,
)
from app.core.config import settings

logging.basicConfig(level=logging.DEBUG if settings.DEBUG else logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando ObstetriCare API (entorno: %s)", settings.ENV)
    yield
    logger.info("Apagando ObstetriCare API")


app = FastAPI(
    title="ObstetriCare API",
    description="Backend para predicción de riesgo obstétrico y clasificación por urgencia",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(usuarios.router)
app.include_router(pacientes.router)
app.include_router(contactos.router)
app.include_router(citas.router)
app.include_router(datos_clinicos.router)
app.include_router(prediccion.router)
app.include_router(s2.router)
app.include_router(s3.router)
app.include_router(s4.router)
app.include_router(triage.router)
app.include_router(recomendaciones.router)
app.include_router(intervenciones.router)
app.include_router(reportes.router)


@app.get("/")
async def root():
    return {"message": "ObstetriCare API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.ENV}
