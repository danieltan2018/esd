from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import json
import pika

app = Flask(__name__)
dbURL = 'mysql+mysqlconnector://root@db:3306/status'
app.config['SQLALCHEMY_DATABASE_URI'] = dbURL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)


class Status(db.Model):
    __tablename__ = 'status'

    machineid = db.Column(db.Integer, primary_key=True)
    statuscodeid = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(100), primary_key=True)
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


@app.route("/status/<string:location>")
def get_location(location):
    return_location = []
    for status in Status.query.all():
        status_container = status.json()
        print(status_container)
        if status_container['location'] not in return_location:
            return_location.append(status_container['location'])
    return jsonify({"Location": return_location})


@app.route("/status/<int:machineid>&<string:location>", methods=['PUT'])
def update_machine(machineid, location):
    code = 200
    result = {}
    if(Status.query.filter_by(machineid=machineid, location=location).first()):
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
        status.prevuser = prevuser
        status.startcode = startcode
        status.unlockcode = unlockcode

    else:
        code = 400
        result = {"code": code, "message": "No such Data"}
    try:
        db.session.commit()
    except:
        code = 500
        result = {"code": code, "message": "Error Updating Data"}

    if code == 200:
        if errcodeid == 0:
            status.errcodeid = "none"
        elif errcodeid == 1:
            status.errcodeid = "Low on Detergent"
        elif errcodeid == 2:
            status.errcodeid = "Machine is Down"
        elif errcodeid == 3:
            status.errcodeid = "Water is Low"
        else:
            status.errcodeid = "Error Unknown Call Tier 3 Support"
        result = status.json()
    send_status(result)
    return str(result), code


@app.route("/status/<int:machineid>&<string:location>", methods=['POST'])
def create_machine(machineid, location):
    code = 200
    result = {}
    if (Status.query.filter_by(machineid=machineid, location=location).first()):
        code = 400
        result = {"code": code, "message": "Machine Already Exist"}
    data = request.get_json()
    status = Status(machineid, **data)
    try:
        db.session.add(status)
        db.session.commit()
    except:
        code = 500
        result = {"code": code, "message": "Error Updating Data"}
    if code == 200:
        result = status.json()
    send_status(result)
    return str(result), code


def send_status(status):
    # Inform Monitoring and Error Handling
    hostname = "rabbit.delaundro.me"
    port = 5672
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=hostname, port=port))
    channel = connection.channel()
    exchangename = "laundro_topic"
    channel.exchange_declare(exchange=exchangename, exchange_type='topic')
    message = json.dumps(status, default=str)

    if "code" in status:
        # inform Error
        channel.queue_declare(queue='errorhandler', durable=True)
        channel.queue_bind(exchange=exchangename,
                           queue='errorhandler', routing_key='*.error')
        channel.basic_publish(exchange=exchangename, routing_key="machine.error",
                              body=message, properties=pika.BasicProperties(delivery_mode=2))
        print("Status sent ({:d}) to error handler.".format(status["code"]))
    elif status["errcodeid"] != 'none':
        # inform Error
        channel.queue_declare(queue='errorhandler', durable=True)
        channel.queue_bind(exchange=exchangename,
                           queue='errorhandler', routing_key='*.error')
        channel.basic_publish(exchange=exchangename, routing_key="machine.error",
                              body=message, properties=pika.BasicProperties(delivery_mode=2))
        print("Machine Error:", status["errcodeid"])
    else:
        # inform shipping
        channel.queue_declare(queue='monitoring', durable=True)
        channel.queue_bind(exchange=exchangename,
                           queue='monitoring', routing_key='*.status')
        channel.basic_publish(exchange=exchangename, routing_key="machine.status",
                              body=message, properties=pika.BasicProperties(delivery_mode=2))
        print("Status sent to monitoring", message)
    connection.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, threaded=True)
