import telegram.ext as telegram
from guide import guide
import osmnx as ox
from haversine import haversine, Unit
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


def _get_angle(angle):
    if angle is None:
        return "Go straight through"
    if angle < 0:
        angle += 360
    if angle < 22.5 or angle > 337.5:
        return "Go straight through"
    elif angle < 67.5:
        return "Turn half right and go straight through"
    elif angle < 112.5:
        return "Turn right and go straight through"
    elif angle < 180:
        return "Turn strong right and go straight through"
    elif angle < 247.5:
        return "Turn strong left and go straight through"
    elif angle < 292.5:
        return "Turn left and go straight through"
    else:
        return "Turn half left and go straight through"


def cancel(update, context):
    if context.user_data['route'] is not None:
        context.user_data['route'] = None
        text = "The guidance system has been canceled successfully.\n✅"
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    else:
        text = "The guidance system has not been activated yet."
        text2 = "Please use the /help command to get help."
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        context.bot.send_message(chat_id=update.effective_chat.id, text=text2)


def _particular_checkpoint_message(update, context):
    lat = context.user_data['coordinates'][0]
    lon = context.user_data['coordinates'][1]
    route = context.user_data['route']
    mapa = context.user_data['mapa']
    n = context.user_data['node']
    destination = context.user_data['destination']
    if n == len(route)-1:
        mid_lat = route[n]['mid'][0]
        mid_lon = route[n]['mid'][1]
        message1 = "Well done: You have reached checkpoint #%s, the last checkpoint!\nYou are at %s, %s" % (len(route)-1, lat, lon)
        message2 = "Go to your destination: %s, %s (%s)." % (mid_lat, mid_lon, destination)
        mapa = _mark_edge(mapa, route, n-1, 'fitxer.png')
        context.bot.send_message(chat_id=update.effective_chat.id, text=message1)
        context.bot.send_photo(chat_id=update.effective_chat.id,
                               photo=open('fitxer.png', 'rb'))
        context.bot.send_message(chat_id=update.effective_chat.id, text=message2)
        context.user_data['node'] += 1
        context.user_data['mapa'] = mapa
    if n == len(route):
        message = "Congratulations! You have reached your destination: %s.\n🏁🏁🏁" % (destination)
        mapa = _mark_edge(mapa, route, n-1, 'fitxer.png')
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        context.bot.send_photo(chat_id=update.effective_chat.id,
                               photo=open('fitxer.png', 'rb'))
        os.remove('fitxer.png')
        context.user_data['route'] = None


def _checkpoint_message(update, context):
    lat = context.user_data['coordinates'][0]
    lon = context.user_data['coordinates'][1]
    route = context.user_data['route']
    mapa = context.user_data['mapa']
    n = context.user_data['node']
    mid_lat = route[n]['mid'][0]
    mid_lon = route[n]['mid'][1]
    next_name = route[n]['next_name']
    current_name = route[n]['current_name']
    if next_name is None:
        next_name = "Unknown"
    if current_name is None:
        current_name = "Unknown"
    distance = _my_round(route[n]['length'])
    angle = route[n-1]['angle']
    message = "Well done: You have reached checkpoint #%s!\nYou are at %s, %s" % (n, lat, lon)
    message2 = "Go to checkpoint #%s: %s, %s (%s)\n%s %s %s meters." % (n+1, mid_lat, mid_lon, next_name, _get_angle(angle), current_name, distance)
    mapa = _mark_edge(mapa, route, n-1, 'fitxer.png')
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    context.bot.send_photo(chat_id=update.effective_chat.id,
                           photo=open('fitxer.png', 'rb'))
    context.bot.send_message(chat_id=update.effective_chat.id, text=message2)
    context.user_data['mapa'] = mapa
    context.user_data['node'] += 1


def _check_distance(context, update):
    coordinates = context.user_data['coordinates']
    route = context.user_data['route']
    n = context.user_data['node']
    if haversine(coordinates, (route[n-1]['mid'][0], route[n-1]['mid'][1]), unit=Unit.METERS) < 3:
        return True
    return False


def _current_location(update, context):
    '''aquesta funció es crida cada cop que arriba una nova
       localització d'un usuari'''
    message = update.edited_message if update.edited_message else update.message
    lat, lon = message.location.latitude, message.location.longitude
    context.user_data['coordinates'] = (lat, lon)
    if context.user_data['route'] is not None:
        if _check_distance(context, update):
            n = context.user_data['node']
            route = context.user_data['route']
            if n == len(route)-1 or n == len(route):
                _particular_checkpoint_message(update, context)
            else:
                _checkpoint_message(update, context)


def _start_guidance(update, context, destination):
    lat = context.user_data['coordinates'][0]
    lon = context.user_data['coordinates'][1]
    route = context.user_data['route']
    context.bot.send_photo(chat_id=update.effective_chat.id,
                           photo=open('fitxer.png', 'rb'))
    mid_lat = route[0]['mid'][0]
    mid_lon = route[0]['mid'][1]
    mid_name = route[0]['next_name']
    message = "You are at %s, %s \nStart at checkpoint #1: %s, %s (%s)" % (lat, lon, mid_lat, mid_lon, mid_name)
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def _location_error(update, context):
    message = "Please, send me your live location first. 📍"
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def go(update, context):
    try:
        coordinates = context.user_data['coordinates']
        destination_name = ' '.join(context.args)
        destination = ox.geo_utils.geocode(destination_name + ', Canet de Mar')
        context.user_data['destination'] = destination_name
        route = guide.get_directions(graph, coordinates, destination)
        context.user_data['route'] = route
        context.user_data['node'] = 1
        mapa = guide.plot_directions(graph, coordinates, destination, route, 'fitxer.png')
        context.user_data['mapa'] = mapa
        _start_guidance(update, context, destination)
    except KeyError:
        _location_error(update, context)


def where(update, context):
    try:
        lat = context.user_data['coordinates'][0]
        lon = context.user_data['coordinates'][1]
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
        _location_error(update, context)


def _false_loc(update, context):
    route = context.user_data['route']
    n = context.user_data['node']
    lat = route[n-1]['mid'][0]
    lon = route[n-1]['mid'][1]
    context.user_data['coordinates'] = (lat, lon)
    _current_location(update, context)


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
dispatcher.add_handler(telegram.CommandHandler('cancel', cancel))
dispatcher.add_handler(telegram.CommandHandler('fake', _false_loc))
# engega el bot
updater.start_polling()
