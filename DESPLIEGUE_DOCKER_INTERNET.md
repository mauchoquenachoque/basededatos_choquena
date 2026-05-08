# Despliegue a internet con Docker (guía práctica)

Esta guía te deja el proyecto publicado en internet usando:
- Un VPS (Ubuntu recomendado)
- Docker + Docker Compose
- Nginx como reverse proxy
- HTTPS con Let's Encrypt

## 1) Requisitos

- Tener un dominio (ejemplo: `enmask.tudominio.com`)
- VPS con IP pública (DigitalOcean, Hetzner, Contabo, etc.)
- DNS del dominio apuntando a la IP del VPS

---

## 2) Preparar el servidor

En el VPS:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y ca-certificates curl git nginx certbot python3-certbot-nginx
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
docker --version
docker compose version
```

---

## 3) Subir el proyecto al VPS

```bash
git clone <TU_REPO_URL> enmask
cd enmask
```

---

## 4) Configurar variables para producción (muy importante)

En backend, usa valores reales (no de local):

Archivo: `backend/.env`

- `SECRET_KEY` -> una clave larga y aleatoria.
- `ADMIN_EMAILS` -> tu correo admin real.
- `BACKEND_CORS_ORIGINS` -> tu dominio frontend (ejemplo: `https://enmask.tudominio.com`).
- `REPOSITORY_BACKEND` -> `mongodb` o `postgres` (no `memory` en producción).
- `API_KEY` -> opcional, pero si la usas debe ser fuerte.

Ejemplo:

```env
API_V1_STR=/api/v1
PROJECT_NAME=Enmask SDM Platform
BACKEND_CORS_ORIGINS=https://enmask.tudominio.com
SECRET_KEY=pon_una_clave_larga_y_segura
ADMIN_EMAILS=tu_correo@dominio.com
REPOSITORY_BACKEND=mongodb
MONGODB_META_URI=mongodb://mongodb:27017
METADATA_DATABASE=enmask_meta
API_KEY=
```

---

## 5) Levantar contenedores

Desde la raíz del proyecto:

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f backend
```

Prueba backend:

```bash
curl http://127.0.0.1:8000/health
```

---

## 6) Publicar con Nginx

Crea configuración Nginx:

```bash
sudo nano /etc/nginx/sites-available/enmask
```

Contenido base:

```nginx
server {
    listen 80;
    server_name enmask.tudominio.com;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:5173/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Activar sitio:

```bash
sudo ln -s /etc/nginx/sites-available/enmask /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 7) Activar HTTPS

```bash
sudo certbot --nginx -d enmask.tudominio.com
sudo certbot renew --dry-run
```

Listo: ya debería abrir por `https://enmask.tudominio.com`.

---

## 8) Comandos de operación diaria

```bash
docker compose pull
docker compose up -d --build
docker compose logs -f backend
docker compose logs -f frontend
docker compose restart backend
docker compose down
```

---

## 9) Recomendaciones para dejarlo "más pro"

Estado actual del repo:
- El frontend Dockerfile corre `npm run dev` (servidor de desarrollo).

Para producción real, conviene:
- Compilar frontend (`npm run build`)
- Servir estáticos con Nginx (contenedor o host)
- Exponer solo Nginx al público
- Backend y DB en red interna Docker

Si quieres, te ayudo a dejar esto listo en el código:
- `frontend/Dockerfile` de producción (multi-stage)
- `docker-compose.prod.yml`
- Nginx container para servir frontend + proxy a backend

