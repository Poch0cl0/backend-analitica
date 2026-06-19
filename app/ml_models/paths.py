"""Rutas centralizadas para artefactos ML (.pkl, .cbm)."""

from pathlib import Path

from app.core.config import settings


def resolve_ml_models_dir() -> Path:
    """Resuelve ML_MODELS_PATH a ruta absoluta (independiente del CWD)."""
    p = Path(settings.ML_MODELS_PATH)
    if p.is_absolute():
        return p
    root = Path(__file__).resolve().parents[2]
    return root / p
