from flask import Flask, request, Response, jsonify
from sqlalchemy.orm import Session
from configuration import Configuration
from models import database, Order, Product, Category, ProductCategory, ProductOrder
from email.utils import parseaddr
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt_identity, get_jwt
from sqlalchemy import and_, func
from rolePerm import roleCheck
import json

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


@application.route("/search", methods=["GET"])
@roleCheck("kupac")
def search():
    name = request.args.get('name', '')
    categoryName = request.args.get('category', '')
    if name != '' and categoryName != '':
        products = Product.query.join(Product.categories).filter(and_(
            Product.name.like(f'%{name}%'),
            Category.name.like(f'%{categoryName}%')
        )).group_by(Product.id).all()

        categories = Category.query.join(ProductCategory, Category.id == ProductCategory.categoryId).join(
            Product, Product.id == ProductCategory.productId).filter(
            and_(
            Product.id.in_([product.id for product in products]),
            Category.name.like(f'%{categoryName}%')
            )
        ).group_by(Category.id).having(func.count(Product.id) > 0).all()
    elif categoryName != '':

        products = Product.query.join(Product.categories).filter(
            Category.name.like(f'%{categoryName}%')
        ).group_by(Product.id).all()

        categories = Category.query.join(ProductCategory, Category.id == ProductCategory.categoryId).join(
            Product, Product.id == ProductCategory.productId).filter(
            and_(
            Product.id.in_([product.id for product in products]),
            Category.name.like(f'%{categoryName}%'))
        ).group_by(Category.id).having(func.count(Product.id) > 0).all()

    elif name != '':
        products = Product.query.filter(Product.name.like(f'%{name}%')).all()
        categories = Category.query.join(ProductCategory, Category.id == ProductCategory.categoryId) .join(
            Product, Product.id == ProductCategory.productId).filter(
            Product.id.in_([product.id for product in products])).group_by(Category.id).having(
            func.count(Product.id) > 0).all()
    else:
        products = Product.query.all()
        categories = Category.query.join(
            ProductCategory, Category.id == ProductCategory.categoryId).join(
            Product, Product.id == ProductCategory.productId).filter(
            Product.id.in_([product.id for product in products])).group_by(Category.id).having(
            func.count(Product.id) > 0).all()
    return Response(json.dumps({
        'categories': [category.name for category in categories],
        'products': [{
            'categories': [category.name for category in product.categories],
            'id': product.id,
            'name': product.name,
            'price': product.price,
        } for product in products]
    }), status=200)


@application.route("/order", methods=["POST"])
@roleCheck("kupac")
def order():
    header = request.headers.get('Authorization')
    if not header:
        return jsonify({"msg": "Missing Authorization Header"}), 401

    requests = request.json.get('requests')
    if not requests:
        return jsonify({"message": "Field requests is missing."}), 400

    email = get_jwt_identity()
    total_price = 0
    i = 0

    for req in requests:
        id = req.get('id')
        if not id:
            return jsonify({"message": f"Product id is missing for request number {i}."}), 400
        quantity = req.get('quantity')
        if not quantity:
            return jsonify({"message": f"Product quantity is missing for request number {i}."}), 400

        try:
            id = int(id)
            if id <= 0:
                raise ValueError
        except ValueError:
            return jsonify({"message": f"Invalid product id for request number {i}."}), 400

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            return jsonify({"message": f"Invalid product quantity for request number {i}."}), 400

        product = Product.query.get(id)
        if not product:
            return jsonify({"message": f"Invalid product for request number {i}."}), 400



        total_price += quantity * product.price
        i+=1

    order = Order(total_price=total_price, email=email)
    database.session.add(order)
    database.session.commit()

    for req in requests:
        product_order = ProductOrder(productId=req['id'], orderId=order.id, quantity=req['quantity'])
        database.session.add(product_order)

    database.session.commit()

    return jsonify({"id": order.id}), 200



@application.route("/delivered", methods=["POST"])
@roleCheck("kupac")
def delivered():
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

    order = Order.query.filter(and_(
        Order.id == id,
        Order.status == 'PENDING'
    )).first()
    if not order:
        return jsonify({"message": "Invalid order id."}), 400

    order.status = "COMPLETE"
    database.session.add(order)
    database.session.commit()

    return '', 200


@application.route("/status", methods=["GET"])
@roleCheck("kupac")
def status():
    header = request.headers.get('Authorization')
    if not header:
        return jsonify({"msg": "Missing Authorization Header"}), 401

    email = get_jwt_identity()

    orders = Order.query.filter_by(email=email).all()
    result = []
    for order in orders:
        products_list = []
        for product in order.products:
            product_order = ProductOrder.query.filter_by(productId=product.id, orderId=order.id).first()

            quantity = product_order.quantity

            product_data = {
                "categories": [cat.name for cat in product.categories],
                "name": product.name,
                "price": product.price,
                "quantity": quantity
            }
            products_list.append(product_data)
        """
        stat = ""
        if order.status == "čekanja":
            stat = "CREATED"
        elif order.status == "na putu":
            stat = "PENDING"
        elif order.status == "izvršena":
            stat = "COMPLETE"
        """
        order_data = {
            "products": products_list,
            "price": order.total_price,
            "status": order.status,
            "timestamp": order.time_of_creation.strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        result.append(order_data)

    return jsonify({"orders": result}), 200


if(__name__=="__main__"):
    database.init_app(application)
    application.run(debug = True, host="0.0.0.0", port = 5002)