import telegram.ext as telegram
from guide import guide
import osmnx as ox
from haversine import haversine, Unit
from staticmap import StaticMap, CircleMarker, Line
import random
import os


'''explain the bot and user_data'''


def _fixed_graph():
    '''Load a fixed graph that has been previously downloaded by the user.
    If that's not the case, the fixed graph is downloaded and stored in the
    user's device.'''
    try:
        return guide.load_graph("Girona")
    except FileNotFoundError:
        Graph = guide.download_graph("Girona")
        guide.save_graph(Graph, "Girona")
        return Graph


# global variable of a fixed graph
graph = _fixed_graph()


def start(update, context):
    '''Welcome the user and offer help. It's automatically executed the first
    time the user begins the chat or when the bot receives the command
    /start.'''
    name = update.effective_chat.first_name
    text = ("*Hello %s, welcome to GuideBot! 🧭\n\n*"
            "Please use the /help command to get help." % (name))
    context.bot.send_message(chat_id=update.effective_chat.id, text=text,
                             parse_mode='Markdown')


def help(update, context):
    '''Show the available commands to interact with the bot and use its
    services. It's activated when the bot receives the command /help.'''
    text = ("I can be your captain and help you go wherever you want!👨‍✈️\n"
            "Just type the following commands:\n\n"
            "/start - starts de conversation.\n\n"
            "/help - offers help about the available commands.\n\n"
            "/author - shows information about the authors of the project.\n\n"
            "/go destí - begins to guide the user to get from their current"
            "position to the chosen destination point.\n"
            "_For example: /go Campus Nord._\n\n"
            "/where - shows the current localization of the user.\n\n"
            "/cancel - cancels the active guidance system.")
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')


def author(update, context):
    '''Return information about the authors of the project.
    It's activated when the bot receives the command /author.'''
    text = ("The creators of this project are Marc Garcia and Jofre Poch,"
            "the Team Piola!")
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    context.bot.send_photo(chat_id=update.effective_chat.id,
                           photo=open('authors.JPG', 'rb'))


def _mark_edge(update, context, filename):
    '''Mark the edge between the last node and the current node in green to
    show the user the last stretch he/she has done. Then, the edited map is
    stored in a given file and the field 'map' of the user_data is updated.'''
    route = context.user_data['route']
    mapa = context.user_data['map']
    node = context.user_data['node']
    # coordinates from the last node
    coordinates_first = (route[node-1]['src'][1], route[node-1]['src'][0])
    # coordinates from the current node
    coordinates_second = (route[node-1]['mid'][1], route[node-1]['mid'][0])
    coordinates = (coordinates_first, coordinates_second)
    # the edge is marked using the staticmap library
    mapa.add_line(Line(coordinates, 'green', 4))
    # the current node is marked unless it's the last one
    if (node != len(route)-1):
        mapa.add_marker(CircleMarker(coordinates_second, 'green', 10))
    picture = mapa.render()
    picture.save(filename)
    context.user_data['map'] = mapa


def _my_round(x, base=5):
    '''Round a distance x depending on its value. If x is smaller than 1,
    it's rouded to 1. If it's smaller than 10, it's rounded to the units
    using the python function round(x). Finally, if x is bigger than 10,
    it's rounded to a base 5 value. The aim of this function is to simplify
    the instructions of the guidance.'''
    if (x < 1):
        return 1
    if (x < 10):
        return round(x)
    return base * round(x/base)


def _get_angle(angle):
    '''Return the direction the user must follow to reach the next checkpoint
    depending on the angle between the user's current node and the next.

    To dicide the the direction we have established the following criterion:

    - straight: angle < 22.5 degrees or > than 337.5 degrees or None
    - half right: angle < 67.5 degrees and angle >= 22.5 degrees
    - right: angle < 112.5 degrees and angle >= 67.5 degrees
    - strong right: angle < 180 degrees and angle >= 112.5 degrees
    - strong left: angle < 247.5 degrees and angle >= 180 degrees
    - left: angle < 292.5 degrees and angle >= 247.5 degrees
    - half right: angle < 337.5 degrees and angle >= 292.5 degrees'''
    if angle is None:
        return "Go straight through"
    # if the angle has a negative value, we add 360 to it
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
    '''Cancel the current guidance system if the command /go has been called
    before. In the other case, the user is adverted that there isn't an active
    route and some help is offered. It's activated when the bot receives the
    command /cancel.'''
    if 'route' in context.user_data and context.user_data['route'] is not None:
        # in the case there's an active route, it's value on the user_data
        # dictionary is set to None
        context.user_data['route'] = None
        text = "The guidance system has been canceled successfully.\n✅"
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    else:
        text1 = "The guidance system has not been activated yet."
        text2 = ("Please use the /go command to start a route "
                 "or the /help command to get help.")
        context.bot.send_message(chat_id=update.effective_chat.id, text=text1)
        context.bot.send_message(chat_id=update.effective_chat.id, text=text2)


