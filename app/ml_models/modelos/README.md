# Carpeta obsoleta

Esta carpeta (`app/ml_models/modelos/`) **ya no se usa** en el backend integrado.

Los artefactos ML (.pkl, .cbm) deben estar en:

**`app/ml_models/models/`**

Configuración: variable de entorno `ML_MODELS_PATH=app/ml_models/models` (ver `.env.example`).

Si tienes archivos aquí de una sesión de desarrollo con `dummy_models.py`, puedes ignorarlos o eliminarlos; el runtime carga desde `models/`.

Validar inferencia:

```bash
python scripts/validar_modelos.py
```
