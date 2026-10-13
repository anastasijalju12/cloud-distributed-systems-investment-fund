import os

mongo_user = os.environ.get("MONGO_USER", "root")
mongo_password = os.environ.get("MONGO_PASSWORD", "example")
mongo_host = os.environ.get("MONGO_HOST", "localhost")
mongo_port = int(os.environ.get("MONGO_PORT", "27017"))
mongo_database_name = os.environ.get("MONGO_DATABASE", "investment_fund")

redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_port = int(os.environ.get("REDIS_PORT", "6379"))

ethereum_url = os.environ.get("ETHEREUM_URL", "http://localhost:8545")

class Configuration:
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "JWT_SECRET_DEV_KEY") # 1. arg is name of env. var.; 2. is default


"""
selling_price i selling_date postoje samo ako je imovina prodata.
MONGO:
{
    "_id": ObjectId("66688f0f4b6f2d6a2f7c9a11"),
    "name": "AssetAlpha",
    "categories": ["Technology", "Finance"],
    "buying_price": 50000,
    "selling_price": 75000,
    "buying_date": "2026-01-01",
    "selling_date": "2026-06-01",
    "info": {"region": "EU"}
}
"""