from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import json
import pika
import requests

statusURL = "http://127.0.0.1:8002/status"

app = Flask(__name__)
dbURL = 'mysql+mysqlconnector://root@localhost:3306/queue'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/queue'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
 
db = SQLAlchemy(app)
 
class LaundQueue(db.Model):
    __tablename__ = 'queue'
 
    queue_id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(64), primary_key = True)
    user_id = db.Column(db.Integer, nullable=False)
    machine_id = db.Column(db.Integer, nullable=False)
    availability = db.Column(db.Boolean, nullable = False)
    service_type = db.Column(db.Integer, nullable = False)
    date_time = db.Column(db.DateTime, nullable =False)
 
    def __init__(self, queue_id, user_id, machine_id, location, availability, service_type, date_time):
        self.queue_id = queue_id
        self.user_id = user_id
        self.machine_id = machine_id
        self.location = location
        self.availability = availability
        self.service_type = service_type
        self.date_time = date_time


    def json(self):
        return {"queue_id": self.queue_id, "user_id": self.user_id, "machine_id":self.machine_id, "location":self.location, "availability": self.availability, 
        "service_type": self.service_type,"date_time":self.date_time}

        
 
engine = create_engine(dbURL)
if not database_exists(engine.url):
    create_database(engine.url)
db.create_all()
db.session.commit()

# Request available machine by location 
@app.route("/queue/<string:location>")
def get_avail_machine_id(location):
    results = LaundQueue.query.filter_by(location=location)
    if not results:
        queryURL = statusURL  + "/" + location + "&0"
        r = requests.get(queryURL)
        return r.text 
        # return jsonify(r.json())


@app.route("/queue/<string:user_id>&<string:location>", methods=['POST'])
def insert_queue(user_id, queue_id, location, date_time, service_type):
    code = 200
    result ={}
    #laundqueue = LaundQueue.query.filter_by(location=location, user_id = user_id).all()
    if(LaundQueue.query.filter_by(queue_id = queue_id, location = location).first()):
        code = 400
        result = {"code": code,"message": "Queue ID Already Exist"}
    data = request.get_json()
    laundqueue = LaundQueue.query.filter_by(location=location).all()
    # if(LaundQueue.query.filter_by(location=location).first()):
    #     last_queue_id = max([ o["queue_id"] for o in laundqueue["queue_id"] ])
    #     new_queue_id = last_queue_id+1
    try:
        db.session.add(laundqueue)
        db.session.commit()
    except:
        code = 500
        result = {"code": code,"message": "Error Updating Data"}
    if code == 200:
        result = status.json()
    send_status(result)
    return str(result), code




#add new service type
@app.route("/queue/<string:user_id>", methods=['POST'])
def add_new_service_request(user_id):
    user_id = LaundQueue.query.get(user_id)
    new_service_request = request.json["service_type"]

#Calculate and return waiting time
@app.route("/queue/<string:location>")
def insert_location(location):
    wait_time = 0
    if(LaundQueue.query.filter_by(location=location).first()):
        queue_length = LaundQueue.query.filter_by(location=location).count()
        wait_time += 45*queue_length
    return wait_time

        
# #Insert location
# # @app.route("/LaundQueue/<string:location>", methods=['POST'])
# # def insert_location(location):
# #     code = 200
# #     result ={}
# #     laundQueue = LaundQueue
# #     if location not in (LaundQueue.query.filter_by(location=location).all()):
# #         Queue = Queue.query.filter_by(location=location).first()

#Return list of Queues        
@app.route("/queue/<string:location>")
def laundqueue_list(location):
    laundqueue = LaundQueue.query.filter_by(
        location=location).all()
    if laundqueue:
        return jsonify({location+" queue": [laundqueue.json()for laundqueue in LaundQueue.query.filter_by(location=location).all()]})
    return jsonify({"message": "There is no queue in this location."}), 404

#Insert into Queue and return Queue length
@app.route("/queue/<string:location>&<string:user_id")



#Return next user, assigned machine
@app.route("/queue/<string:location>&<string:location>&<string:location>")
#Return wash type, duration, cost
@app.route("/Queue/<string:queue_id>")
laundqueue = LaundQueue.query.filter_by(queue_id= queue_id).first()
    if Queue:
        return jsonify({"queue_id": [Queue.json()for Queue in Queue.query.filter_by(queue_id=queue_id).all()]})
    return jsonify({"message": "Machine not found."}), 404

# #Remove from Queue
@app.route("/Queue/<string:location>&<int:queue_id>")
def remove_from_Queue(location, queue_id):
    laundqueue = LaundQueue.query.filter_by(location= location, queue_id= queue_id)
    db.session.delete(laundqueue)
    db.commit()


if __name__ == '__main__':
    app.run(port=5000, debug=True)
    

