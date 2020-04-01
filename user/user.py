import os
import requests
import telegram
import telegram.bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (Updater, CommandHandler, MessageHandler,
                          Filters, PreCheckoutQueryHandler, CallbackQueryHandler)
from telegram.ext.dispatcher import run_async
import pika
import json

import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

BOTTOKEN = os.getenv('BOTTOKEN')
PORT = 88
bot = telegram.Bot(token=BOTTOKEN)

ip = requests.get('https://api.ipify.org').text
try:
    certfile = open("cert.pem")
    keyfile = open("private.key")
    certfile.close()
    keyfile.close()
except IOError:
    from OpenSSL import crypto
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)
    cert = crypto.X509()
    cert.get_subject().CN = ip
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10*365*24*60*60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha256')
    with open("cert.pem", "wt") as certfile:
        certfile.write(crypto.dump_certificate(
            crypto.FILETYPE_PEM, cert).decode('ascii'))
    with open("private.key", "wt") as keyfile:
        keyfile.write(crypto.dump_privatekey(
            crypto.FILETYPE_PEM, key).decode('ascii'))

hostname = "rabbit.delaundro.me"
port = 5672
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=hostname, port=port))
channel = connection.channel()
exchangename = "laundro_topic"
channel.exchange_declare(exchange=exchangename, exchange_type='topic')

WASHTYPES = {"Standard Wash": 5, "Double Wash": 6, "Hot Wash": 7}
STATUSURL = 'http://status.delaundro.me/'
QUEUEURL = 'http://queue.delaundro.me/'
pendingusers = {}


@run_async
def startamqp():
    channelqueue = channel.queue_declare(queue='', durable=True)
    queue_name = channelqueue.method.queue
    channel.queue_bind(exchange=exchangename,
                       queue=queue_name, routing_key='*.status')
    channel.basic_consume(
        queue=queue_name, on_message_callback=amqpcallback, auto_ack=True)
    channel.start_consuming()


@run_async
def amqpcallback(channel, method, properties, body):
    status = json.loads(body)
    print(status)
    statuscode = status['statuscodeid']
    id = status['curuser']
    if statuscode == 1:
        send(id, "*Your wash has started!*\nWe will notify you when it's done.", [])
    elif statuscode == 0:
        send(id, "*Wash Complete!*\nPlease collect your laundry within 15 minutes.", [])
        send(
            id, "Thank you for choosing DE'Laundro. To start another wash, [click here](https://t.me/delaundrobot?start=delaundro).", [])
        location = status['location']
        machine_id = status['machineid']
        params = {'location': location}
        url = QUEUEURL + 'nextuser'
        nextuser = requests.get(url=url, params=params)
        if nextuser.status_code == 200:
            nextuser = nextuser.json()
            newwash(nextuser['user_id'], nextuser['queue_id'],
                    location, machine_id)


@run_async
def paymentamqp(message):
    message = json.dumps(message, default=str)
    channel.queue_declare(queue='monitoring', durable=True)
    channel.queue_bind(exchange=exchangename,
                       queue='monitoring', routing_key='#')
    channel.basic_publish(exchange=exchangename, routing_key="payment.info",
                          body=message, properties=pika.BasicProperties(delivery_mode=2))


@run_async
def send(id, msg, keyboard):
    keyboard = InlineKeyboardMarkup(keyboard)
    bot.send_message(
        chat_id=id, reply_markup=keyboard, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)
    return


@run_async
def start(update, context):
    id = update.message.chat_id
    deeplink = ''.join(context.args)
    if deeplink == 'delaundro':
        welcome(update, context)
    else:
        send(id, "_Please visit our website to start the bot._", [])
    return


@run_async
def callbackquery(update, context):
    query = update.callback_query
    data = query.data
    if data.startswith('LOCATION='):
        selectqueue(update, context)
    elif data.startswith('JOINQUEUE='):
        joinqueue(update, context)
    elif data == ('CANCELQUEUE'):
        cancelqueue(update, context)
    elif data.startswith('WASHTYPE='):
        dopayment(update, context)


