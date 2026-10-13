import re

from flask import Flask
from flask import request
from flask import jsonify

from flask_jwt_extended import JWTManager

from configuration import Configuration

from models import database
from models import User
from flask_jwt_extended import create_access_token
from models import ROLE_EMPLOYEE
from models import ROLE_DIRECTOR
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity
import time
from sqlalchemy.exc import OperationalError
application = Flask(__name__)
application.config.from_object(Configuration) # prepisuje atribute od Configuration u application.config

database.init_app(application)

jwt = JWTManager(application) # turn on and set up  JWT for Flask application

email_pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")

MIN_PASSWORD_LENGTH = 8
MAX_FIELD_LENGTH = 256


@application.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {} # ako je nevalidan json ili nedostaje zaglavlje vrac None -> {}

    forename = data.get("forename", "")
    surname = data.get("surname", "")
    email = data.get("email", "")
    password = data.get("password", "")

    if not isinstance(forename, str) or len(forename) == 0:
        return jsonify(message="Field forename is missing."), 400

    if len(forename) > MAX_FIELD_LENGTH:
        return jsonify(message="Field forename is too long."), 400

    if not isinstance(surname, str) or len(surname) == 0:
        return jsonify(message="Field surname is missing."), 400

    if len(surname) > MAX_FIELD_LENGTH:
        return jsonify(message="Field surname is too long."), 400

    if not isinstance(email, str) or len(email) == 0:
        return jsonify(message="Field email is missing."), 400

    if len(email) > MAX_FIELD_LENGTH:
        return jsonify(message="Field email is too long."), 400

    if not isinstance(password, str) or len(password) == 0:
        return jsonify(message="Field password is missing."), 400

    if len(password) > MAX_FIELD_LENGTH:
        return jsonify(message="Field password is too long."), 400

    if not email_pattern.match(email):
        return jsonify(message="Invalid email."), 400

    if len(password) < MIN_PASSWORD_LENGTH:
        return jsonify(message="Invalid password."), 400

    if User.query.filter(User.email == email).first() is not None:
        return jsonify(message="Email already exists."), 400

    new_user = User(
        forename = forename,
        surname = surname,
        email = email,
        password = password,
        role = ROLE_EMPLOYEE
    )

    database.session.add(new_user) #stavlja objekat u sesiju
    database.session.commit() #stavlja objekat u MySQL

    return "", 200


@application.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    email = data.get("email", "")
    password = data.get("password", "")

    if not isinstance(email, str) or  len(email) == 0:
        return jsonify(message="Field email is missing."), 400

    if len(email) > MAX_FIELD_LENGTH:
        return jsonify(message="Field email is too long."), 400

    if not isinstance(password, str) or  len(password) == 0:
        return jsonify(message="Field password is missing."), 400

    if len(password) > MAX_FIELD_LENGTH:
        return jsonify(message="Field password is too long."), 400

    if not email_pattern.match(email):
        return jsonify(message="Invalid email."), 400

    user = User.query.filter(User.email == email, User.password == password).first()

    if user is None:
        return jsonify(message="Invalid credentials."), 400

    additional_user_claims = {
        "forename": user.forename,
        "surname": user.surname,
        "email": user.email,
        "role": user.role
    }

    token =  create_access_token(
        identity=user.email,
        additional_claims=additional_user_claims
    )

    return jsonify(accessToken=token), 200


@application.route("/delete", methods=["POST"])
@jwt_required()
def delete():
    email = get_jwt_identity()
    user = User.query.filter(User.email == email).first()
    if user is None:
        return jsonify(message="Unknown user."), 400

    database.session.delete(user)
    database.session.commit()

    return "", 200


def initialize_database():
    for attempt in range(40):
        try:
            with application.app_context():
                database.create_all()

                director = User.query.filter(User.email == "onlymoney@gmail.com").first()

                if director is None:
                    director = User(
                        forename = "Scrooge",
                        surname = "McDuck",
                        email = "onlymoney@gmail.com",
                        password = "evenmoremoney",
                        role = ROLE_DIRECTOR
                    )

                    database.session.add(director)
                    database.session.commit()
            return
        except OperationalError:
            print(f"Database not ready, attempt {attempt + 1} of 40")
            time.sleep(2)

    raise RuntimeError("Database is not reachable.")


initialize_database()

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5000, debug=True)