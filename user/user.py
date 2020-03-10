import os
import requests
import telegram
import telegram.bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Updater, CommandHandler,
                          MessageHandler, Filters, CallbackQueryHandler)
from telegram.ext.dispatcher import run_async

BOTTOKEN = os.getenv('BOTTOKEN')
PORT = 8443

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
    print(deeplink)
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
        # Get list of locations from Queue
        raise Exception("Not Implemented")
    except:
        send(id, "_ERROR: Unable to connect to Queue, using sample locations..._", [])
        locations = ['Novena', 'Balestier', 'Bukit Panjang']
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
        # Get estimated waiting time from Queue
        raise Exception("Not Implemented")
    except:
        context.bot.answer_callback_query(
            query.id, text="ERROR: Unable to connect to Queue, using sample waiting time...", show_alert=True)
        waitingtime = str(30)
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


def joinqueue(update, context):
    query = update.callback_query
    data = query.data
    data = data.replace('JOINQUEUE=', '')
    try:
        # Add to Queue
        raise Exception("Not Implemented")
    except:
        context.bot.answer_callback_query(
            query.id, text="ERROR: Unable to connect to Queue, simulating join queue...", show_alert=True)
        queuelength = str(1)
    msg = "You are in the queue"
    context.bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=msg,
        parse_mode=telegram.ParseMode.MARKDOWN
    )
    context.bot.answer_callback_query(
        query.id, text="There are {} people ahead of you. We will notify you when it's your turn.".format(queuelength), show_alert=True)
    return


def cancelqueue(update, context):
    query = update.callback_query
    id = query.message.chat_id
    context.bot.delete_message(chat_id=id, message_id=query.message.message_id)
    selectlocation(id, update, context)
    context.bot.answer_callback_query(query.id)
    return


def main():
    updater = Updater(token=BOTTOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(callbackquery))

    # updater.start_polling()
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
