from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import json
from datetime import date
import datetime

app = Flask(__name__)
dbURL = 'mysql+mysqlconnector://root@localhost:3306/monitoring'
app.config['SQLALCHEMY_DATABASE_URI'] = dbURL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)

class Monitoring(db.Model):
    tablename = 'monitoring'

    m_id = db.Column(db.Integer, primary_key=True, autoincrement=True) #primary key finder
    machineid = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100), primary_key=True)
    statuscodeid = db.Column(db.Integer, nullable=False)
    errcodeid = db.Column(db.Integer, nullable=False)
    payment = db.Column(db.Integer, nullable=False)
    date_time = db.Column(db.String(100), nullable =False)

    def init(self, m_id, machineid, location, statuscodeid, errcodeid, payment, date_time):
        self.m_id = m_id
        self.machineid = machineid
        self.location = location
        self.statuscodeid = statuscodeid
        self.errcodeid = errcodeid
        self.payment = payment
        self.date_time = date_time

    def json(self):
        return {"m_id": self.m_id, "machineid": self.machineid, "location": self.location, "statuscodeid": self.statuscodeid, "errcodeid": self.errcodeid, "payment": self.payment, "date_time": self.date_time}

engine = create_engine(dbURL)
if not database_exists(engine.url):
    create_database(engine.url)
db.create_all()
db.session.commit()

# Return all the monitoring information 
@app.route("/monitoring")
def get_all():
    return {'monitoring': [monitoring.json() for monitoring in Monitoring.query.all()]}

# Log machine statuses 
@app.route("/monitoring/add",methods=['POST'])
def insert_log():
    code = 200
    result = {}
    data = request.get_json()
    monitoring = Monitoring(**data)
    print(monitoring)
    try:
        db.session.add(monitoring)
        db.session.commit()
    except:
        code = 500
        result = {"code": code, "message": "Error Updating Data"}
    if code == 200:
        result = monitoring.json()
    return str(result), code


if __name__ == '__main__':
    app.run(port=8003, debug=True)
