from flask import Blueprint, request, make_response, jsonify
from flask_jwt_simple import jwt_required, create_jwt, get_jwt_identity
from functools import wraps

from project.server import db

bp = Blueprint('auth', __name__)

def require_params(*fargs):
    def real_decorator(func):
        @wraps(func)
        def wrap(*args, **kwargs):
            post_data = request.get_json()
            for f in fargs:
                if post_data.get(f) is None:
                    return make_response(jsonify({})), 400

            return func(*args, **kwargs)

        return wrap
    return real_decorator

def check_item_exists(func):
    @wraps(func)
    def wrap(item_id):
        item = db.item.find_one(dict(_id=item_id))
        if item is None:
            return make_response(jsonify({})), 404

        return func(item_id)

    return wrap

def check_item_ownership(func):
    @wraps(func)
    def wrap(item_id):
        item = db.item.find_one(dict(_id=item_id))
        if item['owner'] != get_jwt_identity():
            return make_response(jsonify({})), 403

        return func(item_id)

    return wrap

@bp.route('/auth/register', methods=['POST'])
@require_params('username', 'password')
def register():
    post_data = request.get_json()
    username = post_data.get('username')
    password = post_data.get('password')

    user = db.user.find_one(dict(username=username))

    if not user:
        user_id = db.user.insert_one(dict(
            username=username,
            password=password
        )).inserted_id

        return make_response(jsonify({})), 201
    else:
        return make_response(jsonify({})), 409

@bp.route('/auth/login', methods=['POST'])
@require_params('username', 'password')
def login():
    post_data = request.get_json()
    username = post_data.get('username')
    password = post_data.get('password')

    user = db.user.find_one({
        "$and": [
            dict(username=username),
            dict(password=password)
        ]
    })

    if user:
        return make_response(jsonify(dict(auth_token=create_jwt(identity=username)))), 201

    return make_response(jsonify(dict())), 403

@bp.route('/item', methods=['GET'])
@jwt_required
def list_items():
    f = {}
    owner = request.args.get('owner', None)

    if owner is not None:
        f = dict(owner=owner)

    items = db.item.find(f)
    return make_response(jsonify([i['data'] for i in items])), 200

@bp.route('/item/<item_id>', methods=['GET'])
@jwt_required
@check_item_exists
def get_item(item_id):
    item = db.item.find_one(dict(_id=item_id))
    return make_response(jsonify(item['data'])), 200

@bp.route('/item', methods=['POST'])
@jwt_required
def create_item():
    post_data = request.get_json()
    item = dict(data=post_data, owner=get_jwt_identity())
    item_id = db.item.insert_one(item).inserted_id

    return make_response(jsonify(dict(id=item_id))), 201

@bp.route('/item/<item_id>', methods=['PUT'])
@jwt_required
@check_item_exists
@check_item_ownership
def replace_item(item_id):
    post_data = request.get_json()
    db.item.update_one(dict(_id=item_id), {'$set': dict(data=post_data)})

    return make_response(jsonify({})), 204

@bp.route('/item/<item_id>', methods=['DELETE'])
@jwt_required
@check_item_exists
@check_item_ownership
def delete_item(item_id):
    db.item.delete_one(dict(_id=item_id))

    return make_response(jsonify({})), 204

@bp.route('/item/<item_id>/transfer', methods=['POST'])
@jwt_required
@check_item_exists
@check_item_ownership
@require_params('to')
def create_ownership_transfer(item_id):
    post_data = request.get_json()
    to = post_data.get('to')

    db.item.update_one(dict(_id=item_id), {'$set': dict(transfer=to)})

    return make_response(jsonify(dict(id=item_id))), 201

@bp.route('/item/<item_id>/transfer/claim', methods=['POST'])
@check_item_exists
@jwt_required
def claim_ownership(item_id):
    item = db.item.find_one(dict(_id=item_id))

    if item['transfer'] != get_jwt_identity():
        return make_response(jsonify({})), 403

    db.item.update_one(dict(_id=item_id), {'$set': dict(transfer=None, owner=get_jwt_identity())})

    return make_response(jsonify(dict(id=item_id))), 204
