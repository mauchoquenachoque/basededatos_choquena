import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def test_connection():
    uri = "mongodb+srv://ef2023076793_db_user:primo2000@cluster0.udu6dxr.mongodb.net/?appName=Cluster0"
    print(f"Probando conexión con URI: {uri}")
    
    try:
        client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
        # Intentar hacer un ping a la base de datos para forzar la autenticación
        result = await client.admin.command('ping')
        print("¡Conexión exitosa a MongoDB Atlas!", result)
    except Exception as e:
        print("Error de conexión:", type(e).__name__)
        print("Detalle:", e)

if __name__ == "__main__":
    asyncio.run(test_connection())
