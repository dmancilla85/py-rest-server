"""
Basic example of a resource server
"""
import logging
import time
import flask_jwt_extended
import bcrypt
from httpproblem import problem_http_response
from flask import request, jsonify, Response
from os import environ as env

from services.mongodb_service import MongoDbService

# MongoDB's connection string
mongo_client = MongoDbService()
users = mongo_client.get_collection("users")


def decode_token(token):
    try:
        return flask_jwt_extended.decode_token(token)
    except Exception as e:
        logging.error(f"Error decoding token: {e}")
        problem = problem_http_response(401, "Something went wrong", str(e), "decode_token")
        return Response(problem['body'], status=problem['statusCode'], headers=problem['headers'])


def login():
    data = request.get_json(silent=True)
    if not data:
        return _error(400, "Login incorrect", "Request must have a JSON body.")

    username = data.get("email") or ""
    password = data.get("password") or ""

    if not username or not password:
        return _error(400, "Login incorrect", "Email and password are required.")

    item = users.find_one({'email': username})
    if item is not None:
        item['_id'] = str(item['_id'])
        if bcrypt.checkpw(password.encode('utf-8'), item['password'].encode('utf-8')):
            return jsonify({"user": item, "token": _build_token(username)})
        return _error(400, "Login incorrect", "The password is incorrect.")

    return _error(400, "Login incorrect", "Email is not valid.")


def _error(status_code, title, detail):
    problem = problem_http_response(status_code, title, detail, "/auth/login")
    return Response(problem['body'], status=problem['statusCode'], headers=problem['headers'])


def _build_token(username) -> str:
    timestamp = int(time.time())
    lifetime = int(env.get('JWT_LIFETIME_SECONDS', 3600))

    payload = {
        "iss": env.get('JWT_ISSUER', 'localhost'),
        "iat": timestamp,
        "aud": env.get('JWT_AUDIENCE', 'localhost'),
        "exp": timestamp + lifetime,
        "sub": str(username),
    }

    return flask_jwt_extended.create_access_token(username, additional_claims=payload)
