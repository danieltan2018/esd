from flask import Flask, request, jsonify
from flask_cors import  CORS
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/book'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
 
db = SQLAlchemy(app)
 
class Queue(db.Model):
    __tablename__ = 'queue'
 
    queue_id = db.Column(db.String(13), primary_key=True)
    location = db.Column(db.Varchar(64), primary_key = True)
    user_id = db.Column(db.Integer(13), nullable=False)
    machine_id = db.Column(db.Integer(13), nullable=False)
    availability = db.Column(db.Boolean, nullable = False)
    service_type = db.Column(db.Integer, nullable = False)
    date_time = db.Column(db.Timestamp, nullabe=False)
 
    def __init__(self, queue_id, user_id, location, availability, service_type, date_time):
        self.queue_id = queue_id
        self.user_id = user_id
        self.machine_id = machine_id
        self.location=location
        self.availability = availability
        self.service_type= service_type
        self.date_time= date_time

 
    def json(self):
        return {"queue_id": self.queue_id, "user_id": self.user_id, "": self.price, "availability": self.availability}
 
@app.route("/queue")
def get_all():
    return jsonify({"queue": [queue.json() for queue in Queue.query.all()]})
 
@app.route("/queue/<string:user_id>&<string:location>", methods=['POST'])
def create_queue_id(user_id):
    user_id= Queue.query.get(user_id)
    location = Queue.query.get(user_id)
    queue_id = request.json["queue_id"]
    
@app.route("/queue/<string:user_id>", methods=['POST'])
def add_new_service_request(user_id):
    user_id = Queue.query.get(user_id)
    new_service_request = request.json["service_type"]



if __name__ == '__main__':
    app.run(port=5000, debug=True)
    