@run_async
def welcome(update, context):
    id = update.message.chat_id
    send(id, "*Welcome to DE’Laundro!*", [])
    selectlocation(id, update, context)
    return


@run_async
def selectlocation(id, update, context):
    try:
        url = STATUSURL + 'findLocation'
        locations = requests.get(url).json()['Location']
    except:
        send(id, "_Sorry, we are having trouble connecting to our Status system._", [])
        return
    msg = "Select a location to wash laundry:"
    keyboard = []
    for location in locations:
        keyboard.append([InlineKeyboardButton(
            location, callback_data='LOCATION={}'.format(location))])
    send(id, msg, keyboard)
    return


@run_async
def selectqueue(update, context):
    query = update.callback_query
    data = query.data
    data = data.replace('LOCATION=', '')
    try:
        params = {'location': data}
        url = QUEUEURL + 'calculateWaitTime'
        waitingtime = requests.get(url=url, params=params).text
    except:
        context.bot.answer_callback_query(
            query.id, text="Sorry, we are having trouble connecting to our Queue system.", show_alert=True)
        return
    msg = "Estimated waiting time at <b>{}</b> is <u>{} minutes</u>. Would you like to join the queue?".format(
        data, waitingtime)
    keyboard = [
        [InlineKeyboardButton(
            "Yes", callback_data='JOINQUEUE={}'.format(data))],
        [InlineKeyboardButton(
            "No", callback_data='CANCELQUEUE')]
    ]
    keyboard = InlineKeyboardMarkup(keyboard)
    context.bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=msg,
        reply_markup=keyboard,
        parse_mode=telegram.ParseMode.HTML
    )
    context.bot.answer_callback_query(query.id)
    return


@run_async
def joinqueue(update, context):
    query = update.callback_query
    data = query.data
    data = data.replace('JOINQUEUE=', '')
    chat_id = query.message.chat_id
    try:
        params = {'location': data, 'statuscodeid': 0}
        url = STATUSURL + 'findAvailMachine'
        machines = requests.get(url=url, params=params)
        if machines.status_code == 200:
            machine_id = machines.json()['machineid'][0]['machineid']
            msg = "It's your turn!"
            queue = False
        else:
            msg = "You are in the queue!"
            queue = True
    except:
        context.bot.answer_callback_query(
            query.id, text="Sorry, we are having trouble connecting to our Status system.", show_alert=True)
        return
    try:
        params = {'location': data, 'user_id': chat_id}
        url = QUEUEURL + 'newqueue'
        requests.post(url=url, params=params)
        context.bot.answer_callback_query(
            query.id, text="There is no queue. You will be assigned the first available machine.", show_alert=True)
        if queue:
            params = {'location': data}
            url = QUEUEURL + 'queuelist'
            queuelist = requests.get(url=url, params=params)
            if queuelist.status_code == 200:
                queuelength = len(queuelist.json()['queue'])
            else:
                queuelength = 0
            context.bot.answer_callback_query(
                query.id, text="There are {} people ahead of you. We will notify you when it's your turn.".format(queuelength), show_alert=True)
        else:
            params = {'location': data}
            url = QUEUEURL + 'nextuser'
            nextuser = requests.get(url=url, params=params)
            if nextuser.status_code == 200:
                nextuser = nextuser.json()
                newwash(nextuser['user_id'],
                        nextuser['queue_id'], data, machine_id)
    except:
        context.bot.answer_callback_query(
            query.id, text="Sorry, we are having trouble connecting to our Queue system.", show_alert=True)
        return
    context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=query.message.message_id,
        text=msg,
        parse_mode=telegram.ParseMode.MARKDOWN
    )
    return


@run_async
def cancelqueue(update, context):
    query = update.callback_query
    id = query.message.chat_id
    context.bot.delete_message(chat_id=id, message_id=query.message.message_id)
    selectlocation(id, update, context)
    context.bot.answer_callback_query(query.id)
    return


