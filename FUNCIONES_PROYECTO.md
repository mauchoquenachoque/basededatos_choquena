# Funciones del proyecto Enmask

Este documento resume **qué hace la plataforma** y **qué puede hacer cada tipo de usuario** en el estado actual del proyecto.

## Objetivo del sistema

Enmask es una plataforma para:

- Conectar bases de datos (PostgreSQL y MongoDB).
- Definir reglas de enmascaramiento de datos sensibles (PII).
- Ejecutar jobs de enmascaramiento.
- Consultar resultados y métricas.

---

## Módulos principales

### 1) Autenticación

- Registro de cuenta (`/auth/register`).
- Inicio de sesión (`/auth/login`).
- Consulta de sesión actual (`/auth/me`).

### 2) Connections

- Crear conexiones a bases de datos.
- Listar conexiones del usuario.
- Eliminar conexión.
- Descubrir PII sugerida desde una conexión (`/connections/{id}/discover`).

### 3) Masking Rules

- Crear reglas por tabla/colección y columna.
- Elegir estrategia de enmascarado (hashing, redaction, substitution, nullification, etc. según configuración).
- Listar y eliminar reglas propias.

### 4) Jobs

- Crear jobs combinando una conexión + reglas.
- Listar y consultar jobs.
- Ejecutar un job en background (`/jobs/{id}/run`).
- Compartir un job con otro usuario (`/jobs/{id}/share`).
- Consultar datos de un job (`/jobs/{id}/query`).
- Consultar auditoría del job (`/jobs/{id}/audit`).

### 5) Reports (Dashboard)

- Resumen de:
  - total de conexiones
  - total de reglas
  - total de jobs
  - total de registros procesados

---

## Roles y permisos

## Usuario (`user`)

- Puede registrarse e iniciar sesión.
- Puede crear/leer/eliminar **sus propias** conexiones, reglas y jobs.
- Puede ejecutar sus jobs.
- Puede compartir sus jobs con otros usuarios por correo.
- Puede consultar datos de jobs:
  - Si es propietario: ve datos sin enmascarar.
  - Si el job fue compartido con él: ve datos enmascarados.
- Puede ver auditoría de jobs propios.
- En reportes, ve solo su propio alcance.

## Administrador (`admin`)

- Tiene todo lo del rol `user`.
- Puede listar todos los usuarios (`/auth/users`).
- En reportes, ve agregados globales (sin filtro por propietario).
- Puede acceder a auditoría de jobs aunque no sea el owner.
- En consulta de datos de jobs (`/jobs/{id}/query`), ve datos sin enmascarar.

---

## Cómo se asigna el rol admin

Un usuario queda como `admin` al registrarse si su correo está incluido en:

- `ADMIN_EMAILS` del backend (`backend/.env`)

Si no está en esa lista, se registra como `user`.

---

## Flujo típico de uso

1. Registrarse / iniciar sesión.
2. Crear una conexión (Connections).
3. Crear reglas de enmascaramiento (Rules).
4. Crear un job con esa conexión + reglas (Jobs).
5. Ejecutar el job.
6. Revisar resultados, compartir si hace falta y consultar auditoría.
7. Ver métricas en Dashboard.

---

## Pantallas del frontend

- `Dashboard`: resumen general.
- `Connections`: gestión de conexiones.
- `Masking Rules`: gestión de reglas.
- `Jobs`: ejecución, consulta, compartir y auditoría.
- `Login`: acceso y registro.

---

## Nota importante de entorno local

Si usas `REPOSITORY_BACKEND=memory`, usuarios/jobs/reglas/conexiones se pierden al reiniciar backend.  
Para persistencia real, usa `mongodb` o `postgres` como backend de metadatos en el `.env`.