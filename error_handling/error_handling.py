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
    sendMessage(json.loads(body))


def sendMessage(order):
    if order['errcodeid']:
        message = "Machine "+str(order['machineid']) + " at " + str(
            order['location']) + " is having this error: " + str(order['errcodeid'])
    else:
        message = "Machine " + \
            str(order['machineid']) + " at " + \
            str(order['location']) + " error resolved."
    return requests.post(
        "https://api.mailgun.net/v3/delaundro.me/messages",
        auth=("api", MAILGUNKEY),
        data={"from": "DeLaundro <do_not_reply@delaundro.me>",
              "to": ["admin@delaundro.me"],
              "subject": "Machine Error",
              "text":  message,
              "o:tracking": False})


if __name__ == '__main__':
    receiveError()
