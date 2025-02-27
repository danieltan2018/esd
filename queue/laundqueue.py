from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import json
import pika
import requests
from datetime import datetime

statusURL = "http://status.delaundro.me"

app = Flask(__name__)
dbURL = 'mysql+mysqlconnector://root@db:3306/queue'
app.config['SQLALCHEMY_DATABASE_URI'] = dbURL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class LaundQueue(db.Model):
    __tablename__ = 'queue'

    queue_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    location = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    machine_id = db.Column(db.Integer, nullable=True)
    status_code = db.Column(db.Integer, nullable=True)
    service_type = db.Column(db.String(64), nullable=True)
    date_time = db.Column(db.String(100), nullable=True)

    def __init__(self, queue_id, user_id, machine_id, location, service_type, date_time, status_code):
        self.queue_id = queue_id
        self.user_id = user_id
        self.machine_id = machine_id
        self.location = location
        self.service_type = service_type
        self.date_time = date_time
        self.status_code = status_code

    def json(self):
        return {"queue_id": self.queue_id, "user_id": self.user_id, "machine_id": self.machine_id, "location": self.location, "status_code": self.status_code,
                "service_type": self.service_type, "date_time": self.date_time}


engine = create_engine(dbURL)
if not database_exists(engine.url):
    create_database(engine.url)
db.create_all()
db.session.commit()


@app.route("/newqueue", methods=['POST'])
def insert_queue():
    code = 200
    result = {}
    location = request.args.get('location')
    user_id = request.args.get('user_id')
    now = datetime.now()
    data = {"queue_id": None, "location": location, "user_id": user_id,
            "machine_id": None, "service_type": None, "status_code": None, "date_time": now}
    laundQueue = LaundQueue(**data)
    try:
        db.session.add(laundQueue)
        db.session.commit()
    except:
        code = 500
        result = {"code": code, "message": "Error Updating Data"}
    if code == 200:
        result = laundQueue.json()
    return str(result), code

# Calculate and return waiting time
@app.route("/calculateWaitTime")
def calculate_wait_time():
    location = request.args.get('location')
    queryURL = statusURL+"/countMachine?location="+location
    machines = requests.get(queryURL).json()
    noMachines = int(machines['availandunavail'])
    wait_time = 0
    if(LaundQueue.query.filter_by(location=location).first()):
        queue_length = LaundQueue.query.filter_by(location=location).count()
        wait_time += (45*queue_length)/noMachines
    return str(wait_time)

# Return list of Queues
@app.route("/queuelist")
def laundqueue_list():
    location = request.args.get('location')
    laundqueue = LaundQueue.query.filter_by(
        location=location).all()
    if laundqueue:
        return jsonify({"queue": [laundqueue.json()for laundqueue
                                  in LaundQueue.query.filter_by(location=location).all()]})
    return jsonify({"message": "There is no queue in this location."}), 404


# Return next user, assigned queue_id
@app.route("/nextuser")
def next_user():
    location = request.args.get('location')
    laundqueue = LaundQueue.query.filter_by(location=location).first()
    if laundqueue == None:
        return jsonify({"message": "not found in the queue"}), 404
    else:
        laundqueue = LaundQueue.query.filter_by(location=location).first()
        next_user = laundqueue.json()["user_id"]
        queue_id = laundqueue.json()["queue_id"]
        if next_user:
            return jsonify({"user_id": next_user, "queue_id": queue_id})
        return jsonify({"message": "No user in the queue"}), 404

# Return wash type
@app.route("/washtype")
def get_wash_type():
    user_id = request.args.get('user_id')
    laundqueue = LaundQueue.query.filter_by(user_id=user_id).first()
    wash_type = laundqueue.json()["service_type"]
    if wash_type == None:
        return jsonify({"wash type": "Wash Type not indicated yet"})
    return jsonify({"wash type": wash_type}), 200


# Insert MachineID and and Washtype to Queue
@app.route("/allocateMachine", methods=['PUT'])
def alloc_Machine():
    user_id = request.args.get('user_id')
    queue_id = request.args.get('queue_id')
    wash_type = request.args.get('service_type')
    machine_id = request.args.get('machine_id')
    code = 200
    result = {}
    laundqueue = LaundQueue.query.filter_by(
        user_id=user_id, queue_id=queue_id).first()
    if laundqueue:
        laundqueue.service_type = wash_type
        laundqueue.machine_id = machine_id
    else:
        code = 400
        result = {"message": "No such Data"}
    try:
        db.session.commit()
    except:
        code = 500
        result = {"message": "Error Updating Data"}

    if code == 200:
        result = laundqueue.json()
    return result, code


# Return  duration, cost
# Dequeue
@app.route("/serviceDequeue")
def service_details():
    user_id = request.args.get('user_id')
    location = request.args.get('location')
    laundqueue = LaundQueue.query.filter_by(
        user_id=user_id, location=location).first()
    if laundqueue:
        db.session.delete(laundqueue)
        db.session.commit()
    return {"Status": "Success"}, 200

# # #Remove from Queue
# @app.route("/dequeue/<string:location>&<int:queue_id>")
# def remove_from_queue(location, queue_id):
#     laundqueue = LaundQueue.query.filter_by(location= location, queue_id= queue_id)
#     db.session.delete(laundqueue)
#     db.commit()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, threaded=True)
