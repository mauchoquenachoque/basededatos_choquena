import sys
sys.path.insert(0, ".")

from app.core.config import settings

print("=== VALORES ACTUALES DE SETTINGS ===")
print(f"REPOSITORY_BACKEND = '{settings.REPOSITORY_BACKEND}'")
print(f"Es igual a 'mongodb': {settings.REPOSITORY_BACKEND == 'mongodb'}")
print(f"MONGODB_META_URI    = '{settings.MONGODB_META_URI}'")
print(f"METADATA_DATABASE   = '{settings.METADATA_DATABASE}'")
