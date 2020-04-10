import json
import sys
import os
import pika
import requests

MAILGUNKEY = os.getenv('MAILGUNKEY')

hostname = "rabbit.delaundro.me"
port = 5672
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=hostname, port=port))
channel = connection.channel()
exchangename = "laundro_topic"
channel.exchange_declare(exchange=exchangename, exchange_type='topic')


def receiveError():
    channelqueue = channel.queue_declare(queue="errorhandler", durable=True)
    queue_name = channelqueue.method.queue
    channel.queue_bind(exchange=exchangename,
                       queue=queue_name, routing_key='*.error')
    channel.basic_consume(
        queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()


# required signature for the callback; no return
def callback(channel, method, properties, body):
    print("Received an error by " + __file__)
    processError(json.loads(body))
    sendMessage(json.loads(body))
    print()


def processError(order):
    print("Recording an error:")
    print(order)


def sendMessage(order):
    message = "Machine:"+str(order['machineid']) + " at " + str(
        order['location']) + " having this error " + str(order['errcodeid'])
    print(message)
    return requests.post(
        "https://api.mailgun.net/v3/delaundro.me/messages",
        auth=("api", MAILGUNKEY),
        data={"from": "DeLaundro <do_not_reply@delaundro.me>",
              "to": ["admin@delaundro.me"],
              "subject": "Machine Error",
              "text":  message,
              "o:tracking": False})


if __name__ == '__main__':
    print("This is " + os.path.basename(__file__) +
          ": processing an order error...")
    receiveError()
