import os
from datetime import timedelta
# just sql base
# ime, prezime, mejl, lozinka, uloga korisnika;
# id	forename	surname	email	password	role
# 1	Scrooge	McDuck	onlymoney@gmail.com	...	director
database_url = os.environ.get("DATABASE_URL", "localhost:3307") #3307 - port which is used by docker to connect MySql messages on my laptop with container port;
#lokalno se pokrece sa default, a kada radi Kubernetes deployment iz configMap ubacuje DATABASE_URL=fund-db-service:3306
database_name     = os.environ.get("DATABASE_NAME", "fund")
database_user     = os.environ.get("DATABASE_USER", "root")
database_password = os.environ.get("DATABASE_PASSWORD", "root")


class Configuration:
    SQLALCHEMY_DATABASE_URI  = f"mysql+pymysql://{database_user}:{database_password}@{database_url}/{database_name}"
    JWT_SECRET_KEY           = os.environ.get("JWT_SECRET_KEY", "JWT_SECRET_DEV_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

"""
users tabela u SQL:
id       | int, primary key, auto increment
forename | varchar(256)
surname  | varchar(256)
email    | varchar(256), unique
password | varchar(256)
role     | varchar(256) - "employee" ili "director"
"""