from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routers import connections, rules, jobs, reports
from app.api.routers.auth import router as auth_router
import app.core.logging

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
allow_origins = settings.cors_origins_list()
if allow_origins:
    allow_credentials = True
    if len(allow_origins) == 1 and allow_origins[0] == "*":
        allow_credentials = False

    cors_kwargs = dict(
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    origin_regex = settings.cors_origin_regex()
    if origin_regex:
        cors_kwargs["allow_origin_regex"] = origin_regex

    app.add_middleware(CORSMiddleware, **cors_kwargs)

app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(connections.router, prefix=settings.API_V1_STR)
app.include_router(rules.router, prefix=settings.API_V1_STR)
app.include_router(jobs.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)


@app.get("/health")
def health_check():
    """Comprueba que el proceso es el backend Enmask (evita confundir otro servicio en :8000)."""
    return {
        "status": "ok",
        "service": "enmask-backend",
        "api_prefix": settings.API_V1_STR,
    }


@app.get(f"{settings.API_V1_STR}/meta", tags=["meta"])
def api_meta():
    """Expuesto al front para verificar que /api/v1 corresponde a este proyecto (auth email/contraseña)."""
    return {
        "service": "enmask-backend",
        "auth": "email_password",
        "api_prefix": settings.API_V1_STR,
        "has_register": True,
    }
