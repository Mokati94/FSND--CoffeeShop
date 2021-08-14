import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)


'''
ENDPOINTS
'''
'''
GET /drinks:

a public endpoint, requires no permissions.
returns a list of drinks using the drink.short() representation.
'''


@app.route('/drinks', methods=["GET"])
def get_drinks():
    drinks = Drink.query.all()
    drinks_formatted = [drink.short() for drink in drinks]

    return jsonify({
        'success': True,
        'drinks': drinks_formatted
    })


'''
GET /drinks-detail:

Fetches list of drinks using the drink.long() data representation.
Requires the "get:drinks-details" permission.
'''


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-details')
def view_drinks_detail(jwt):
    drinks = Drink.query.all()
    formatted_drinks = [drink.long() for drink in drinks]

    return jsonify({
        'success': True,
        'drinks': formatted_drinks
    })


'''
POST /drinks endpoint:

Requires 'post:drinks' permission.
Creates a new row in the drinks table.
Contains the drink.long() data representation.
'''


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(jwt):
    body = json.loads(request.data.decode('utf-8'))

    try:
        drink = Drink(title=body['title'], recipe=json.dumps(body['recipe']))

        drink.insert()

        return jsonify({
            'success': True,
            'drinks': drink.long()
        })
    except Exception:
        abort(422)


'''
PATCH /drinks/<id> endpoint:

Updates the drink information at the given <id>.
Requires the 'patch:drinks' permission.
Contains drink.long() data representation.
Returns 404 error if <id> isn't found.
'''


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drink(jwt, id):
    drink = Drink.query.filter(
        Drink.id == id).one_or_none()

    if(drink is None):
        abort(404)

    body = request.get_json()
    title = body.get('title', drink.title)
    recipe = body.get('recipe', drink.recipe)

    try:
        drink.title = title
        drink.recipe = json.dumps(recipe)
        drink.update()

        return jsonify({
            'success': True,
            'drinks': [drink.long()],
        })
    except Exception:
        abort(422)


'''
DELETE /drinks/<id> :

Requires "delete:drinks" permission.
Endpoint  deletes the drink at the given <id>.
Responds with 404 error if <id> is not found.

'''


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drink')
def delete_drink(jwt, id):
    try:
        drink = Drink.query.filter(
            Drink.id == id).one_or_none()

        if(drink is None):
            abort(404)

        drink.delete()
        return jsonify({
            'success': True,
            'delete': id
        })

    except Exception:
        abort(422)


'''
Error Handling
'''

'''
422 Eror: Unprocessable

'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
404 error: Resource not found.
'''


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


'''
AuthError Handling.
'''


@app.errorhandler(AuthError)
def AuthError(error):
    return jsonify({
        "success": False,
        "error": error.error['code'],
        "message": error.error['description']
    }), 401
