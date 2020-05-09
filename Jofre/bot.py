import telegram.ext as telegram
from telegram import KeyboardButton, ReplyKeyboardMarkup
from guide import guide
import osmnx as ox
from staticmap import StaticMap, CircleMarker
import random
import os

# variables globals que indiquen la posició actual de l'usuari
lat, lon = None, None
graph = guide.load_graph("Girona")


def _current_location(update, context):
    '''aquesta funció es crida cada cop que arriba una nova
       localització d'un usuari'''
    message = update.edited_message if update.edited_message else update.message
    global lat
    global lon
    lat, lon = message.location.latitude, message.location.longitude


# defineix una funció que saluda i que s'executarà quan el bot rebi el missatge /start
def start(update, context):
    name = update.effective_chat.first_name
    message1 = "*Hello %s, welcome to GuideBot!\n🧭*" % (name)
    message2 = "Please use the /help command to get help."
    context.bot.send_message(chat_id=update.effective_chat.id, text=message1,
                             parse_mode='Markdown')
    context.bot.send_message(chat_id=update.effective_chat.id, text=message2)


def help(update, context):
    message = "I can be your captain and help you go wherever you want!👨‍✈️\nJust type the following commands:"
    command1 = "/start - starts de conversation."
    command2 = "/help - offers help abput the available commands."
    command3 = '/author - shows information about the authors of the project.'
    command4 = "/go destí - begins to guide the user to get from their current position tho the chosen destination point."
    example4 = "<i>For example: /go Campus Nord.</i>"
    command5 = "/where - shows the current localization of the user."
    command6 = "/cancel - cancels the active guidance system."
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id=chat_id, text=message)
    context.bot.send_message(chat_id=chat_id, text=command1)
    context.bot.send_message(chat_id=chat_id, text=command2)
    context.bot.send_message(chat_id=chat_id, text=command3)
    context.bot.send_message(chat_id=chat_id, text=command4)
    context.bot.send_message(chat_id=chat_id, text=example4, parse_mode='HTML')
    context.bot.send_message(chat_id=chat_id, text=command5)
    context.bot.send_message(chat_id=chat_id, text=command6)


def author(update, context):
    message = "My creators of this project are Marc Garcia and Jofre Poch, the Team Piola!"
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    context.bot.send_photo(chat_id=update.effective_chat.id,
                           photo=open('authors.JPG', 'rb'))


def go(update, context):
    destination_name = ' '.join(context.args)
    destination = ox.geo_utils.geocode(destination_name)
    route = guide.get_directions(graph, (lat, lon), destination)
    guide.plot_directions(graph, (lat, lon), destination, route, 'fitxer.png')
    context.bot.send_photo(chat_id=update.effective_chat.id,
                           photo=open('fitxer.png', 'rb'))
    os.remove('fitxer.PNG')
    mid_lat = route[0]['mid'][0]
    mid_lon = route[0]['mid'][1]
    mid_name = route[0]['next_name']
    message = "You are at %s, %s \nStart at checkpoint #1: %s, %s %s" % (lat, lon, mid_lat, mid_lon, mid_name)
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def where(update, context):
    if lat is not None and lon is not None:
        # envia la localització al xat del client
        text = "You are at the coordinates %s, %s" % (lat, lon)
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        fitxer = "%d.png" % random.randint(1000000, 9999999)
        mapa = StaticMap(500, 500)
        mapa.add_marker(CircleMarker((lon, lat), 'blue', 20))
        imatge = mapa.render()
        imatge.save(fitxer)
        context.bot.send_photo(chat_id=update.effective_chat.id,
                               photo=open(fitxer, 'rb'))
        os.remove(fitxer)
    else:
        location_keyboard = KeyboardButton(text="Send location 📍",
                                           request_location=True)
        cancel_keyboard = KeyboardButton('Cancel')
        custom_keyboard = [[location_keyboard, cancel_keyboard]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard)
        update.message.reply_text(
                    "Please, send me your current location.",
                    reply_markup=reply_markup)


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

dispatcher.add_handler(telegram.CommandHandler('cancel', cancel))
dispatcher.add_handler(telegram.CommandHandler('where', where))
dispatcher.add_handler(telegram.MessageHandler(telegram.Filters.location,
                                               _current_location))
dispatcher.add_handler(telegram.CommandHandler('go', go))
# engega el bot
updater.start_polling()
