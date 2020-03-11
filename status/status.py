from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import json


app = Flask(__name__)
dbURL = 'mysql+mysqlconnector://root@localhost:3306/status'
app.config['SQLALCHEMY_DATABASE_URI'] = dbURL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)


class Status(db.Model):
    __tablename__ = 'status'

    machineid = db.Column(db.Integer, primary_key=True)
    statuscodeid = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(100), nullable=True)
    curuser = db.Column(db.Integer, nullable=False)
    prevuser = db.Column(db.Integer, nullable=False)
    errcodeid = db.Column(db.Integer, nullable=False)
    unlockcode = db.Column(db.String(1000), nullable=False)
    startcode = db.Column(db.String(1000), nullable=False)

    def __init__(self, machineid, statuscodeid, location, curuser, prevuser, errcodeid, unlockcode, startcode):
        self.machineid = machineid
        self.statuscodeid = statuscodeid
        self.location = location
        self.curuser = curuser
        self.prevuser = prevuser
        self.errcodeid = errcodeid
        self.unlockcode = unlockcode
        self.startcode = startcode

    def json(self):
        return {"machineid": self.machineid, "statuscodeid": self.statuscodeid, "location": self.location, "curuser": self.curuser, "prevuser": self.prevuser, "errcodeid": self.errcodeid, "unlockcode": self.unlockcode, "startcode": self.startcode}


engine = create_engine(dbURL)
if not database_exists(engine.url):
    create_database(engine.url)
db.create_all()
db.session.commit()


@app.route("/status")
def get_available():
    return jsonify({"status": [status.json() for status in Status.query.all()]})


@app.route("/status/<string:location>&<int:statuscodeid>")
def find_by_location(location, statuscodeid):
    status = Status.query.filter_by(
        location=location, statuscodeid=statuscodeid).all()
    if status:
        return jsonify({"machineid": [status.json()for status in Status.query.filter_by(location=location, statuscodeid=statuscodeid).all()]})
    return jsonify({"message": "Location not found."}), 404


@app.route("/status/<int:machineid>")
def find_by_machineid(machineid):
    status = Status.query.filter_by(machineid=machineid).all()
    if status:
        return jsonify({"machineid": [status.json()for status in Status.query.filter_by(machineid=machineid).all()]})
    return jsonify({"message": "Machine not found."}), 404


@app.route("/status/<int:machineid>&<string:location>", methods=['PUT'])
def update_machine(machineid, location):
    status = Status.query.filter_by(
        machineid=machineid, location=location).first()
    errcodeid = request.json["errcodeid"]
    statuscodeid = request.json["statuscodeid"]
    curuser = request.json["curuser"]
    prevuser = request.json["prevuser"]
    startcode = request.json["startcode"]
    unlockcode = request.json["unlockcode"]

    status.errcodeid = errcodeid
    status.statuscodeid = statuscodeid
    status.curuser = curuser
    status.startcode = startcode
    status.unlockcode = unlockcode

    try:
        db.session.commit()
    except:
        return jsonify({"message": "Error Updating Data"}), 500

    return jsonify(status.json()), 201


@app.route("/status/<int:machineid>&<string:location>", methods=['POST'])
def create_machine(machineid, location):
    if (Status.query.filter_by(machineid=machineid, location=location).first()):
        return jsonify({"message": "Machine Already Exist"}), 400
    data = request.get_json()
    status = Status(machineid, **data)
    print(status)
    try:
        db.session.add(status)
        db.session.commit()
    except:
        return jsonify({"message": "Error Updating Data"}), 500

    return jsonify(status.json()), 201


if __name__ == '__main__':
    app.run(port=5000, debug=True)
