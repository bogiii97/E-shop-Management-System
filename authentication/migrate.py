from flask import Flask
from configuration import Configuration
from flask_migrate import Migrate, init, migrate, upgrade
from models import database, Role, UserRole, User
from sqlalchemy_utils import database_exists, create_database

application = Flask(__name__)
application.config.from_object(Configuration)

migrateObject = Migrate(application, database)

if not database_exists(application.config["SQLALCHEMY_DATABASE_URI"]):
    create_database(application.config["SQLALCHEMY_DATABASE_URI"])
database.init_app(application)

with application.app_context() as context:
    init()
    migrate(message="Migration 1")
    upgrade()

    vlasnikUloga = Role(name="vlasnik")
    kupacUloga = Role(name="kupac")
    kurirUloga = Role(name="kurir")

    database.session.add(vlasnikUloga)
    database.session.add(kupacUloga)
    database.session.add(kurirUloga)

    database.session.commit()

    vlasnik = User(
        email="onlymoney@gmail.com",
        password="evenmoremoney",
        forename="Scrooge",
        surname="McDuck"
    )

    database.session.add(vlasnik)
    database.session.commit()

    userRole = UserRole(
        userId=vlasnik.id,
        roleId=vlasnikUloga.id
    )

    database.session.add(userRole)
    database.session.commit()