# Setup — Instalación y Configuración

## Prerrequisitos

- Python 3.12+
- Node.js 20+
- PostgreSQL 16
- Redis (opcional, para caché)
- Git

## Backend

### 1. Clonar repositorio
```bash
git clone <repo-url>
cd SOFTWARE/backend-analitica
```

### 2. Entorno virtual
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Variables de entorno
```bash
cp .env.example .env
# Editar .env con:
#   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/sat_prematuro
#   SECRET_KEY=tu_secreto_jwt
#   GEMINI_APIKEY=tu_api_key_gemini
#   REDIS_URL=redis://localhost:6379/0
```

### 5. Base de datos
```bash
# Crear la BD:
createdb sat_prematuro

# Ejecutar migraciones:
alembic upgrade head
```

### 6. Semillas
```bash
python -m app.seed.seeds
```

### 7. Iniciar servidor
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend

### 1. Instalar dependencias
```bash
cd SOFTWARE/frontend-analitica
npm install
```

### 2. Variables de entorno
```bash
cp .env.example .env
# Editar con:
#   VITE_API_URL=http://localhost:8000/api
```

### 3. Iniciar dev server
```bash
npm run dev
```

## Gemini API Key

1. Obtener API key en https://aistudio.google.com/apikey
2. Agregar al `.env` del backend:
```
GEMINI_APIKEY=AIzaSy...
```
3. Modelo usado: `gemini-2.0-flash` (gratuito con cuota de 1500 req/día)
4. Sin API key, el sistema usa fallback rule-based (no requiere modelos ML)

## Verificar Instalación

1. Backend: `http://localhost:8000/docs` (Swagger UI)
2. Frontend: `http://localhost:5173`
3. Usuario por defecto (seed): admin@clinica.com / admin123

## Scripts Útiles

```bash
# Backend - Tests
pytest

# Backend - Nueva migración
alembic revision --autogenerate -m "descripcion"

# Backend - Aplicar migración
alembic upgrade head

# Backend - Formato y lint
ruff check . --fix
ruff format .
```

## Estructura de `.env`

### Backend (backend-analitica/.env)
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/sat_prematuro
SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e77
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
GEMINI_APIKEY=AIzaSy...
REDIS_URL=redis://localhost:6379/0
MAIL_USERNAME=tu_correo@gmail.com
MAIL_PASSWORD=tu_contraseña_app
MAIL_FROM=tu_correo@gmail.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
```

### Frontend (frontend-analitica/.env)
```
VITE_API_URL=http://localhost:8000/api
```
