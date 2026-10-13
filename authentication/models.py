from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()

ROLE_EMPLOYEE = "employee"
ROLE_DIRECTOR = "director"


class User(database.Model):
    __tablename__ = "users"

    id       = database.Column(database.Integer, primary_key=True)
    forename = database.Column(database.String(256), nullable=False)
    surname  = database.Column(database.String(256), nullable=False)
    email    = database.Column(database.String(256), nullable=False, unique=True)
    password = database.Column(database.String(256), nullable=False)
    role     = database.Column(database.String(256), nullable=False)

    def __repr__(self):
        return (
            f"<User:\n"
            f"  id: {self.id}\n"
            f"  forename: {self.forename}\n"
            f"  surname: {self.surname}\n"
            f"  email: {self.email}\n"
            f"  role: {self.role}\n"
            f">"
        )