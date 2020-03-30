from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import json
import pika
import uuid

app = Flask(__name__)
# dbURL = 'mysql+mysqlconnector://root@localhost:3306/status'
dbURL = 'mysql+mysqlconnector://root@db:3306/status'
app.config['SQLALCHEMY_DATABASE_URI'] = dbURL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)


class Status(db.Model):
    __tablename__ = 'status'

    machineid = db.Column(db.Integer, primary_key=True)
    statuscodeid = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(100), primary_key=True)
    curuser = db.Column(db.Integer, nullable=True)
    prevuser = db.Column(db.Integer, nullable=True)
    errcodeid = db.Column(db.Integer, nullable=False)
    unlockcode = db.Column(db.String(1000), nullable=True)
    startcode = db.Column(db.String(1000), nullable=True)

    def __init__(self, machineid, statuscodeid, location, curuser, prevuser, errcodeid, unlockcode, startcode):
        self.machineid = machineid
        self.statuscodeid = statuscodeid
        self.location = location
        self.curuser = curuser
        self.prevuser = prevuser
        self.errcodeid = errcodeid
        self.unlockcode = unlockcode
        self.startcode = startcode

    def json(self):
        return {"machineid": self.machineid, "statuscodeid": self.statuscodeid, "location": self.location, "curuser": self.curuser, "prevuser": self.prevuser, "errcodeid": self.errcodeid, "unlockcode": self.unlockcode, "startcode": self.startcode}


engine = create_engine(dbURL)
if not database_exists(engine.url):
    create_database(engine.url)
db.create_all()
db.session.commit()

@app.route("/")
def get_available():
    return jsonify({"status": [status.json() for status in Status.query.all()]})


@app.route("/countMachine")
def count_by_location():
    location = request.args.get('location')
    status_all = Status.query.filter_by(location=location).all()
    totalMachine = len(status_all)
    status_unavailable = Status.query.filter_by(location=location, errcodeid=0).all()
    unavailMachine = len(status_unavailable)
    status_available = Status.query.filter_by(location=location, errcodeid=1).all()
    availMachine = len(status_available)
    status_down = Status.query.filter_by(location=location, errcodeid=2).all()
    downMachine = len(status_down)
    totallessbroken = (unavailMachine+availMachine)
    if status_all:
        
        
        return jsonify({"locationtotalmachine":totalMachine, "numberofdown":downMachine, "availandunavail":totallessbroken})
    return jsonify({"message": "Error Finding Machine."}), 404


@app.route("/findAvailMachine")
def find_by_location():
    location = request.args.get('location')
    statuscodeid = request.args.get('statuscodeid')
    status = Status.query.filter_by(location=location, statuscodeid=statuscodeid).all()
    if status:
        return jsonify({"machineid": [status.json()for status in Status.query.filter_by(location=location, statuscodeid=statuscodeid).all()]})
    return jsonify({"message": "Location not found."}), 404


@app.route("/findMachine")
def find_by_machineid():
    machineid = request.args.get('machineid')
    status = Status.query.filter_by(machineid=machineid).all()
    if status:
        return jsonify({"machineid": [status.json()for status in Status.query.filter_by(machineid=machineid).all()]})
    return jsonify({"message": "Machine not found."}), 404


@app.route("/getUnlockCode")
def find_unlock_code():
    unlockcode = request.args.get('unlockcode')
    machineid = request.args.get('machineid')
    location = request.args.get('location')
    status = Status.query.filter_by(location=location, machineid= machineid,unlockcode=unlockcode).first()
    
    if status:
        status_info =status.json()
        return jsonify({"userid": status_info['prevuser']})
    return jsonify({"message": "Unlock Code Invalid."}), 404


@app.route("/getStartCode")
def find_start_code():
    startcode = request.args.get('startcode')
    machineid = request.args.get('machineid')
    location = request.args.get('location')
    status = Status.query.filter_by(location=location, machineid=machineid, startcode=startcode).first()
    
    if status:
        status_info =status.json()
        return jsonify({"userid": status_info['curuser']})
    return jsonify({"message": "Start Code Invalid."}), 404


@app.route("/getQRCode")
def find_QR_code():
    machineid = request.args.get('machineid')
    location = request.args.get('location')
    status = Status.query.filter_by(location=location, machineid=machineid).first()
    
    if status:
        status_info =status.json()
        return jsonify({"unlockcode": status_info['unlockcode'], "startcode":status_info['startcode']})
    return jsonify({"message": "No Code valid."}), 404


@app.route("/findLocation")
def get_location():
    location = request.args.get('location')
    return_location = []
    for status in Status.query.all():
        status_container = status.json()
        if status_container['location'] not in return_location:
            return_location.append(status_container['location'])
    return jsonify({"Location": return_location})


