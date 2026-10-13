import json
import re
import uuid
from functools import wraps

from flask import Flask
from flask import request
from flask import jsonify

from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt
from pymongo import MongoClient
from bson import ObjectId
import redis
from datetime import datetime
from configuration import Configuration
from configuration import mongo_user
from configuration import mongo_password
from configuration import mongo_host
from configuration import mongo_port
from configuration import mongo_database_name
from configuration import redis_host
from configuration import redis_port

ROLE_EMPLOYEE = "employee"
application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)

client = MongoClient(
    username = mongo_user,
    password = mongo_password,
    host = mongo_host,
    port = mongo_port,
    authSource = "admin"
)

mongo_database = client[mongo_database_name]
assets = mongo_database["assets"]

redis_client = redis.Redis(
    host = redis_host,
    port = redis_port,
    decode_responses = True # redis send bytes through network, and this command convert it into string, before it takes it back
)

def role_check(role):
    def decorator(function):
        @jwt_required()
        @wraps(function)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get("role") == role:
                return function(*args, **kwargs)
            else:
                return jsonify(msg="Missing Authorization Header"), 401
        return wrapper
    return decorator
@application.route("/create_buy_order", methods=["POST"])
@role_check(ROLE_EMPLOYEE)
def create_buy_order():
    data = request.get_json(silent=True) or {}

    name = data.get("name", "")
    categories = data.get("categories")
    buying_price = data.get("buying_price") # None if key doesn't exists
    info = data.get("info")


    if not isinstance(name, str) or len(name) == 0 or len(name) > 256:
        return jsonify(message="Field name is missing."), 400
    if not isinstance(categories, list):
        return jsonify(message="Field categories is missing."), 400
    if not all(isinstance(category, str) for category in categories):
        return jsonify(message="Field categories is missing."), 400
    if buying_price is None:
        return jsonify(message="Field buying_price is missing."), 400
    if info is None or not isinstance(info, dict):
        return jsonify(message="Field info is missing."), 400
    if len(categories) == 0:
        return jsonify(message="Categories list is empty."), 400
    if not isinstance(buying_price, (int, float)) or buying_price <= 0:
        return jsonify({"message" : "Invalid buying price."}), 400
    if any(len(c)>256 for c in categories):
        return jsonify({"message":"Field categories is too long."}), 400



    buy_order = {
        "order_type": "BUY",
        "name": name,
        "categories": categories,
        "buying_price": buying_price,
        "info": info
    }
    redis_client.set(str(uuid.uuid4()), json.dumps(buy_order)) # convert python dict into JSON string, opposite of json.loads()
    return "", 200

def parse_asset_id(value):  # try from string to make identificator, for not-valid-objectid throws InvalidId exception
    try: # checks MongoDB ObjectId — 24 hexadecimal characters, ObjectId - property identifier in MongoDB
        return ObjectId(value)
    except Exception:
        return None
@application.route("/create_sell_order", methods=["POST"])
@role_check(ROLE_EMPLOYEE)
def create_sell_order():
    data = request.get_json(silent=True) or {}

    id = data.get("id")
    selling_price = data.get("selling_price")

    object_id = parse_asset_id(id)
    if not isinstance(id, str) or len(id) == 0:
        return jsonify(message = "Field id is missing."), 400

    if selling_price is None:
        return jsonify(message="Field selling_price is missing."), 400

    if object_id is None:
        return jsonify(message="Invalid id."), 400

    asset = assets.find_one({"_id": object_id})
    if asset is None:
        return jsonify(message="Invalid id."), 400

    if not isinstance(selling_price, (int, float)) or selling_price <= 0:
        return jsonify(message = "Invalid selling price."), 400


    sell_order = {
        "order_type": "SELL",
        "id": id,
        "selling_price": selling_price
    }

    redis_client.set(str(uuid.uuid4()), json.dumps(sell_order))

    return "", 200

def parse_iso_date(value):
    if not isinstance(value, str):
        return None

    text = value.strip()

    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    try:
        return datetime.fromisoformat(text)
    except ValueError:
        pass

    for pattern in (
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(text, pattern)
        except ValueError:
            continue

    return None

def serialize_asset(document): # convert MongoDB to dict
    asset = {
        "id": str(document["_id"]),
        "name": document.get("name"),
        "categories": document.get("categories", []),
        "buying_price": document.get("buying_price"),
        "info": document.get("info", {})
    }

    buying_date = document.get("buying_date")
    selling_date = document.get("selling_date")
    selling_price = document.get("selling_price")

    if buying_date is not None:
        asset["buying_date"] = buying_date.isoformat()
    if selling_date is not None:
        asset["selling_date"] = selling_date.isoformat()
    if selling_price is not None:
        asset["selling_price"] = selling_price

    return asset


@application.route("/search", methods=["POST"])
@role_check(ROLE_EMPLOYEE)
def search():
    data = request.get_json(silent=True) or {}

    filters = {}

    name = data.get("name")
    category = data.get("category")
    buying_date = parse_iso_date(data.get("buying_date"))
    selling_date = parse_iso_date(data.get("selling_date"))
    info_filters = data.get("info_filters")

    # check name
    if isinstance(name, str) and len(name) > 0:
        filters["name"] = {"$regex": re.escape(name)}

    # check category
    if isinstance(category, str) and len(category) > 0:
        filters["categories"] = category

    # check buying_date
    if buying_date is not None:
        filters["buying_date"] = {"$gt": buying_date}

    # check selling_date
    if selling_date is not None:
        filters["selling_date"] = {"$lt": selling_date}

    # check info_filters
    if isinstance(info_filters, list):
        for info_filter in info_filters:
            if not isinstance(info_filter, dict):
                continue

            field = info_filter.get("field")
            operator = info_filter.get("operator")

            if not isinstance(field, str) or len(field) == 0:
                continue
            if not isinstance(operator, str) or len(operator) == 0:
                continue

            if not operator.startswith("$"):
                operator = "$" + operator

            filters["info." + field] = {operator: info_filter.get("value")} #ex.: "$eq":"high"

    result = [serialize_asset(document) for document in assets.find(filters)]

    return jsonify(assets=result), 200

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5001, debug=True)
