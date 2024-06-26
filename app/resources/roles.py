from flask import Flask, jsonify, request, Response
from httpproblem import problem_http_response
from pymongo import MongoClient
from bson import ObjectId
from os import environ as env

resource = 'roles'
# basePath = f"/api/{resource}"

# MongoDB's connection string
client = MongoClient(env['MONGODB_CONN'])
db = client['cafeDB']
items_collection = db[resource]


#@app.route(basePath, methods=['GET'])
def get_items():

    items = list(items_collection.find())
    for item in items:
        item['_id'] = str(item['_id'])
    return jsonify({'items': items})


#@app.route(f'{basePath}/<string:item_id>', methods=['GET'])
def get_item(item_id):

    if not ObjectId.is_valid(item_id):
        problem = problem_http_response(400, "Invalid parameters", "Item ID is not valid.", f"/{resource}/{item_id}")
        return Response(problem['body'], status=problem['statusCode'], headers=problem['headers'])

    item = items_collection.find_one({'_id': ObjectId(item_id)})
    if item is not None:
        item['_id'] = str(item['_id'])
        return jsonify(item)
    else:
        return jsonify({'message': 'Item not found'}), 404


#@app.route(basePath, methods=['POST'])
def create_item():
    item = request.get_json()
    exists = items_collection.find_one({'role': item['role']})

    if exists is not None:
        problem = problem_http_response(400, "Invalid parameters", "Item already exists.", f"/{resource}")
        return Response(problem['body'], status=problem['statusCode'], headers=problem['headers'])

    result = items_collection.insert_one(item)
    item['_id'] = str(result.inserted_id)
    return jsonify(item), 201


#@app.route(f'{basePath}/<string:item_id>', methods=['PUT'])
def update_item(item_id):

    if not ObjectId.is_valid(item_id):
        problem = problem_http_response(400, "Invalid parameters", "Item ID is not valid.", f"/{resource}/{item_id}")
        return Response(problem['body'], status=problem['statusCode'], headers=problem['headers'])

    item = request.get_json()
    result = items_collection.update_one({'_id': ObjectId(item_id)}, {'$set': item})

    if result.matched_count:
        item['_id'] = item_id
        return jsonify(item)
    else:
        problem = problem_http_response(404, "Item not found", "Item ID not exists.", f"/{resource}/{item_id}")
        return Response(problem['body'], status=problem['statusCode'], headers=problem['headers'])


#@app.route(f'{basePath}/<string:item_id>', methods=['DELETE'])
def delete_item(item_id):

    if not ObjectId.is_valid(item_id):
        problem = problem_http_response(400, "Invalid parameters", "Item ID is not valid.", f"/{resource}/{item_id}")
        return Response(problem['body'], status=problem['statusCode'], headers=problem['headers'])

    result = items_collection.delete_one({'_id': ObjectId(item_id)})

    if result.deleted_count:
        return jsonify({'message': 'Item deleted'})
    else:
        problem = problem_http_response(404, "Item not found", "Item ID not exists.", f"/{resource}/{item_id}")
        return Response(problem['body'], status=problem['statusCode'], headers=problem['headers'])