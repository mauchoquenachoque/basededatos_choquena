from enum import Enum


class DatabaseType(str, Enum):
    POSTGRES = "postgres"
    MONGODB = "mongodb"
    MYSQL = "mysql"
