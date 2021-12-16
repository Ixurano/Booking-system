from enum import unique
from json import decoder
import os
import requests
from types import SimpleNamespace
from flask import Flask, json, jsonify, request
from flask_cors import CORS, cross_origin
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

# Load variables from .env
load_dotenv()

# Create Flask instance
app = Flask(__name__)
CORS(app)
app.config['JSON_AS_ASCII'] = False

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://jpkbxhbgkgeqxs:27448ec1c35ae46cef04537983d6d25b27c82f5bbbf654921b71283987285085@ec2-54-158-247-97.compute-1.amazonaws.com:5432/df9pte76elbftp"
# os.environ.get('DATABASE_URL')
# Borttagen för heroku låter den inte va så där VARS blir fel och går ej och ändra.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# remember to run python > from app.main import db > db.create_all() when you update the models

# Service class


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    servicename = db.Column(db.String(80), unique=True, nullable=False)
    # orders = db.relationship('Order', backref='service', lazy=True)

# Order class


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cabin_id = db.Column(db.String(80), unique=False)
    service_id = db.Column(db.Integer, unique=False)
    date = db.Column(db.DateTime(), default=db.func.now(),
                     onupdate=db.func.now())


# token try/catch to get the token from the api
try:
    url = 'https://wom21-cabin-service.herokuapp.com/auth'
    header = {'Content-Type': 'application/json'}
    # logs in. we want to change this to get this info from
    # the front-end later on
    body = {"email": "tester@example.com",  "password": "12345"}
    response = requests.post(url, headers=header, json=body)
    cabins_token = response.content.decode('utf-8')

except Exception as e:
    print(e)


@app.route("/")
def standare_route():
    return jsonify("hej")

# Route for cabins from the API


@app.route("/cabins", methods=['GET'])
def cabins_route():
    url = 'https://wom21-cabin-service.herokuapp.com/cabins/owned/'
    #x = json.loads(cabins_token, object_hook=lambda d: SimpleNamespace(**d))
    token = request.headers['x-access-token']
    header = {'x-access-token': token}
    response_data = requests.get(url, headers=header)
    return jsonify(response_data.json())

# route for services


@app.route("/services", methods=['GET', 'POST', 'PUT', 'DELETE'])
def services_route():
    ret = []
    if request.method == "GET":
        for u in Service.query.all():
            ret.append({'id': u.id, 'service': u.servicename})

    if request.method == "POST":
        body = request.get_json()

        new_service = Service(servicename=body['service'])
        db.session.add(new_service)
        db.session.commit()
        ret = ["Added new service"]

    if request.method == "PUT":
        body = request.get_json()
        if 'service' in body and 'id' in body:
            old_service = Service.query.filter_by(id=body['id']).first()
            if old_service is not None:
                old_service.servicename = body['service']
                db.session.commit()
                ret = ["Updated!"]
            else:
                ret = ["There was no service with that id"]
        else:
            ret = [
                "Endpoint expects 'service' and 'id' to be submitted as json in body"]

    if request.method == "DELETE":
        body = request.get_json()
        if 'id' in body:
            old_service = Service.query.filter_by(id=body['id']).first()
            if old_service is not None:
                db.session.delete(old_service)
                db.session.commit()
                ret = ["Deleted!"]
            else:
                ret = ["There was no service with that id"]

        else:
            ret = ["Endpoint expects 'id' to be submitted as json in body"]

    return jsonify(ret)

# Route for orders


@app.route("/orders", methods=['GET', 'POST', 'PUT', 'DELETE'])
def orders_route():
    ret = []

    if request.method == "GET":
        orders = Order.query.all()
        if orders is not None:
            for ord in orders:
                ret.append({'id': ord.id, 'cabin_id': ord.cabin_id,
                           'service_id': ord.service_id, 'date': ord.date})
        else:
            ret.append("There are currently no orders registered")

    # This needs to connect to The old API in order to get the cabins,
    # that's why it was changed to cabin_id and service_id
    if request.method == "POST":
        body = request.get_json()
        if 'service_id' in body and 'cabin_id' in body:
            new_order = Order(
                cabin_id=body['cabin_id'], service_id=body['service_id'], date=body['date'])
            db.session.add(new_order)
            db.session.commit()
            ret.append({'id': new_order.id, 'cabin_id': new_order.cabin_id,
                           'service_id': new_order.service_id, 'date': new_order.date})
        else:
            ret.append(
                "Endpoint expects 'service_id' and 'cabin_id' to be submitted as json in body")

    if request.method == "PUT":
        body = request.get_json()
        if 'service_id' in body and 'id' in body and 'cabin_id' in body:
            old_order = Order.query.filter_by(id=body['id']).first()
            if old_order is not None:
                old_order.service_id = body['service_id']
                old_order.cabin_id = body['cabin_id']
                old_order.date = body['date']
                db.session.commit()
                ret = ["Order updated!"]
            else:
                ret = ["There was no order with that id"]
        else:
            ret = [
                "Endpoint expects 'service_id', 'id' and 'cabin_id' to be submitted as json in body"]

    if request.method == "DELETE":
        body = request.get_json()
        if 'id' in body:
            old_service = Order.query.filter_by(id=body['id']).first()
            if old_service is not None:
                db.session.delete(old_service)
                db.session.commit()
                ret = ["Deleted!"]
            else:
                ret = ["There was no service with that id"]

        else:
            ret = ["Endpoint expects 'id' to be submitted as json in body"]

    return jsonify(ret)


# Run app if called directly
if __name__ == "__main__":
    app.run()
