from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()

class ProductCategory(database.Model):
    __tablename__ = "productcategory"
    id = database.Column(database.Integer, primary_key=True)
    productId = database.Column(database.Integer, database.ForeignKey("product.id"), nullable = False)
    categoryId = database.Column(database.Integer, database.ForeignKey("category.id"), nullable = False)

class ProductOrder(database.Model):
    __tablename__ = "productorder"
    id = database.Column(database.Integer, primary_key=True)
    productId = database.Column(database.Integer, database.ForeignKey("product.id"), nullable = False)
    orderId = database.Column(database.Integer, database.ForeignKey("order.id"), nullable = False)
    quantity = database.Column(database.Integer, nullable=False)

class Product(database.Model):
    __tablename__ = "product"

    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False, unique = True)
    price = database.Column(database.Float, nullable = False)

    categories = database.relationship("Category", secondary=ProductCategory.__table__, back_populates="products")
    orders = database.relationship("Order", secondary=ProductOrder.__table__, back_populates="products")


class Category(database.Model):
    __tablename__ = "category"

    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False, unique=True)

    products = database.relationship("Product", secondary=ProductCategory.__table__, back_populates="categories")


class Order(database.Model):
    __tablename__ = "order"

    id = database.Column(database.Integer, primary_key=True)
    total_price = database.Column(database.Float, nullable = False)
    status = database.Column(database.String(10), nullable=False, default = "CREATED")
    time_of_creation = database.Column(database.DateTime, default = database.func.current_timestamp())
    email = database.Column(database.String(256), nullable=False)

    products = database.relationship("Product", secondary=ProductOrder.__table__, back_populates="orders")
