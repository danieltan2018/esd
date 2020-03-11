from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import json
from datetime import datetime

app = Flask(__name__)
dbURL = 'mysql+mysqlconnector://root@localhost:3306/monitoring'
app.config['SQLALCHEMY_DATABASE_URI'] = dbURL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)


class Monitoring(db.Model):
    __tablename__ = 'monitoring'

    m_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    location = db.Column(db.String, nullable=False)
    machine_id = db.Column(db.Integer, nullable=False)
    m_status = db.Column(db.String, nullable=False)  # on,off,unavailable
    # machine spoil, no detergent etc
    error = db.Column(db.String, nullable=False)
    payment = db.Column(db.String)  # incomplete, complete
    datetime_now = db.Column(db.DateTime, default=datetime.now)

    def __init__(m_id, location, machine_id, datetime_now, status, error, payment):
        self.m_id = m_id
        self.location = location
        self.machine_id = machine_id
        self.datetime_now = datetime_now
        self.m_status = m_status
        self.error = error
        self.payment = payment

    def json(self):
        return {"m_id": self.m_id, "location": self.location, "machine_id": self.machine_id, "status_m": self.m_status, "error": self.error, "payment": self.payment, "datetime_now": self.datetime_now}


engine = create_engine(dbURL)
if not database_exists(engine.url):
    create_database(engine.url)
db.create_all()
db.session.commit()


@app.route("/monitoring")
def get_all():
    return {'monitoring': [monitoring.json() for monitoring in Monitoring.query.all()]}


if __name__ == '__main__':
    app.run(port=8003, debug=True)