def _checkpoint_message(update, context):
    '''dssd'''
    lat = context.user_data['coordinates'][0]
    lon = context.user_data['coordinates'][1]
    route = context.user_data['route']
    node = context.user_data['node']
    mid_lat = route[node]['mid'][0]
    mid_lon = route[node]['mid'][1]
    next_name = route[node]['next_name']
    current_name = route[node]['current_name']
    if next_name is None:
        next_name = "Unknown"
    if current_name is None:
        current_name = "Unknown"
    distance = _my_round(route[node]['length'])
    angle = route[node-1]['angle']
    message = "Well done: You have reached checkpoint #%s!\nYou are at %s, %s" % (node, lat, lon)
    message2 = "Go to checkpoint #%s: %s, %s (%s)\n%s %s %s meters." % (node+1, mid_lat, mid_lon, next_name, _get_angle(angle), current_name, distance)
    _mark_edge(update, context, 'fitxer.png')
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    context.bot.send_photo(chat_id=update.effective_chat.id,
                           photo=open('fitxer.png', 'rb'))
    context.bot.send_message(chat_id=update.effective_chat.id, text=message2)
    context.user_data['node'] += 1


def _particular_checkpoint_message(update, context):
    lat = context.user_data['coordinates'][0]
    lon = context.user_data['coordinates'][1]
    route = context.user_data['route']
    node = context.user_data['node']
    destination = context.user_data['destination']
    if node == len(route)-1:
        mid_lat = route[node]['mid'][0]
        mid_lon = route[node]['mid'][1]
        message1 = "Well done: You have reached checkpoint #%s, the last checkpoint!\nYou are at %s, %s" % (len(route)-1, lat, lon)
        message2 = "Go to your destination: %s, %s (%s)." % (mid_lat, mid_lon, destination)
        _mark_edge(update, context, 'fitxer.png')
        context.bot.send_message(chat_id=update.effective_chat.id, text=message1)
        context.bot.send_photo(chat_id=update.effective_chat.id,
                               photo=open('fitxer.png', 'rb'))
        context.bot.send_message(chat_id=update.effective_chat.id, text=message2)
        context.user_data['node'] += 1
    if node == len(route):
        message = "Congratulations! You have reached your destination: %s.\n🏁🏁🏁" % (destination)
        _mark_edge(update, context, 'fitxer.png')
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        context.bot.send_photo(chat_id=update.effective_chat.id,
                               photo=open('fitxer.png', 'rb'))
        os.remove('fitxer.png')
        context.user_data['route'] = None


def _check_distance(context, update):
    '''Check if the distance between the current location of the user and the
    next node is smaller than 4 meters, which means the user is practicaly. A
    boolean value is returned indicating if the condition has been satisfied
    or not.'''
    coordinates = context.user_data['coordinates']
    route = context.user_data['route']
    node = context.user_data['node']
    # the calculus of the distance between two points has been made with the
    # library haversine
    if haversine(coordinates, (route[node-1]['mid'][0],
                 route[node-1]['mid'][1]), unit=Unit.METERS) < 4:
        return True
    return False


def _live_location(update, context):
    '''Update the 'coordinates' field from the user_data every time that a
    new location is detected. The distance between the current location and
    the next node is checked to see if the user has reached the next
    checkpoint. In this case, a function that will guide the user to the next
    checkpoint is called.'''

    '''message = update.edited_message if update.edited_message else update.message
    lat, lon = message.location.latitude, message.location.longitude
    context.user_data['coordinates'] = (lat, lon)'''
    # if the 'route' field from user_data is None, it means that the user
    # hasn't started any route
    if 'route' in context.user_data and context.user_data['route'] is not None:
        if _check_distance(context, update):
            node = context.user_data['node']
            route = context.user_data['route']
            # the stretch between the last two nodes and the one between the
            # last node and the destination point are treated with special
            # functions
            if node == len(route)-1 or node == len(route):
                _particular_checkpoint_message(update, context)
            else:
                _checkpoint_message(update, context)


