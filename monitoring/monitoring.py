from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import json
from datetime import datetime
import sys
import os
import pika
import threading

app = Flask(__name__)
dbURL = 'mysql+mysqlconnector://root@db:3306/monitoring'
app.config['SQLALCHEMY_DATABASE_URI'] = dbURL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)


class Monitoring(db.Model):
    tablename = 'monitoring'

    m_id = db.Column(db.Integer, primary_key=True,
                     autoincrement=True)  # primary key finder
    machineid = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100), primary_key=True)
    statuscodeid = db.Column(db.Integer, nullable=False)
    errcodeid = db.Column(db.String(100), nullable=False)
    payment = db.Column(db.Integer, nullable=True)
    date_time = db.Column(db.String(100), nullable=True)

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
@app.route("/")
def get_all():
    return {'monitoring': [monitoring.json() for monitoring in Monitoring.query.all()]}


def receiveOrderLog():
    hostname = "rabbit.delaundro.me"
    port = 5672
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=hostname, port=port))
    channel = connection.channel()
    exchangename = "laundro_topic"
    channel.exchange_declare(exchange=exchangename, exchange_type='topic')
    channelqueue = channel.queue_declare(queue="", exclusive=True)
    queue_name = channelqueue.method.queue
    channel.queue_bind(exchange=exchangename,queue=queue_name, routing_key='#')
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()


def callback(channel, method, properties, body):
    insert_log(json.loads(body))


def insert_log(order):
    location = order['location']
    machineid = order['machineid']
    statuscodeid = order['statuscodeid']
    errcodeid = order['errcodeid']
    now = datetime.now()
    data = {"m_id": None, "machineid": machineid, "location": location,
            "statuscodeid": statuscodeid, "errcodeid": errcodeid, "payment": None, "date_time": now}
    monitoring = Monitoring(**data)
    db.session.add(monitoring)
    db.session.commit()



if __name__ == '__main__':
    thread = threading.Thread(target=receiveOrderLog, daemon=True)
    thread.start()
    app.run(host='0.0.0.0', port=80, threaded=True)
