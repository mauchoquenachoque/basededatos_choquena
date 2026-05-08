# Enmask — Static Data Masking Platform

Plataforma de enmascaramiento estático de datos para **PostgreSQL** y **MongoDB**, con API en FastAPI y panel en React.

**Enfoque actual:** ejecutar y probar todo en **localhost**. Las opciones de despliegue (Railway, Docker, etc.) están al final, como referencia cuando las necesites.

---

## Ejecutar en localhost

### Requisitos

| Herramienta | Versión recomendada |
|-------------|---------------------|
| Python      | 3.12+               |
| Node.js     | 20+                 |
| npm         | 9+                  |

PostgreSQL o MongoDB en tu máquina solo hacen falta cuando quieras **lanzar jobs reales** contra una base; el propio API puede usar metadatos en memoria (`REPOSITORY_BACKEND=memory`).

### Opción rápida (Windows)

Desde la **raíz del repo**:

```powershell
.\scripts\start-local.cmd
```

Si prefieres el `.ps1` y PowerShell te dice que la ejecución de scripts está deshabilitada, usa una sola vez:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-local.ps1
```

(Opcional y permanente solo para tu usuario: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.)

Se abren dos ventanas: API en el puerto **8000** y Vite en **5173**. Luego abre **http://localhost:5173**, regístrate e inicia sesión.

### Backend (manual)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Edita .env si hace falta (SECRET_KEY, CORS, etc.)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: **http://localhost:8000/api/v1**
- Documentación interactiva: **http://localhost:8000/docs**
- Comprobación rápida: **http://localhost:8000/health** (debe incluir `"service": "enmask-backend"`)

### Frontend (manual)

En otra terminal:

```powershell
cd frontend
npm install
npm run dev
```

- Interfaz: **http://localhost:5173**

En modo desarrollo, el cliente usa por defecto **http://127.0.0.1:8000/api/v1** (CORS). Si el backend está en otro puerto, define `VITE_API_URL` en `frontend/.env.local` (ver `frontend/.env.example`).

---

## Uso en local

1. **Connections** — Alta de credenciales PostgreSQL o MongoDB (ej. `localhost`, puerto, base, usuario).
2. **Masking Rules** — Tabla/colección, columna y estrategia (hashing, substitution, redaction, nullification).
3. **Jobs** — Enlaza conexión + reglas y ejecuta el job.

**PostgreSQL de ejemplo:**

```
Tipo:      postgres
Host:      localhost
Puerto:    5432
Base:      mydb
Usuario:   postgres
Contraseña: (la tuya)
```

---

## Ejemplo SQL (opcional)

```sql
CREATE DATABASE masking_demo;
\c masking_demo
CREATE TABLE users (
    id       SERIAL PRIMARY KEY,
    name     TEXT NOT NULL,
    email    TEXT NOT NULL,
    phone    TEXT,
    address  TEXT
);
INSERT INTO users (name, email, phone, address) VALUES
  ('Alice Smith', 'alice@example.com', '+1-555-0100', '123 Maple St');
```

Crea reglas sobre la tabla `users` y columnas que quieras enmascarar.

---

## Ejemplo MongoDB (opcional)

```javascript
use masking_demo
db.customers.insertMany([
  { name: "Alice Smith", email: "alice@example.com", phone: "+1-555-0100" },
])
```

---

## Estructura del repo

```
EnmascaradoDatos/
├── backend/          # FastAPI, uvicorn app.main:app
├── frontend/         # React + Vite
├── scripts/          # start-local.ps1 (Windows)
└── docker-compose.yml  # solo si más adelante quieres contenedores
```

---

## Referencia API (resumen)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/meta` | Identidad del servicio (localhost / diagnóstico) |
| POST | `/api/v1/auth/register` | Registro |
| POST | `/api/v1/auth/login` | Login |
| GET/POST | `/api/v1/connections/` | Conexiones |
| GET/POST | `/api/v1/rules/` | Reglas |
| GET/POST | `/api/v1/jobs/` | Jobs |
| POST | `/api/v1/jobs/{id}/run` | Ejecutar job |

Detalle completo en **http://localhost:8000/docs** con el backend en marcha.

---

## Notas

- Con **`REPOSITORY_BACKEND=memory`**, usuarios, conexiones y reglas se pierden al **reiniciar** el proceso del backend. Para persistencia en local puedes configurar Postgres/Mongo en `backend/.env`.
- Los jobs **modifican datos** en la base objetivo; prueba primero sobre copias o entornos de prueba.
- La estrategia **hashing** es determinista (misma entrada + sal → mismo valor), útil para integridad referencial.

---

## Más adelante: despliegue (opcional)

Cuando quieras publicar el proyecto en la nube o usar contenedores, revisa **`backend/.env.example`** (variables de producción, CORS, `SECRET_KEY`, metadata en Mongo/Postgres). En el repo hay **`docker-compose.yml`** para levantar Postgres, Mongo, backend y frontend juntos; no es necesario para desarrollar en localhost.

Pasos tipo Railway u otros hosts puedes documentarlos en tu propio checklist de despliegue cuando toque; el flujo diario de este README es **solo local**.
