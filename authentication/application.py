import re

from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import database, User, UserRole, Role
from email.utils import parseaddr
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, decode_token,get_jwt_identity
from sqlalchemy import and_


application = Flask(__name__)
application.config.from_object(Configuration)


@application.route("/register_customer", methods=["POST"])
def register_customer():
    email = request.json.get("email", "")
    password = request.json.get("password", "")
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")

    emailEmpty = len(email)
    passwordEmpty = len(password)
    shortPassword = len(password) < 8
    forenameEmpty = len(forename)
    surnameEmpty = len(surname)
    validEmail = True

    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(regex, email):
        validEmail = False

    message = ""

    user = User.query.filter(User.email==email).first()

    if not forenameEmpty:
        message = "Field forename is missing."
    elif not surnameEmpty:
        message = "Field surname is missing."
    elif not emailEmpty:
        message = "Field email is missing."
    elif not passwordEmpty:
        message = "Field password is missing."
    elif not validEmail:
        message = "Invalid email."
    elif shortPassword:
        message = "Invalid password."
    elif user:
        message = "Email already exists."

    if message != "":
        return jsonify({"message":message}), 400


    user = User(email = email, password = password, forename = forename, surname= surname)
    database.session.add(user)
    database.session.commit()

    userRole = UserRole(userId = user.id, roleId = 2)
    database.session.add(userRole)
    database.session.commit()

    return Response(status = 200)

@application.route("/register_courier", methods=["POST"])
def register_courier():
    email = request.json.get("email", "")
    password = request.json.get("password", "")
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")

    emailEmpty = len(email)
    passwordEmpty = len(password)
    shortPassword = len(password) < 8
    forenameEmpty = len(forename)
    surnameEmpty = len(surname)
    validEmail = True

    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(regex, email):
        validEmail = False

    message = ""

    user = User.query.filter(User.email==email).first()

    if not forenameEmpty:
        message = "Field forename is missing."
    elif not surnameEmpty:
        message = "Field surname is missing."
    elif not emailEmpty:
        message = "Field email is missing."
    elif not passwordEmpty:
        message = "Field password is missing."
    elif not validEmail:
        message = "Invalid email."
    elif shortPassword:
        message = "Invalid password."
    elif user:
        message = "Email already exists."

    if message != "":
        return jsonify({"message":message}), 400


    user = User(email = email, password = password, forename = forename, surname= surname)
    database.session.add(user)
    database.session.commit()

    userRole = UserRole(userId = user.id, roleId = 3)
    database.session.add(userRole)
    database.session.commit()

    return Response(status = 200)

jwt = JWTManager(application)

@application.route("/login", methods= ["POST"])
def login():
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    emailEmpty = len(email)
    passwordEmpty = len(password)

    validEmail = True
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(regex, email):
        validEmail = False

    message = ""

    if not emailEmpty:
        message = "Field email is missing."
    elif not passwordEmpty:
        message = "Field password is missing."
    elif not validEmail:
        message = "Invalid email."

    if message != "":
        return jsonify({"message": message}), 400

    user = User.query.filter(
        and_(
            User.email==email,
            User.password==password
        )
    ).first()
    if not user:
        message = "Invalid credentials."

    if message != "":
        return jsonify({"message": message}), 400

    additionalClaims = {
        "forename" : user.forename,
        "surname" : user.surname,
        "roles": [str(role) for role in user.roles]
    }
    accessToken = create_access_token(identity = user.email, additional_claims=additionalClaims)

    return jsonify({"accessToken": accessToken}), 200

@application.route("/check", methods=["POST"])
@jwt_required()
def check():
    return "Token is valid"

@application.route("/delete", methods=["POST"])
@jwt_required()
def delete():
    token = request.headers.get('Authorization')

    user_email = get_jwt_identity()

    if not user_email:
        return jsonify({"message": "Invalid token"}), 400

    user = User.query.filter(User.email==user_email).first()

    if not user:
        return jsonify({"message": "Unknown user."}), 400


    try:
        database.session.delete(user)
        database.session.commit()
        return Response(status = 200)

    except Exception as e:
        return jsonify({"message": str(e)}), 400


if(__name__=="__main__"):
    database.init_app(application)
    application.run(debug = True, host = "0.0.0.0", port = 5000)