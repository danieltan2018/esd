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
STATUSURL = 'http://status.delaundro.me'
QUEUEURL = 'http://queue.delaundro.me'


@run_async
def startamqp():
    channelqueue = channel.queue_declare(queue="status", durable=True)
    queue_name = channelqueue.method.queue
    channel.queue_bind(exchange=exchangename,
                       queue=queue_name, routing_key='*.status')
    channel.basic_consume(
        queue=queue_name, on_message_callback=amqpcallback, auto_ack=True)
    channel.start_consuming()


@run_async
def amqpcallback(channel, method, properties, body):
    status = json.loads(body)
    statuscode = status['statuscodeid']
    id = status['curuser']
    if statuscode == 1:
        bot.send_message(
            chat_id=id, text="*Your wash has started!*\nWe will notify you when it's done.", parse_mode=telegram.ParseMode.MARKDOWN)
    elif statuscode == 0:
        bot.send_message(
            chat_id=id, text="*Wash Complete!*\nPlease collect your laundry within 15 minutes.", parse_mode=telegram.ParseMode.MARKDOWN)
        bot.send_message(
            chat_id=id, text="Thank you for choosing DE'Laundro. To start another wash, [click here](https://t.me/delaundrobot?start=delaundro).", parse_mode=telegram.ParseMode.MARKDOWN)
        location = status['location']
        machine_id = status['machineid']
        params = {'location': location}
        url = QUEUEURL + 'nextuser'
        nextuser = requests.get(url=url, params=params)
        newwash(nextuser, location, machine_id)


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
    bot = telegram.Bot(token=BOTTOKEN)
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


@run_async
def welcome(update, context):
    id = update.message.chat_id
    send(id, "*Welcome to DE’Laundro!*", [])
    selectlocation(id, update, context)
    return


@run_async
def selectlocation(id, update, context):
    try:
        url = STATUSURL + '/findLocation'
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
        waitingtime = requests.get(url=url, params=params)
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
            context.bot.answer_callback_query(
                query.id, text="There is no queue. You will be assigned the first available machine.", show_alert=True)
            newwash(chat_id, data, machine_id)
            msg = "It's your turn!"
            queue = False
        else:
            msg = "You are in the queue!"
            queue = True
    except:
        context.bot.answer_callback_query(
            query.id, text="Sorry, we are having trouble connecting to our Status system.", show_alert=True)
        return
    if queue:
        try:
            params = {'location': data}
            url = QUEUE + 'queuelist'
            queuelength = len(requests.get(
                url=url, params=params).json()['queue'])
            params = {'location': data, 'user_id': chat_id}
            url = QUEUE + 'newqueue'
            requests.post(url=url, params=params)
            context.bot.answer_callback_query(
                query.id, text="There are {} people ahead of you. We will notify you when it's your turn.".format(queuelength), show_alert=True)
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
def newwash(user_id, location, machine_id):
    pass


@run_async
def dopayment(update, context):
    washtype = "Standard Wash"  # for testing
    price = 5  # for testing
    id = update.message.chat_id  # for testing
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


@run_async
def precheckout(update, context):
    query = update.pre_checkout_query
    if query.invoice_payload != 'delaundro-pay':
        query.answer(ok=False, error_message="Something went wrong...")
    else:
        query.answer(ok=True)


@run_async
def paymentsuccess(update, context):
    update.message.reply_text("Thank you for your payment!")
    user_id = update.message.chat_id
    paymentdetails = {"payment": user_id}
    paymentamqp(paymentdetails)


@run_async
def sendqr(update, context):
    id = update.message.chat_id  # for testing
    unlockcode = 12345  # for testing
    context.bot.send_photo(chat_id=id, photo='https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={}&qzone=20'.format(
        unlockcode), caption='Scan this QR code at the assigned washing machine to start wash or unlock the door')
    return


def main():
    updater = Updater(token=BOTTOKEN, workers=8, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(callbackquery))
    dp.add_handler(CommandHandler("testpay", dopayment))
    dp.add_handler(PreCheckoutQueryHandler(precheckout))
    dp.add_handler(MessageHandler(Filters.successful_payment, paymentsuccess))
    dp.add_handler(CommandHandler("testqr", sendqr))

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
