"""
Basic example of a resource server
"""
import time
import flask_jwt_extended
import bcrypt
from pymongo import MongoClient
from httpproblem import problem_http_response
from flask import request, jsonify, Response
from os import environ as env

# MongoDB's connection string
client = MongoClient(env['MONGODB_CONN'])
db = client['cafeDB']


def decode_token(token):
    try:
        return flask_jwt_extended.decode_token(token)
    except Exception as e:
        problem = problem_http_response(401, "Something went wrong", str(e), "decode_token")
        return Response(problem['body'], status=problem['statusCode'], headers=problem['headers'])


def login():
    username = request.json.get("email", None)
    password = request.json.get("password", None)

    if len(username) == 0 or len(password) == 0:
        problem = problem_http_response(400, "Login incorrect", "Empty parameters.", "/auth/login")
        return Response(problem['body'], status=problem['statusCode'], headers=problem['headers'])

    item = db['users'].find_one({'email': username})
    item['_id'] = str(item['_id'])

    if item is not None:
        if bcrypt.checkpw(bytes(password, 'utf-8'), bytes(item['password'], 'utf-8')):
            return jsonify({"user": item, "token": _build_token(username)})
        else:
            problem = problem_http_response(400, "Login incorrect", "The password is incorrect.", "/auth/login")
            return Response(problem['body'], status=problem['statusCode'], headers=problem['headers'])

    problem = problem_http_response(400, "Login incorrect", "Email is not valid.", "/auth/login")
    return Response(problem['body'], status=problem['statusCode'], headers=problem['headers'])


def _current_timestamp() -> int:
    return int(time.time())


def _build_token(username) -> str:
    timestamp = _current_timestamp()

    payload = {
        "iss": env['JWT_ISSUER'],
        "iat": int(timestamp),
        "aud": env['JWT_AUDIENCE'],
        "exp": int(timestamp + int(env['JWT_LIFETIME_SECONDS'])),
        "sub": str(username),
    }

    # You can use the additional_claims argument to either add
    # custom claims or override default claims in the JWT.
    return flask_jwt_extended.create_access_token(username, additional_claims=payload)
