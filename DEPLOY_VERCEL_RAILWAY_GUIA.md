# Guia simple: Vercel + Railway (recomendada)

Si eres nuevo, este es el camino mas facil y estable:

- **Frontend (React/Vite)** en **Vercel**
- **Backend (FastAPI)** en **Railway**

---

## Arquitectura final

- Frontend: `https://tu-app.vercel.app`
- Backend: `https://tu-backend.up.railway.app`
- El frontend llama al backend usando `VITE_API_URL`.

---

## 1) Subir proyecto a GitHub

Desde la raiz del repo:

```bash
git add .
git commit -m "prepare deployment files for Vercel and Railway"
git push
```

---

## 2) Desplegar backend en Railway

1. Entra a [Railway](https://railway.app/) y crea proyecto nuevo.
2. Elige **Deploy from GitHub repo**.
3. Selecciona el repo y como raiz del servicio usa carpeta `backend` (si te la pide).
4. En variables de entorno de Railway agrega:

```env
API_V1_STR=/api/v1
PROJECT_NAME=Enmask SDM Platform
SECRET_KEY=pon_una_clave_larga_y_segura
ADMIN_EMAILS=tu_correo_admin@dominio.com
REPOSITORY_BACKEND=mongodb
MONGODB_META_URI=<tu_uri_mongodb>
METADATA_DATABASE=enmask_meta
API_KEY=
BACKEND_CORS_ORIGINS=https://tu-app.vercel.app
```

1. Railway detectara el `Procfile` y correra uvicorn con `PORT` dinamico.
2. Cuando termine, copia la URL publica del backend (ejemplo: `https://mi-api.up.railway.app`).

Prueba salud:

- `https://mi-api.up.railway.app/health`
- `https://mi-api.up.railway.app/docs`

---

## 3) Desplegar frontend en Vercel

1. Entra a [Vercel](https://vercel.com/), importa el mismo repo.
2. En **Root Directory** selecciona `frontend`.
3. En variables de entorno agrega:

```env
VITE_API_URL=https://mi-api.up.railway.app/api/v1
```

1. Deploy.

El archivo `frontend/vercel.json` ya esta listo para que rutas SPA (`/jobs`, `/rules`, etc.) no den 404.

---

## 4) Ajustar CORS al dominio final

Cuando tengas la URL final de Vercel, vuelve a Railway y deja:

```env
BACKEND_CORS_ORIGINS=https://tu-app.vercel.app
```

Si tienes dominio personalizado:

```env
BACKEND_CORS_ORIGINS=https://app.tudominio.com,https://tu-app.vercel.app
```

Haz redeploy del backend despues de este cambio.

---

## 5) Checklist de errores comunes

### Error: `Failed to fetch`

- Backend caido o URL de `VITE_API_URL` incorrecta.
- CORS sin dominio de Vercel.
- Solucion: revisar `VITE_API_URL`, `BACKEND_CORS_ORIGINS` y `/health`.

### Error: 401/Not authenticated

- Token vencido o no guardado.
- Solucion: cerrar sesion y entrar de nuevo.

### Registro/Login no persiste

- `REPOSITORY_BACKEND=memory`.
- Solucion: usar `mongodb` o `postgres` en Railway.

### Vercel abre home pero `/jobs` falla al refrescar

- Falta rewrite SPA.
- Solucion: ya incluido en `frontend/vercel.json`.

---

## 6) Opcion aun mas simple (si no quieres dividir)

Puedes desplegar **todo en Render** (frontend + backend + DB), pero normalmente:

- Vercel es mas comodo para frontend
- Railway/Render es mas comodo para backend Python

Por eso Vercel + Railway suele ser el mejor equilibrio para empezar.