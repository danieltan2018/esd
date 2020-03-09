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
    usagecount = db.Column(db.Integer)
    statuscode = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=True)
    curuser = db.Column(db.String(100), nullable=False)
    prevuser = db.Column(db.String(100), nullable=False)
    errcode = db.Column(db.String(100), nullable=False)
    unlockcode = db.Column(db.String(1000), nullable=False)
    startcode = db.Column(db.String(1000), nullable=False)
    
 
    def __init__(self, machineid, usagecount, statuscode, location, curuser, prevuser, errcode , unlockcode, startcode):
        self.machineid = machineid
        self.usagecount = usagecount
        self.statuscode = statuscode
        self.location = location
        self.curuser = curuser
        self.prevuser = prevuser
        self.errcode = errcode
        self.unlockcode = unlockcode
        self.startcode = startcode
 
    def json(self):
        return {"machineid": self.machineid, "usagecount": self.usagecount, "statuscode": self.statuscode, "location": self.location, "curuser": self.curuser, "prevuser": self.prevuser, "errcode": self.errcode, "unlockcode": self.unlockcode, "startcode": self.startcode}
    
    
@app.route("/status")
def get_available():
    return jsonify({"status": [status.json() for status in Status.query.all()]})

@app.route("/status/<string:location>&<string:statuscode>")
def find_by_location(location, statuscode):
    status= Status.query.filter_by(location=location, statuscode=statuscode).all()
    if status:
        return jsonify({"machineid":[status.json()for status in Status.query.filter_by(location=location,statuscode=statuscode).all()]})
    return jsonify({"message": "Location not found."}), 404


@app.route("/status/<string:machineid>")
def find_by_machineid(machineid):
    status= Status.query.filter_by(machineid=machineid).all()
    if status:
        return jsonify({"machineid":[status.json()for status in Status.query.filter_by(machineid=machineid).all()]})
    return jsonify({"message": "Machine not found."}), 404



@app.route("/status/<string:machineid>", methods=['PUT'])
def update_machine(machineid):
    status = Status.query.get(machineid)
    errcode = request.json["errcode"]
    statuscode = request.json["statuscode"]
    curuser = request.json["curuser"]
    startcode = request.json["startcode"]
    unlockcode = request.json["unlockcode"]
    
    
    status.errcode = errcode
    status.statuscode = statuscode
    status.curuser = curuser
    status.startcode = startcode
    status.unlockcode = unlockcode
    status.usagecount = status.usagecount + 1
    
    try:
        db.session.commit()
    except:
        return jsonify({"message": "Error Updating Data"}), 500
    
    return jsonify(status.json()), 201


@app.route("/status/<string:machineid>&<string:statuscode>", methods=['PUT'])
def update_machine_error(machineid,statuscode):
    status = Status.query.get(machineid)
    errcode = request.json["errcode"]
    statuscode = request.json["statuscode"]
 
    status.errcode = errcode
    status.statuscode = statuscode
  
    
    try:
        db.session.commit()
    except:
        return jsonify({"message": "Error Updating Data"}), 500
    
    return jsonify(status.json()), 201

    
if __name__ == '__main__':
    app.run(port=5000, debug=True)
    

