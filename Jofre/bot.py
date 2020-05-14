import telegram.ext as telegram
from telegram import KeyboardButton, ReplyKeyboardMarkup
from guide import guide
import osmnx as ox
from haversine import haversine
from staticmap import StaticMap, CircleMarker, Line
import random
import os


def _fixed_graph():
    try:
        return guide.load_graph("Canet")
    except FileNotFoundError:
        Canet = guide.download_graph("Canet de Mar")
        guide.save_graph(Canet, "Canet")
        return guide.load_graph("Canet")


graph = _fixed_graph()


def _current_location(update, context):
    '''aquesta funció es crida cada cop que arriba una nova
       localització d'un usuari'''
    message = update.edited_message if update.edited_message else update.message
    chat_id = update.effective_chat.id
    lat, lon = message.location.latitude, message.location.longitude
    context.user_data[chat_id] = (lat, lon)


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
    command2 = "/help - offers help about the available commands."
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


def _mark_edge(mapa, directions, node, filename):
    coordinates_first = (directions[node]['src'][1], directions[node]['src'][0])
    coordinates_second = (directions[node]['mid'][1], directions[node]['mid'][0])
    coordinates = (coordinates_first, coordinates_second)
    mapa.add_line(Line(coordinates, 'green', 4))
    if (node != len(directions)-1):
        mapa.add_marker(CircleMarker(coordinates_second, 'green', 10))
    imatge = mapa.render()
    imatge.save(filename)
    return mapa


def _my_round(x, base=5):
    if (x < 1):
        return 1
    if (x < 10):
        return round(x)
    return base * round(x/base)


def _go_particular_case(route, node, destination_name):
    if node == len(route)-2:
        mid_lat = route[node]['dst'][0]
        mid_lon = route[node]['dst'][1]
        message = "Go to your destination: %s, %s (%s)." % (mid_lat, mid_lon, destination_name)
        return message
    if node == len(route)-1:
        message = "Congratulations! You have reached your destination: %s.\n🏁🏁🏁" % (destination_name)
        return message


def go(update, context):
    try:
        chat_id = update.effective_chat.id
        lat = context.user_data[chat_id][0]
        lon = context.user_data[chat_id][1]
        destination_name = ' '.join(context.args)
        destination = ox.geo_utils.geocode(destination_name + ', Canet de Mar')
        route = guide.get_directions(graph, (lat, lon), destination)
        mapa = guide.plot_directions(graph, (lat, lon), destination, route, 'fitxer.png')
        context.bot.send_photo(chat_id=update.effective_chat.id,
                               photo=open('fitxer.png', 'rb'))
        mid_lat = route[0]['mid'][0]
        mid_lon = route[0]['mid'][1]
        mid_name = route[0]['next_name']
        message = "You are at %s, %s \nStart at checkpoint #1: %s, %s (%s)" % (lat, lon, mid_lat, mid_lon, mid_name)
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        n = 0
        while (n < len(route) - 2):
            # while haversine((lat, lon), (route[n]['mid'][0], route[n]['mid'][1])) > 1:
            #   None
            n += 1
            mid_lat = route[n]['mid'][0]
            mid_lon = route[n]['mid'][1]
            next_name = route[n]['next_name']
            current_name = route[n]['current_name']
            if next_name is None:
                next_name = "Unknown"
            if current_name is None:
                current_name = "Unknown"
            distance = guide._my_round(route[n]['length'])
            angle = route[n-1]['angle']
            message = "Well done: You have reached checkpoint #%s!\nYou are at %s, %s" % (n, lat, lon)
            message2 = "Go to checkpoint #%s: %s, %s (%s)\n%s %s %s meters." % (n+1, mid_lat, mid_lon, next_name, guide._get_angle(angle), current_name, distance)
            mapa = guide._mark_edge(mapa, route, n-1, 'fitxer.png')
            context.bot.send_message(chat_id=update.effective_chat.id, text=message)
            context.bot.send_photo(chat_id=update.effective_chat.id,
                                   photo=open('fitxer.png', 'rb'))
            context.bot.send_message(chat_id=update.effective_chat.id, text=message2)
        final_message1 = "Well done: You have reached checkpoint #%s, the last checkpoint!\nYou are at %s, %s" % (len(route)-1, lat, lon)
        final_message1_2 = guide._go_particular_case(route, len(route)-2, destination_name)
        final_message2 = guide._go_particular_case(route, len(route)-1, destination_name)
        # while haversine((lat, lon), (route[len(route)-2]['mid'][0], route[len(route)-2]['mid'][1])) > 1:
        # None
        n += 1
        mapa = guide._mark_edge(mapa, route, n-1, 'fitxer.png')
        context.bot.send_message(chat_id=update.effective_chat.id, text=final_message1)
        context.bot.send_photo(chat_id=update.effective_chat.id,
                               photo=open('fitxer.png', 'rb'))
        context.bot.send_message(chat_id=update.effective_chat.id, text=final_message1_2)
        # while haversine((lat, lon), (route[len(route)-1]['mid'][0], route[len(route)-1]['mid'][1])) > 1:
        # None
        n += 1
        mapa = guide._mark_edge(mapa, route, n-1, 'fitxer.png')
        context.bot.send_message(chat_id=update.effective_chat.id, text=final_message2)
        context.bot.send_photo(chat_id=update.effective_chat.id,
                               photo=open('fitxer.png', 'rb'))
        os.remove('fitxer.png')
    except KeyError:
        location_keyboard = KeyboardButton(text="Send location 📍",
                                           request_location=True)
        cancel_keyboard = KeyboardButton('Cancel')
        custom_keyboard = [[location_keyboard, cancel_keyboard]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard)
        update.message.reply_text(
                    "Please, send me your current location first.",
                    reply_markup=reply_markup)


def where(update, context):
    try:
        chat_id = update.effective_chat.id
        lat = context.user_data[chat_id][0]
        lon = context.user_data[chat_id][1]
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
    except KeyError:
        location_keyboard = KeyboardButton(text="Send location 📍",
                                           request_location=True)
        cancel_keyboard = KeyboardButton('Cancel')
        custom_keyboard = [[location_keyboard, cancel_keyboard]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard)
        update.message.reply_text(
                    "Please, send me your current location first.",
                    reply_markup=reply_markup)


def cancel(update, context):
    """if active_guidance:
        active_guidance = False
        text = "The guidance system has been canceled successfully.\n✅"
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    else:
        text = "The guidance system has not been activated yet."
        text2 = "Please use the /help command to get help."
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        context.bot.send_message(chat_id=update.effective_chat.id, text=text2)"""


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
