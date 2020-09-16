import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from .database.models import db_drop_and_create_all, setup_db, Drink
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
@TODO implement endpoint

    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json
    {"success": True, "drinks": drinks} where drinks is the list of drinks
    or appropriate status code indicating reason for failure
'''


@app.route('/drinks', methods='GET')
def get_drinks():
    body = request.get_json()
    drinks = Drink.query.all().short()
    if len(drinks) == 0:
        return abort(404, 'Drinks not found')
    return jsonify({
        "success": True,
        "drinks": [drink.short() for drink in drinks]
    }), 200


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json
    {"success": True, "drinks": drinks} where drinks is the list of drinks
    or appropriate status code indicating reason for failure
'''


@app.route('/drinks-detail', methods='GET')
@requires_auth('get:drinks-detail')
def get_drinks_detail():
    body = request.get_json()
    drinks = Drink.query.all()
    if len(drinks) == 0:
        return abort(404, 'Drinks not found')
    return jsonify({
        "success": True,
        "drinks": [drink.long() for drink in drinks]
    }), 200


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json
    {"success": True, "drinks": drink} where
    drink an array containing only the newly created drink
    or appropriate status code indicating reason for failure
'''


@app.route('/drinks', methods='POST')
@requires_auth('post:drinks')
def create_drinks():
    body = request.get_json()
    req_title = body.get('title', None)
    req_recipe = body.get('recipe', None)
    if not (req_title and req_recipe):
        return abort(400, 'Required object keys missing from request')
    try:
        if isinstance(req_recipe, dict):
            req_recipe = [req_recipe]
        drink = Drink(title=req_title, recipe=req_recipe)
        drink.insert()
    except Exception:
        return abort(500)

    return jsonify({
        "success": True,
        "drinks": drink.long()
    })


'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json
    {"success": True, "drinks": drink} where
    drink an array containing only the updated drink
    or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:drink_id>', methods='PATCH')
@requires_auth('patch:drinks')
def edit_drink(drink_id):
    body = request.get_json()
    drink = Drink.query.filter(
        Drink.id == drink_id
    ).one_or_none()
    if drink is None:
        return(404, f'Drink with id {drink_id} not found')
    try:
        req_title = body.get('title', None)
        req_recipe = body.get('recipe', None)
        if req_title:
            drink.title = req_title
        if req_recipe:
            drink.recipe = json.dumps(body['recipe'])

        drink.update()
    except Exception:
        return abort(500)

    return json.dumps({
        'success': True,
        'drinks': drink.long()
        }), 200


'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json
    {"success": True, "delete": id} where id is the id of the deleted record
    or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:drink_id>', methods='DELETE')
@requires_auth('delete:drinks')
def delete_drink(drink_id):
    drink = Drink.query.filter(
        Drink.id == drink_id
    ).one_or_none()
    if drink is None:
        return abort(404, f'Drink with id {drink_id} not found')
    try:
        drink.delete()
    except Exception:
        return abort(500)
    return jsonify({
        "success": True,
        "delete": drink_id
    }), 200

# Error Handling


@app.errorhandler(HTTPException)
def http_exception_handler(error):
    return jsonify({
        'success': False,
        'error': error.code,
        'message': error.description
        }), error.code


@app.errorhandler(Exception)
def exception_handler(error):
    return jsonify({
        'success': False,
        'error': 500,
        'message': f'Internal Server error: {error}'
        }), 500


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''


@app.errorhandler(AuthError)
def authorization_error(error):
    return jsonify({
        "success": False,
        "error": error.code,
        "message": error.description
    }), error.code
