from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import json
import pika
import requests
from urllib.request import urlretrieve
from datetime import datetime

statusURL = "http://127.0.0.1:8002/status"

app = Flask(__name__)
dbURL = 'mysql+mysqlconnector://root@localhost:3306/queue'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/queue'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
 
db = SQLAlchemy(app)
 
class LaundQueue(db.Model):
    __tablename__ = 'queue'
 
    queue_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    location = db.Column(db.String(64), primary_key = True)
    user_id = db.Column(db.Integer, nullable=False)
    machine_id = db.Column(db.Integer, nullable=True)
    status_code = db.Column(db.Integer, nullable = True)
    service_type = db.Column(db.String(64), nullable = True)
    date_time = db.Column(db.String(100), nullable =True)
 
    def __init__(self, queue_id, user_id, machine_id, location, service_type, date_time, status_code):
        self.queue_id = queue_id
        self.user_id = user_id
        self.machine_id = machine_id
        self.location = location
        self.service_type = service_type
        self.date_time = date_time
        self.status_code = status_code


    def json(self):
        return {"queue_id": self.queue_id, "user_id": self.user_id, "machine_id":self.machine_id, "location":self.location, "status_code": self.status_code, 
        "service_type": self.service_type,"date_time":self.date_time}

        
 
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
    data = {"queue_id":None, "location": location, "user_id": user_id, "machine_id":None, "service_type":None, "status_code":None, "date_time":now}
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


# #add new service type
# @app.route("/queue/<string:user_id>", methods=['POST'])
# def add_new_service_request(user_id):
#     user_id = LaundQueue.query.get(user_id)
#     new_service_request = request.json["service_type"]

#Calculate and return waiting time
@app.route("/calculateWaitTime")
def calculate_wait_time():
    location = request.args.get('location')
    queryURL = statusURL
    machines = int(requests.get(queryURL).text)
    wait_time = 0
    if(LaundQueue.query.filter_by(location=location).first()):
        queue_length = LaundQueue.query.filter_by(location=location).count()
        wait_time += (45*queue_length)/machines
    return wait_time

# # Request available machine by location 
# @app.route("/queue/<string:location>")
# def get_avail_machine_id(location):
#     queryURL = statusURL
#     results = LaundQueue.query.filter_by(location=location).first()
#     #print("here", results)
#     if not results:
#         queryURL = statusURL +"/"+ location + "&0"
#     return requests.get(queryURL).text
    
        # return jsonify(r.json())
        
#Return list of Queues        
@app.route("/queuelist")
def laundqueue_list():
    location = request.args.get('location')
    laundqueue = LaundQueue.query.filter_by(
        location=location).all()
    if laundqueue:
        return jsonify({location+ " queue": [laundqueue.json()for laundqueue 
                in LaundQueue.query.filter_by(location=location).all()]})
    return jsonify({"message": "There is no queue in this location."}), 404


#Return next user, assigned queue_id
@app.route("/nextuser")
def next_user():
    location = request.args.get('location')
    laundqueue = LaundQueue.query.filter_by(location=location).first()
    next_user = laundqueue.json()["user_id"]
    queue_id = laundqueue.json()["queue_id"]
    if next_user:   
        return jsonify({"user_id": next_user, "queue_id":queue_id})
    return jsonify({"message": "No user in the queue"}), 404

#Return wash type
@app.route("/washtype")
def get_wash_type():
    user_id = request.args.get('user_id')
    laundqueue = LaundQueue.query.filter_by(user_id = user_id).first()
    wash_type = laundqueue.json()["service_type"]
    return jsonify({"wash type": wash_type})


#Return wash type, duration, cost
# Dequeue
@app.route("/serviceDequeue")
def service_details():
    user_id = request.args.get('user_id')
    location = request.args.get('location')
    cost = 0
    laundqueue = LaundQueue.query.filter_by(user_id = user_id, location = location).first()
    wash_type = laundqueue.json()["service_type"]
    if wash_type == "standard wash":
        cost = 5
    elif wash_type == "double wash":
        cost = 6
    elif wash_type == "hot wash":
        cost = 7

    if laundqueue:
        db.session.delete(laundqueue)
        db.session.commit()
        return jsonify({"user_id": user_id, "wash_type": wash_type,"duration":45, "cost":cost })

    return jsonify({"message": "Machine not found."}), 404

# # #Remove from Queue
# @app.route("/dequeue/<string:location>&<int:queue_id>")
# def remove_from_queue(location, queue_id):
#     laundqueue = LaundQueue.query.filter_by(location= location, queue_id= queue_id)
#     db.session.delete(laundqueue)
#     db.commit()


if __name__ == '__main__':
    app.run(port=5000, debug=True)
    

