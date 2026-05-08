import logging
from flask import jsonify, request, Response
from httpproblem import problem_http_response
from bson import ObjectId
from services.mongodb_service import MongoDbService


class BaseResource:
    def __init__(self, collection, stringify_fields=('_id',), unique_field='name', include_count=True):
        self.collection_name = collection
        self.stringify_fields = list(stringify_fields)
        self.unique_field = unique_field
        self.include_count = include_count
        self.mongo = MongoDbService()
        self.collection = self.mongo.get_collection(collection)

    def get_items(self):
        page = request.args.get('page', None)
        per_page = request.args.get('per_page', 20, type=int)

        if page is not None:
            page = int(page)
            skip = (page - 1) * per_page
            cursor = self.collection.find().skip(skip).limit(per_page)
        else:
            cursor = self.collection.find()

        items = list(cursor)
        for item in items:
            for field in self.stringify_fields:
                if field in item:
                    item[field] = str(item[field])

        result = {'items': items}
        if self.include_count:
            result['count'] = len(items)
        return jsonify(result)

    def get_item(self, item_id):
        if not ObjectId.is_valid(item_id):
            return self._error(400, "Invalid parameters", "Item ID is not valid.")

        item = self.collection.find_one({'_id': ObjectId(item_id)})
        if item is not None:
            for field in self.stringify_fields:
                if field in item:
                    item[field] = str(item[field])
            return jsonify(item)

        logging.warning(f"ID {item_id} not exists in {self.collection_name}.")
        return self._error(404, "Item not found", "Item ID not exists.")

    def create_item(self):
        item = request.get_json()
        if not item:
            return self._error(400, "Invalid parameters", "Request body is empty.")

        unique_value = item.get(self.unique_field)
        if unique_value:
            exists = self.collection.find_one({self.unique_field: unique_value})
            if exists is not None:
                return self._error(400, "Invalid parameters", "Item already exists.")

        result = self.collection.insert_one(item)
        item['_id'] = str(result.inserted_id)
        return jsonify(item), 201

    def update_item(self, item_id):
        if not ObjectId.is_valid(item_id):
            return self._error(400, "Invalid parameters", "Item ID is not valid.")

        item = request.get_json()
        if not item:
            return self._error(400, "Invalid parameters", "Request body is empty.")

        result = self.collection.update_one({'_id': ObjectId(item_id)}, {'$set': item})
        if result.matched_count:
            item['_id'] = item_id
            return jsonify(item)

        logging.warning(f"ID {item_id} not exists in {self.collection_name}.")
        return self._error(404, "Item not found", "Item ID not exists.")

    def delete_item(self, item_id):
        if not ObjectId.is_valid(item_id):
            return self._error(400, "Invalid parameters", "Item ID is not valid.")

        result = self.collection.delete_one({'_id': ObjectId(item_id)})
        if result.deleted_count:
            return jsonify({'message': 'Item deleted'})

        logging.warning(f"ID {item_id} not exists in {self.collection_name}.")
        return self._error(404, "Item not found", "Item ID not exists.")

    def _error(self, status_code, title, detail):
        problem = problem_http_response(
            status_code, title, detail, f"/{self.collection_name}"
        )
        return Response(problem['body'], status=problem['statusCode'], headers=problem['headers'])
