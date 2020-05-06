import telegram.ext as telegram
from guide import guide
import pandas as pd
from staticmap import StaticMap, CircleMarker
import random
import os

# defineix una funció que saluda i que s'executarà quan el bot rebi el missatge /start
def start(update, context):
    name = update.effective_chat.first_name
    message = "*Hello %s, welcome to GuideBot!\n🧭*" % (name)
    context.bot.send_message(chat_id=update.effective_chat.id, text=message,
                             parse_mode='Markdown')
    context.bot.send_message(chat_id=update.effective_chat.id, text="Please use the /help command to get help.")


def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I can be your captain and help you go wherever you want!👨‍✈️\nJust type the following commands:")
    context.bot.send_message(chat_id=update.effective_chat.id, text="/author - show my creators\n/go destiny - start the guide to arrive from the actual position to the destiny\n/where - give your actual position\n/cancel - cancel the active guide system")

def author(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="My creators are Marc Garcia and Jofre Poch, the Team Piola!")
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('authors.JPG', 'rb'))


def go(update, context):



def where(update, context):
    # aquí, els missatges són rars: el primer és de debò, els següents són edicions
    message = update.edited_message if update.edited_message else update.message
    # extreu la localització del missatge
    lat, lon = message.location.latitude, message.location.longitude
    # escriu la localització al servidor
    print(lat, lon)
    # envia la localització al xat del client
    context.bot.send_message(chat_id=message.chat_id, text="You are at %s, %s"
                             % (lat, lon))
    fitxer = "%d.png" % random.randint(1000000, 9999999)
    mapa = StaticMap(500, 500)
    mapa.add_marker(CircleMarker((lon, lat), 'blue', 20))
    imatge = mapa.render()
    imatge.save(fitxer)
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(fitxer, 'rb'))
    os.remove(fitxer)


def cancel(update, context):
    print()


# declara una constant amb el access token que llegeix de token.txt
TOKEN = open('token.txt').read().strip()

# crea objectes per treballar amb Telegram
updater = telegram.Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# indica que quan el bot rebi la comanda /start s'executi la funció start
dispatcher.add_handler(telegram.CommandHandler('start', start))
dispatcher.add_handler(telegram.CommandHandler('help', help))
dispatcher.add_handler(telegram.CommandHandler('author', author))
dispatcher.add_handler(telegram.CommandHandler('go', go))
dispatcher.add_handler(telegram.MessageHandler(telegram.Filters.location,
                                               where))
dispatcher.add_handler(telegram.CommandHandler('cancel', cancel))
#dispatcher.add_handler(telegram.MessageHandler(Filters.location, where))

# engega el bot
updater.start_polling()
