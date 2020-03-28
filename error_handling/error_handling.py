import json
import sys
import os
import pika

MAILGUNKEY = os.getenv('MAILGUNKEY')

hostname = "rabbit.delaundro.me"
port = 5672
connection = pika.BlockingConnection(pika.ConnectionParameters(host=hostname, port=port))
channel = connection.channel()
exchangename = "laundro_topic"
channel.exchange_declare(exchange=exchangename, exchange_type='topic')

def receiveError():
    # prepare a queue for receiving messages
    channelqueue = channel.queue_declare(queue="errorhandler", durable=True) # 'durable' makes the queue survive broker restarts
    queue_name = channelqueue.method.queue
    channel.queue_bind(exchange=exchangename, queue="queue_name", routing_key='*.error') 

    # set up a consumer and start to wait for coming messages
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming() 

def callback(channel, method, properties, body): # required signature for the callback; no return
    print("Received an error by " + __file__)
    processError(json.loads(body))
    sendMessage(json.loads(body))
    print()

def processError(order):
    print("Recording an error:")
    print(order)

def sendMessage(order):
    return requests.post(
        "https://api.mailgun.net/v3/delaundro.me/messages",
        auth=("api", MAILGUNKEY),
        data={"from": "DeLaundro <do_not_reply@delaundro.me>",
              "to": ["admin@delaundro.me"],
              "subject": "Machine Error",
              "text": "Error: ".order." observed, please fix asap",
              "o:tracking": False})

if __name__ == "__main__":  # execute this program only if it is run as a script (not by 'import')
    print("This is " + os.path.basename(__file__) + ": recording an error...")