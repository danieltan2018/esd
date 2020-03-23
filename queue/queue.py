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
dbURL = 'mysql+mysqlconnector://root@localhost:3306/Queue'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/Queue'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
 
db = SQLAlchemy(app)
 
class Queue(db.Model):
    __tablename__ = 'Queue'
 
    Queue_id = db.Column(db.String(13), primary_key=True)
    location = db.Column(db.String(64), primary_key = True)
    user_id = db.Column(db.Integer, nullable=False)
    machine_id = db.Column(db.Integer, nullable=False)
    availability = db.Column(db.Boolean, nullable = False)
    service_type = db.Column(db.Integer, nullable = False)
    date_time = db.Column(db.DateTime, nullable =False)
 
    def __init__(self, Queue_id, user_id, machine_id, location, availability, service_type, date_time):
        self.Queue_id = Queue_id
        self.user_id = user_id
        self.machine_id = machine_id
        self.location = location
        self.availability = availability
        self.service_type = service_type
        self.date_time = date_time


    def json(self):
        return {"Queue_id": self.Queue_id, "user_id": self.user_id, "machine_id":self.machine_id, "location":self.location, "availability": self.availability, 
        "service_type": self.service_type,"date_time":self.date_time}
 
engine = create_engine(dbURL)
if not database_exists(engine.url):
    create_database(engine.url)
db.create_all()
db.session.commit()

# Request available machine by location 
@app.route("/queue/<string:location>")
def get_avail_machine_id(location):
    # return ("HELLO BITCH")
    queryURL = statusURL  + "/" + location + "&0"
    r = requests.get(queryURL)
    return json.loads(r)
    print(r.text)
    # return jsonify(r.json())



# @app.route("/Queue")
# def get_all():
#     return jsonify({"Queue": [Queue.json() for Queue in Queue.query.all()]})

# #(If no existing Queue) Request for available machines for location
# @app.route("/Queue/<string:location>")
# def get_avail_machine_id(location):
#     results = Queue.query.filter_by(location=location)
#     if not results:
#     #availID = ##
#         queryURL = statusURL  + "/" + location + "&" + 0
#         r = requests.get(queryURL)
#         return jsonify(r.json())
#     return jsonify(results.json())
#     # filter out machine ids only
#     # return above

#     #result = json.loads(r.text.lower())
#         # check/print shipping's result


# # @app.route("/Queue/<string:user_id>&<string:location>", methods=['POST'])
# # def create_Queue_id(user_id,location):
# #     user_id= Queue.query.filter_by(user_id=user_id)
# #     location = Queue.query.get(user_id)
# #     Queue_id = request.json["Queue_id"]

# @app.route("/Queue/<string:user_id>", methods=['POST'])
# def add_new_service_request(user_id):
#     user_id = Queue.query.get(user_id)
#     new_service_request = request.json["service_type"]

# #Calculate and return waiting time
# @app.route("/Queue/<string:location>")
# def insert_location(location):
#     code = 200
#     result ={}
#     Queue = Queue
#     if(Queue.query.filter_by(location=location).first()):
#         Queue = Queue.query.filter_by(location=location).first()
#         count = cursor.execute("select count(*) from Queue")  
#         cursor.commit
#         wait_time = 45*count
#     return wait_time
        
# #Insert location
# @app.route("/Queue/<string:location>", methods=['PUT'])
# def insert_location(location):
#     code = 200
#     result ={}
#     Queue = Queue
#     if(Queue.query.filter_by(location=location).first()):
#         Queue = Queue.query.filter_by(location=location).first()

# #Return list of Queues        
# @app.route("/status/<string:location>&<int:statuscodeid>")
# def Queue_list(location, statuscodeid):
#     status = Status.query.filter_by(
#         location=location, statuscodeid=statuscodeid).all()
#     if status:
#         return jsonify({"machineid": [status.json()for status in Status.query.filter_by(location=location, statuscodeid=statuscodeid).all()]})
#     return jsonify({"message": "Location not found."}), 404

# #Insert into Queue and return Queue length


# #Return next user, assigned machine


# #Return wash type, duration, cost
# @app.route("/Queue/<string:Queue_id>")
#     Queue = Queue.query.filter_by(Queue_id= Queue_id).first()
#     if Queue:
#         return jsonify({"Queue_id": [Queue.json()for Queue in Queue.query.filter_by(Queue_id=Queue_id).all()]})
#     return jsonify({"message": "Machine not found."}), 404

# #Remove from Queue
# @app.route("/Queue/<string:user_id>")
# def remove_from_Queue(user_id):
#     mycursor = db.cursor()
#     query = "DELETE FROM Queue WHERE user_id = "
#     mycursor.execute(query)
#     db.commit()


if __name__ == '__main__':
    app.run(port=5000, debug=True)
    