def _start_guidance(update, context, destination):
    '''Lead the user from his/her source point to the first checkpoint. This
    stretch is treated as an special case because it's not an edge of the
    graph and there could be undetectable obstacles.'''

    # the coordinates and the route are obtained from the user_data dictionary
    lat = context.user_data['coordinates'][0]
    lon = context.user_data['coordinates'][1]
    route = context.user_data['route']
    context.bot.send_photo(chat_id=update.effective_chat.id,
                           photo=open('fitxer.png', 'rb'))
    next_lat = route[0]['mid'][0]
    next_lon = route[0]['mid'][1]
    next_name = route[0]['next_name']
    text = ("You are at %s, %s \nStart at checkpoint #1: %s, %s (%s)"
            % (lat, lon, next_lat, next_lon, next_name))
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def _location_error(update, context):
    '''Advert the user that his/her live location hasn't been sent. This
    function is called when the user tries to use the /where and /go commands
    before sending the live location.'''
    text = "Please, send me your live location first. 📍"
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def _destination_error(update, context):
    '''Advert the user that there has been a problem with his/her destination.
    This function is called when the user uses the command /go without any
    destination or with an unexistent one.'''
    text = ("You have not entered a destination or it's out of the graph's "
            "range.")
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def go(update, context):
    '''Begin the guidance system, the principal fucntion of the bot.
    The following fields are initialized in the user_data, which is an
    internal dictionary exclusive for every chat ID: destination, route,
    node and map.An error will be rised if the user hasn't provided his
    location, as well as if the user hasn't specified a destination or it
    doesn't exist. It's activated when the bot receives the command /go and
    a destination (string).'''
    try:
        # the user's current location is obtainted from user_data
        coordinates = (41.968450, 2.821167)
        context.user_data['coordinates'] = coordinates
        # gets the destination name from the user's message
        destination_name = ' '.join(context.args)
        # convertion of the destination name (string) to a tuple
        # of coordinates using the osmnx library
        destination = ox.geo_utils.geocode(destination_name)
        context.user_data['destination'] = destination_name
        route = guide.get_directions(graph, coordinates, destination)
        context.user_data['route'] = route
        context.user_data['node'] = 1
        # checks if the destination point is within the graph's range
        # if the distance from the last node to the destination point
        # is bigger than 4km, an error is rised
        if haversine(destination, route[len(route)-1]['src']) > 4:
            _destination_error(update, context)
        else:
            _map = guide.plot_directions(graph, coordinates, destination,
                                         route, 'fitxer.png')
            context.user_data['map'] = _map
            # special function to treat the stretch from the user's source
            # point to the first node of the route
            _start_guidance(update, context, destination)
    except KeyError:
        _location_error(update, context)
    except Exception:
        _destination_error(update, context)


def where(update, context):
    '''Give the user the coordinates of his/her current location and shows a
    photo with it on the current graph. It's activated when the bot receives
    the command /where.'''
    try:
        lat = context.user_data['coordinates'][0]
        lon = context.user_data['coordinates'][1]
        text = "You are at the coordinates %s, %s" % (lat, lon)
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        # a provisional file is generated to store the location photo
        file = "%d.png" % random.randint(1000000, 9999999)
        # the map is created using the library staticmap
        mapa = StaticMap(500, 500)
        mapa.add_marker(CircleMarker((lon, lat), 'blue', 20))
        picture = mapa.render()
        picture.save(file)
        context.bot.send_photo(chat_id=update.effective_chat.id,
                               photo=open(file, 'rb'))
        # the file is removed after the photo is sent to avoid preserving
        # useless data and save memory space
        os.remove(file)
    except KeyError:
        _location_error(update, context)


def _false_loc(update, context):
    route = context.user_data['route']
    node = context.user_data['node']
    lat = route[node-1]['mid'][0]
    lon = route[node-1]['mid'][1]
    context.user_data['coordinates'] = (lat, lon)
    _live_location(update, context)


def main():
    # the token of the chat is obtainted from the user's file token.txt
    TOKEN = open('token.txt').read().strip()

    # create the Updater and pass it to the bot's token.
    updater = telegram.Updater(token=TOKEN, use_context=True)
    # get the dispatcher to register the handlers
    dispatcher = updater.dispatcher

    # add the command handlers of the bot
    # the bot will answer to any of these commands
    dispatcher.add_handler(telegram.CommandHandler('start', start))
    dispatcher.add_handler(telegram.CommandHandler('help', help))
    dispatcher.add_handler(telegram.CommandHandler('author', author))
    dispatcher.add_handler(telegram.CommandHandler('cancel', cancel))
    dispatcher.add_handler(telegram.CommandHandler('where', where))
    dispatcher.add_handler(telegram.CommandHandler('go', go))
    dispatcher.add_handler(telegram.CommandHandler('cancel', cancel))

    # add a message handler to call the fucntion _live_location every time that
    # a location is sent by the user
    dispatcher.add_handler(telegram.MessageHandler(telegram.Filters.location,
                                                   _live_location))

    dispatcher.add_handler(telegram.CommandHandler('fake', _false_loc))

    # run the bot
    updater.start_polling()


main()
