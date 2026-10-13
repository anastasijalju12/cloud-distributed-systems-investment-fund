import os

mongo_user = os.environ.get("MONGO_USER", "root")
mongo_password = os.environ.get("MONGO_PASSWORD", "example")
mongo_host = os.environ.get("MONGO_HOST", "localhost")
mongo_port = int(os.environ.get("MONGO_PORT", "27017"))
mongo_database_name = os.environ.get("MONGO_DATABASE", "investment_fund")

redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_port = int(os.environ.get("REDIS_PORT", "6379"))

class Configuration:
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "JWT_SECRET_DEV_KEY") # 1. arg is name of env. var.; 2. is default