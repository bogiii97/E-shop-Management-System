from flask import Flask, request, Response, jsonify
from sqlalchemy.orm import Session
from configuration import Configuration
from models import database, Order, Product, ProductOrder, Category, ProductCategory
from email.utils import parseaddr
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt_identity, get_jwt
from sqlalchemy import and_, func, case
from rolePerm import roleCheck
import io
import csv, json
from collections import defaultdict

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)

@application.route('/update', methods=['POST'])
@roleCheck(role="vlasnik")
def update():

    file = request.files.get('file')
    if not file:
        return jsonify({"message": "Field file is missing."}), 400

    content = file.stream.read().decode("cp1252")
    stream = io.StringIO(content)
    reader = csv.reader(stream)
    redniBroj = 0
    for row in reader:
        if len(row) != 3:
            message = "Incorrect number of values on line " + str(redniBroj) + "."
            return jsonify({"message": message}), 400
        try:
            price = float(row[2])
            if price <= 0:
                raise ValueError
        except ValueError:
            message = "Incorrect price on line " + str(redniBroj) + "."
            return jsonify({"message": message}), 400

        existing_product = Product.query.filter(Product.name==row[1]).first()
        if existing_product:
            return jsonify({"message": f"Product {row[1]} already exists."}), 400
        redniBroj+=1

    stream.seek(0)
    for row in csv.reader(stream):
        product_name = row[1]
        category_names = row[0].split('|')
        price = float(row[2])

        new_product = Product(name=product_name, price=price)
        database.session.add(new_product)
        database.session.commit()

        for cat_name in category_names:
            category = Category.query.filter(Category.name==cat_name).first()

            if not category:
                category = Category(name=cat_name)
                database.session.add(category)
                database.session.commit()

            product_category_link = ProductCategory(productId=new_product.id, categoryId=category.id)
            database.session.add(product_category_link)
            database.session.commit()

    return Response(status = 200)


@application.route('/product_statistics', methods=['GET'])
@roleCheck(role="vlasnik")
def product_statistics():
    statistics = []

    products = Product.query.all()

    for product in products:
        count = func.sum(ProductOrder.quantity)
        soldList = (ProductOrder.query.join(Product, ProductOrder.productId == Product.id)
                    .join(Order, ProductOrder.orderId == Order.id)
                    .filter(Order.status == "COMPLETE", Product.id == product.id).all())
        sold = sum(item.quantity for item in soldList)

        waitingList = (ProductOrder.query.join(Product, ProductOrder.productId == Product.id)
                       .join(Order, ProductOrder.orderId == Order.id)
                       .filter(Order.status != "COMPLETE", Product.id == product.id).all())
        waiting = sum(item.quantity for item in waitingList)


        if sold > 0 or waiting > 0:
            statistics.append({
                "name": product.name,
                "sold": sold,
                "waiting": waiting
            })
    return jsonify({"statistics": statistics}), 200

from collections import defaultdict
from flask import request, jsonify

@application.route('/category_statistics', methods=['GET'])
@roleCheck(role="vlasnik")
def category_statistics():
    header = request.headers.get('Authorization')
    if not header:
        return jsonify({"msg": "Missing Authorization Header"}), 401

    categories = Category.query.all()
    category_counts = []
    for category in categories:
        products = Product.query.join(ProductCategory, ProductCategory.productId == Product.id)\
            .filter(ProductCategory.categoryId == category.id).all()

        cnt = 0
        for product in products:
            productCompleted = ProductOrder.query.join(Product, ProductOrder.productId == Product.id)\
                .join(Order, ProductOrder.orderId == Order.id)\
                .filter(Order.status == "COMPLETE", Product.id == product.id).all()
            cnt += sum(item.quantity for item in productCompleted)
        category_counts.append([category.name, cnt])

    sorted_categories = sorted(category_counts, key=lambda x: (-x[1], x[0]))

    result =[elem[0] for elem in sorted_categories]

    return jsonify({"statistics": result}), 200


if(__name__=="__main__"):
    database.init_app(application)
    application.run(debug = True, host="0.0.0.0", port = 5001)


