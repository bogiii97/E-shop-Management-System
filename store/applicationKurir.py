from flask import Flask, request, Response, jsonify
from sqlalchemy.orm import Session
from configuration import Configuration
from models import database, Order, Product
from email.utils import parseaddr
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt_identity, get_jwt
from sqlalchemy import and_, func
from rolePerm import roleCheck

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


@application.route('/pick_up_order', methods=['POST'])
@roleCheck(role="kurir")
def pick_up_order():
    header = request.headers.get('Authorization')
    if not header:
        return jsonify({"msg": "Missing Authorization Header"}), 401

    id = request.json.get('id')
    if not id:
        return jsonify({"message": "Missing order id."}), 400

    try:
        id = int(id)
        if id <= 0:
            raise ValueError
    except ValueError:
        return jsonify({"message": "Invalid order id."}), 400

    order = Order.query.get(id)
    if not order:
        return jsonify({"message": "Invalid order id."}), 400
    if order.status != "CREATED":
        return jsonify({"message": "Invalid order id."}), 400

    order.status = "PENDING"
    database.session.commit()

    return '', 200


@application.route('/orders_to_deliver', methods=['GET'])
@roleCheck(role="kurir")
def orders_to_deliver():
    header = request.headers.get('Authorization')

    if not header:
        return jsonify({"msg": "Missing Authorization Header"}), 401

    orders = Order.query.filter_by(status='CREATED').all()

    result = {
        "orders": [{"id": order.id, "email": order.email} for order in orders]
    }

    return jsonify(result), 200


if(__name__=="__main__"):
    database.init_app(application)
    application.run(debug = True, host="0.0.0.0", port = 5003)