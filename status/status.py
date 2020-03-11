from flask import Flask, request, jsonify
from flask_cors import  CORS
from flask_sqlalchemy import SQLAlchemy
import json



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/status'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
 
db = SQLAlchemy(app)
CORS(app) 


class Status(db.Model):
    __tablename__ = 'status'
 
    machineid = db.Column(db.String(100), primary_key=True)
    statuscodeid = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=True)
    curuser = db.Column(db.String(100), nullable=False)
    prevuser = db.Column(db.String(100), nullable=False)
    errcodeid = db.Column(db.String(100), nullable=False)
    unlockcode = db.Column(db.String(1000), nullable=False)
    startcode = db.Column(db.String(1000), nullable=False)
    
 
    def __init__(self, machineid, statuscodeid, location, curuser, prevuser, errcodeid , unlockcode, startcode):
        self.machineid = machineid
        self.statuscodeid = statuscodeid
        self.location = location
        self.curuser = curuser
        self.prevuser = prevuser
        self.errcodeid = errcodeid
        self.unlockcode = unlockcode
        self.startcode = startcode
 
    def json(self):
        return {"machineid": self.machineid, "statuscodeid": self.statuscodeidid, "location": self.location, "curuser": self.curuser, "prevuser": self.prevuser, "errcodeid": self.errcodeid, "unlockcode": self.unlockcode, "startcode": self.startcode}
    
    
@app.route("/status")
def get_available():
    return jsonify({"status": [status.json() for status in Status.query.all()]})

@app.route("/status/<string:location>&<string:statuscodeidid>")
def find_by_location(location, statuscodeidid):
    status= Status.query.filter_by(location=location, statuscodeidid=statuscodeidid).all()
    if status:
        return jsonify({"machineid":[status.json()for status in Status.query.filter_by(location=location,statuscodeidid=statuscodeidid).all()]})
    return jsonify({"message": "Location not found."}), 404


@app.route("/status/<string:machineid>")
def find_by_machineid(machineid):
    status= Status.query.filter_by(machineid=machineid).all()
    if status:
        return jsonify({"machineid":[status.json()for status in Status.query.filter_by(machineid=machineid).all()]})
    return jsonify({"message": "Machine not found."}), 404


@app.route("/status/<string:machineid>&<string:location>", methods=['PUT'])
def update_machine(machineid,location):
    status = Status.query.get(machineid,location)
    errcodeid = request.json["errcodeid"]
    statuscodeidid = request.json["statuscodeid"]
    curuser = request.json["curuser"]
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


@app.route("/status/<string:machineid>&<string:statuscodeid>", methods=['PUT'])
def update_machine_error(machineid,statuscodeid):
    status = Status.query.get(machineid)
    errcodeid = request.json["errcodeid"]
    statuscodeid = request.json["statuscodeid"]
 
    status.errcodeid = errcodeid
    status.statuscodeid = statuscodeid
  
    
    try:
        db.session.commit()
    except:
        return jsonify({"message": "Error Updating Data"}), 500
    
    return jsonify(status.json()), 201

    
if __name__ == '__main__':
    app.run(port=5000, debug=True)
    