@app.route("/updateMachineError", methods=['PUT'])
def update_machine_Error():
    machineid = request.args.get('machineid')
    location = request.args.get('location')
    code = 200
    result = {}
    if(Status.query.filter_by(machineid=machineid, location=location).first()):
        status = Status.query.filter_by(
            machineid=machineid, location=location).first()
        
        errcodeid = request.json["errcodeid"]
        status.errcodeid = errcodeid
        status.statuscodeid = 2


    else:
        code = 400
        result = {"code": code, "message": "No such Data"}
    try:
        db.session.commit()
    except:
        code = 500
        result = {"code": code, "message": "Error Updating Data"}

    if code == 200:
        if errcodeid == 0:
            status.errcodeid = "none"
        elif errcodeid == 1:
            status.errcodeid = "Low on Detergent"
        elif errcodeid == 2:
            status.errcodeid = "Machine is Down"
        elif errcodeid == 3:
            status.errcodeid = "Water is Low"
        else:
            status.errcodeid = "Error Unknown Call Tier 3 Support"
        result = status.json()
    send_status(result)
    return str(result), code


@app.route("/updateMachineUser", methods=['PUT'])
def update_machine_User():
    machineid = request.args.get('machineid')
    location = request.args.get('location')
    code = 200
    result = {}
    if(Status.query.filter_by(machineid=machineid, location=location, errcodeid=0).first()):
        status = Status.query.filter_by(machineid=machineid, location=location).first()
        #curuser = request.json["curuser"]
        #status.curuser = curuser
        if request.json["curuser"] == status.curuser:
            code = 400
            result = {"code": code, "message": "Duplicate Userid"}
        else:
            #if request.json["curuser"]:
            #    status.curuser = request.json["curuser"]
            #    startcode = uuid.uuid4()
            #    status.startcode = startcode.hex
            #if status.curuser == None:
            #    prevuser = status.curuser
            #    status.prevuser = prevuser
            #    status.unlockcode = status.startcode
            if status.curuser == None:
                status.curuser = request.json["curuser"]
                startcode = uuid.uuid4()
                status.startcode = startcode.hex
            elif status.curuser != None:
                prevuser = status.curuser
                prevusercode = status.startcode
                status.curuser = request.json["curuser"]
                startcode = uuid.uuid4()
                status.startcode = startcode.hex
                status.prevuser = prevuser
                status.unlockcode = prevusercode
                         
    else:
        code = 400
        result = {"code": code, "message": "No such Machine"}
    try:
        db.session.commit()
    except:
        code = 500
        result = {"code": code, "message": "Error Updating Data"}

    if code == 200:
        result = status.json()
    send_status(result)
    return str(result), code


@app.route("/createMachine", methods=['POST'])
def create_machine():
    machineid = request.args.get('machineid')
    location = request.args.get('location')
    code = 200
    result = {}
    if (Status.query.filter_by(machineid=machineid, location=location).first()):
        code = 400
        result = {"code": code, "message": "Machine Already Exist"}
    data = {"machineid":machineid, "location": location, "statuscodeid":1, "curuser": None, "prevuser":None, "errcodeid":0, "unlockcode":None, "startcode":None}
    status = Status(**data)
    try:
        db.session.add(status)
        db.session.commit()
    except:
        code = 500
        result = {"code": code, "message": "Error Updating Data"}
    if code == 200:
        result = status.json()
    send_status(result)
    return str(result), code





@app.route("/updateMachineToInUse", methods=['PUT'])
def update_machine_In_Use():
    machineid = request.args.get('machineid')
    location = request.args.get('location')
    code = 200
    result = {}
    if(Status.query.filter_by(machineid=machineid, location=location).first()):
        status = Status.query.filter_by(
            machineid=machineid, location=location).first()
        
    
        status.statuscodeid = 1
        

    else:
        code = 400
        result = {"code": code, "message": "No such Data"}
    try:
        db.session.commit()
    except:
        code = 500
        result = {"code": code, "message": "Error Updating Data"}

    if code == 200:
        result = status.json()
    send_status(result)
    return str(result), code





def send_status(status):
    # Inform Monitoring and Error Handling
    hostname = "rabbit.delaundro.me"
    port = 5672
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=hostname, port=port))
    channel = connection.channel()
    exchangename = "laundro_topic"
    channel.exchange_declare(exchange=exchangename, exchange_type='topic')
    message = json.dumps(status, default=str)

    if "code" in status:
        # inform Error
        channel.queue_declare(queue='errorhandler', durable=True)
        channel.queue_bind(exchange=exchangename,
                           queue='errorhandler', routing_key='*.error')
        channel.basic_publish(exchange=exchangename, routing_key="machine.error",
                              body=message, properties=pika.BasicProperties(delivery_mode=2))
    elif status["errcodeid"] != 'none':
        # inform Error
        channel.queue_declare(queue='errorhandler', durable=True)
        channel.queue_bind(exchange=exchangename,
                           queue='errorhandler', routing_key='*.error')
        channel.basic_publish(exchange=exchangename, routing_key="machine.error",
                              body=message, properties=pika.BasicProperties(delivery_mode=2))
    else:
        # inform shipping
        channel.queue_declare(queue='monitoring', durable=True)
        channel.queue_bind(exchange=exchangename,
                           queue='monitoring', routing_key='*.status')
        channel.basic_publish(exchange=exchangename, routing_key="machine.status",
                              body=message, properties=pika.BasicProperties(delivery_mode=2))
    connection.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002, threaded=True)
    # app.run(port=8002, threaded=True)
