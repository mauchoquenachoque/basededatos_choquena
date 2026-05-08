#!/usr/bin/env python3
"""
Script de verificación pre-despliegue para Enmask
Ejecuta: python check_deployment.py
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Verifica versión de Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Python 3.11+ requerido")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Verifica dependencias del backend"""
    try:
        import fastapi, uvicorn, pydantic, motor, asyncpg, bcrypt, email_validator
        print("✅ Dependencias del backend instaladas")
        return True
    except ImportError as e:
        print(f"❌ Falta instalar dependencias: {e}")
        return False

def check_env_file():
    """Verifica archivo .env"""
    # Buscar desde el directorio actual hacia arriba
    current = Path.cwd()
    env_path = current / ".env"
    if not env_path.exists():
        env_path = current.parent / "backend" / ".env"
    if not env_path.exists():
        print("⚠️  No existe .env - copia .env.example y configúralo")
        return False
    print("✅ Archivo .env encontrado")
    return True

def check_secret_key():
    """Verifica que SECRET_KEY no sea el valor de ejemplo."""
    env_path = Path("backend/.env")
    if not env_path.exists():
        return False

    with open(env_path, encoding="utf-8") as f:
        content = f.read()
    if "SECRET_KEY=tu_clave_secreta" in content or "SECRET_KEY=changeme" in content:
        print("⚠️  SECRET_KEY sigue siendo el valor de ejemplo (cámbialo en producción)")
        return False
    print("✅ SECRET_KEY personalizado")
    return True

def check_mongodb_uri():
    """Verifica URI de MongoDB"""
    env_path = Path("backend/.env")
    if not env_path.exists():
        return False

    with open(env_path) as f:
        content = f.read()
        if "MONGODB_META_URI=mongodb+srv://" not in content:
            print("⚠️  MONGODB_META_URI no configurado (usa Atlas)")
            return False
    print("✅ MongoDB URI configurado")
    return True

def main():
    """Función principal"""
    print("🔍 Verificando configuración de despliegue...\n")

    checks = [
        check_python_version,
        check_dependencies,
        check_env_file,
        check_secret_key,
        check_mongodb_uri,
    ]

    passed = 0
    for check in checks:
        if check():
            passed += 1
        print()

    print(f"Resultado: {passed}/{len(checks)} checks pasaron")

    if passed == len(checks):
        print("🎉 ¡Todo listo para desplegar!")
        print("\nSiguientes pasos:")
        print("1. Sube el código a GitHub")
        print("2. Despliega backend en Railway")
        print("3. Despliega frontend en Railway")
        print("4. Configura CORS con URLs reales")
    else:
        print("⚠️  Revisa las configuraciones antes de desplegar")
        sys.exit(1)

if __name__ == "__main__":
    main()