@run_async
def newwash(user_id, queue_id, location, machine_id):
    try:
        params = {'location': location,
                  'machineid': machine_id, 'curuser': user_id}
        url = STATUSURL + 'updateMachineUser'
        requests.put(url=url, params=params)
    except:
        send(id, "_Sorry, we are having trouble connecting to our Status system._", [])
        return
    global pendingusers
    pendingusers[user_id] = {'queue': queue_id,
                             'location': location, 'machine': machine_id}
    msg = "Select a wash type:"
    keyboard = []
    for washtype in WASHTYPES:
        keyboard.append([InlineKeyboardButton(
            washtype, callback_data='WASHTYPE={}'.format(washtype))])
    send(id, msg, keyboard)
    return


@run_async
def dopayment(update, context):
    query = update.callback_query
    data = query.data
    data = data.replace('WASHTYPE=', '')
    washtype = data
    id = query.message.chat_id
    try:
        params = {'user_id': id, 'queue_id': pendingusers[id]['queue'],
                  'machine_id': machine_id, 'wash_type': washtype}
        url = QUEUEURL + 'allocateMachine'
        requests.post(url=url, params=params)
    except:
        send(id, "_Sorry, we are having trouble connecting to our Queue system._", [])
        return
    context.bot.delete_message(chat_id=id, message_id=query.message.message_id)
    context.bot.answer_callback_query(query.id)
    price = WASHTYPES[washtype]
    title = "DE'Laundro Payment"
    description = "Bill for {}:".format(washtype)
    payload = "delaundro-pay"
    provider_token = os.getenv('STRIPETOKEN')
    start_parameter = "pay"
    currency = "SGD"
    prices = [LabeledPrice(washtype, price*100)]
    context.bot.send_invoice(id, title, description, payload,
                             provider_token, start_parameter, currency, prices)
    send(id, '_Stripe Payments running in TEST mode._\n\nUse card number `4000 0070 2000 0003` with any future expiry date and CVV.', [])
    return


@run_async
def precheckout(update, context):
    query = update.pre_checkout_query
    if query.invoice_payload != 'delaundro-pay':
        query.answer(ok=False, error_message="Something went wrong...")
    else:
        query.answer(ok=True)
    return


@run_async
def paymentsuccess(update, context):
    user_id = update.message.chat_id
    paymentdetails = {"payment": user_id}
    paymentamqp(paymentdetails)
    machine_id = pendingusers[user_id]['machine']
    send(user_id, "Thank you for your payment! Please proceed to *{}*.".format(machine_id), [])
    sendqr(update, context)
    return


@run_async
def sendqr(update, context):
    id = update.message.chat_id
    try:
        params = {'location': pendingusers[id]['location'],
                  'machineid': pendingusers[id]['machine_id']}
        url = STATUSURL + 'getQRCode'
        startcode = requests.get(url=url, params=params).json()['startcode']
    except:
        send(id, "_Sorry, we are having trouble connecting to our Status system._", [])
        return
    context.bot.send_photo(chat_id=id, photo='https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={}&qzone=20'.format(
        startcode), caption='Scan this QR code at the assigned washing machine to start wash or unlock the door')
    del pendingusers[id]
    return


def main():
    updater = Updater(token=BOTTOKEN, workers=8, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(callbackquery))
    dp.add_handler(PreCheckoutQueryHandler(precheckout))
    dp.add_handler(MessageHandler(Filters.successful_payment, paymentsuccess))

    startamqp()
    updater.start_webhook(listen='0.0.0.0',
                          port=PORT,
                          url_path=BOTTOKEN,
                          key='private.key',
                          cert='cert.pem',
                          webhook_url='https://{}:{}/{}'.format(ip, PORT, BOTTOKEN))

    print("Bot is running. Press Ctrl+C to stop.")
    updater.idle()
    print("Bot stopped successfully.")


if __name__ == '__main__':
    main()
