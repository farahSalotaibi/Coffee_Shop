import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db, db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()


# ROUTES
'''
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
        returns status code 200 and json {"success": True, "drinks": drinks}
        where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks', methods=['GET'])
def get_drinks():
    all_drinks = Drink.query.all()
    if all_drinks is None:
        abort(404)
    drinks = []
    for drink in all_drinks:
        drinks.append(drink.short())

    return jsonify({
        'success': True,
        'drinks': drinks
    })


'''
    GET /drinks-detail
        it require the 'get:drinks-detail' permission
        it contain the drink.long() data representation
        returns status code 200 and json {"success": True, "drinks": drinks}
        where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    all_drinks = Drink.query.all()
    drink_list = []
    for drink in all_drinks:
        drink_list.append(drink.long())
    return jsonify({
        'success': True,
        'drinks': drink_list
    })


'''
    POST /drinks
        it create a new row in the drinks table
        it require the 'post:drinks' permission which apply only on the manager
        it contain the drink.long() data representation
        returns status code 200 and json {"success": True, "drinks": drink}
        where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_drink(payload):
    body = request.get_json()

    if body is None:
        abort(404)

    else:
        new_title = body.get('title', None)
        new_recipe = body.get('recipe', None)

        try:
            drink = Drink(
                title=new_title,
                recipe=json.dumps(new_recipe)
            )
            drink.insert()
            return jsonify(
                {"success": True, "drinks": [drink.long()]}
            )

        except BaseException:
            abort(422)


'''
    PATCH /drinks/<id>
        where <id> is the existing model id
        it respond with a 404 error if <id> is not found
        it update the corresponding row for <id>
        it require the 'patch:drinks' permission  apply only for the manager
        it contain the drink.long() data representation
        returns status code 200 and json {"success": True, "drinks": drink}
        where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drink(payload, drink_id):
    body = request.get_json()
    if body is None:
        abort(404)

    else:
        new_title = body.get('title', None)
        new_recipe = body.get('recipe', None)

        try:
            drink = Drink.query.filter_by(id=drink_id).one_or_none()
            if drink is None:
                abort(404)
            drink.title = new_title
            drink.recipe = json.dumps(new_recipe)

            drink.update()
            return jsonify(
                {"success": True, "drinks": [drink.long()]}
            )

        except BaseException:
            abort(422)


'''
    DELETE /drinks/<id>
        where <id> is the existing model id
        it respond with a 404 error if <id> is not found
        it delete the corresponding row for <id>
        it require the 'delete:drinks' permission for the manager only
        returns status code 200 and json {"success": True, "delete": id}
        where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''


@ app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@ requires_auth('delete:drinks')
def delete_drink(payload, drink_id):
    try:
        drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
        if drink is None:
            abort(404)
        drink.delete()

        return jsonify({
            'success': True,
            'deleted': drink_id
        })
    except BaseException:
        abort(422)


# Error Handling

@ app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@ app.errorhandler(404)
def resourcenotfound(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@ app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['code']
    }), 401
