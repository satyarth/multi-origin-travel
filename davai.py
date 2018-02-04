from telegram.ext import Updater, CommandHandler, Job, MessageHandler, Filters
from telegram.ext.dispatcher import run_async

from textwrap import dedent
from datetime import datetime

from branch_and_bound import solve_branch_and_bound
from manager import SolutionManager
from botutils import get_place, NotFound
from secret import telegram_key

from util import FORMAT

import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def start(bot, update):
    chat_id = update.message.chat_id

    dates[chat_id] = ('anytime', 'anytime')
    tabu_destinations[chat_id] = []
    origins[chat_id] = []

    solution_managers.pop(chat_id, None)
    expecting_id.pop(chat_id, None)
    destinations.pop(chat_id, None)

    bot.sendMessage(update.message.chat_id, 
                    text=dedent('''\
                                Hi!
                                First, pick origin cities with /origins [name]
                                e.g. /origins moscow london
                                Then pick dates with /dates
                                e.g. /dates 2018-01 2018-03
                                or /dates anytime
                                Then start optimizing with /davai
                                When you no longer need new search results, hit /stop
                                Davai!'''))

def completed(bot, chat_id):
    if chat_id in dates and chat_id in origins:
        bot.sendMessage(chat_id, text="You're good to go! Start me with /davai")

city_not_found = '''We couldn't find a city by that name. Sad!
                    Usage: /origin [cityname]
                    Example: /origin Moscow'''

def add_origins(bot, update, args):
    chat_id = update.message.chat_id
    
    if len(args) == 0:
        bot.sendMessage(chat_id, text='Where are you flying from? One or more cities')
        proceed_handlers[chat_id] = lambda cities: add_origins(bot, update, cities.split(' '))
        return
    
    for query in args:
        try:
            place = get_place(query)

        except NotFound:
            bot.sendMessage(chat_id, text=dedent(city_not_found))
            continue

        origins[chat_id].append(place)

        bot.sendMessage(chat_id,
                        text=place['PlaceName'] + " added. All good in da hood!")
    completed(bot, chat_id)

def add_destination(bot, update, args):
    chat_id = update.message.chat_id

    if len(args) == 0:
        bot.sendMessage(chat_id, text="Are you set on a particular destination? Give me your destination city or 'anywhere'")
        proceed_handlers[chat_id] = lambda dest: add_destination(bot, update, dest)
        return

    try:
        place = get_place(args[0])
        destinations[chat_id] = place
        bot.sendMessage(chat_id, text='Going to ' + place['PlaceName'] + '. Roger!')
    except NotFound:
        bot.sendMessage(chat_id, text=dedent(city_not_found))
        proceed_handlers[chat_id] = lambda dest: add_destination(bot, update, dest)
        return
    
    completed(bot, chat_id)

def add_tabu_destinations(bot, update, args):
    chat_id = update.message.chat_id

    if len(args) == 0:
        bot.sendMessage(chat_id, text="Are there places you definitely DON'T want to go to?")
        proceed_handlers[chat_id] = lambda tabus: add_tabu_destinations(bot, update, tabus.split(' '))
        return

    for query in args:
        try:
            place = get_place(query)

        except NotFound:
            bot.sendMessage(chat_id, text=dedent(city_not_found))
            continue

        tabu_destinations[chat_id].append(place)

        bot.sendMessage(chat_id,
                        text=place['PlaceName'] + " will not happen. I promise!")
    
    completed(bot, chat_id)

def get_dates(bot, update, args):
    print("AYY")
    chat_id = update.message.chat_id

    error_msg = '''Dates aren't in the right format. Examples of valid dates:
                   anytime
                   2018-01 2018-01
                   2018-02-12 2018-03-04'''

    success_msg = 'All good! Dates: '

    if len(args) == 0:
        bot.sendMessage(chat_id, text='When do you want to leave? [anytime/2012-12-21/2012-12]')
        proceed_handlers[chat_id] = lambda date: get_dates(bot, update, [date])
        return

    if args[0].lower() == 'anytime':
        dates[chat_id] = ['anytime', 'anytime']
        bot.sendMessage(chat_id,
                    text="Anytime, huh? You're an eager one!")
        completed(bot, chat_id)
        return

    if len(args) == 1:
        bot.sendMessage(chat_id, text='When do you want to return? [anytime/2012-12-21/2012-12]')
        proceed_handlers[chat_id] = lambda date: get_dates(bot, update, args + [date])
        return

    if len(args) == 2:
        [outbound, inbound] = args
        if len(outbound) == len(inbound):
            if outbound <= inbound:
                if len(outbound) == 7:
                    for date in [outbound, inbound]:
                        try:
                            datetime.strptime(date, '%Y-%m')

                        except ValueError:
                            bot.sendMessage(chat_id, text=dedent(error_msg))
                            return

                    dates[chat_id] = [outbound, inbound]
                    bot.sendMessage(chat_id, text=success_msg + str(dates[chat_id]))
                    completed(bot, chat_id)
                    return

                elif len(outbound) == 10:
                    for date in [outbound, inbound]:
                        try:
                            datetime.strptime(date, '%Y-%m-%d')
                        except ValueError:
                            bot.sendMessage(chat_id, text=dedent(error_msg))
                            return

                    dates[chat_id] = [outbound, inbound]
                    bot.sendMessage(chat_id, text=success_msg + str(dates[chat_id]))
                    completed(bot, chat_id)
                    return

    bot.sendMessage(chat_id, text=dedent(error_msg))

def get_solution_processor(bot, chat_id):
    def get_links_to_links(solution):
        def route2link(route):
            return 'https://www.skyscanner.ru/transport/flights' \
                   + '/' + route['OutboundLeg']['OriginDetails']['CityId'] \
                   + '/' + route['InboundLeg']['OriginDetails']['CityId'] \
                   + '/' + route['OutboundLeg']['DepartureDate'].replace('-', '')[2:8] \
                   + '/' + route['InboundLeg']['DepartureDate'].replace('-', '')[2:8]
        
        return map(route2link, solution.routes)

    def solution_processor(id, solution):
        msg = solution.destination_city or solution.destination
        msg += " from " + str(solution.price) + " roubles"
        msg += "\nOutbound date: " + solution.date_come.strftime(FORMAT)
        msg += "\nInbound date: "+ solution.date_leave.strftime(FORMAT)
        for link in get_links_to_links(solution):
            msg += '\n' + link
        bot.sendMessage(chat_id, text=msg)

    return solution_processor

@run_async
def davai(bot, update):
    chat_id = update.message.chat_id
    sp = get_solution_processor(bot, chat_id)
    solution_managers[chat_id] = SolutionManager(solve_branch_and_bound, sp)
    solution_managers[chat_id].solve(origins[chat_id], dates[chat_id],
                                     tabu_destinations=tabu_destinations[chat_id],
                                     destination= destinations[chat_id] if chat_id in destinations else 'anywhere')

def stop(bot, update):
    chat_id = update.message.chat_id
    if chat_id in solution_managers:
        solution_managers[chat_id].stopped = True
        bot.sendMessage(chat_id, text="Okay, I'll stop looking now. Start me again with /start")
        get_favourite(bot, chat_id)
        return

    bot.sendMessage(chat_id, text="Erm, nothing to stop...?")

def get_favourite(bot, chat_id):
    bot.sendMessage(chat_id, text="Pick your favourite solution and I'll share links to book it :D")
    expecting_id[chat_id] = True

def pick(bot, update):
    chat_id = update.message.chat_id
    if chat_id not in expecting_id:
        bot.sendMessage(chat_id, text="I don't remember finding any solutions for you. Retry with /start?")
        return

    msg = update.message.text.lstrip("/pick").strip()

    solution_ids = [int(solution_id) for solution_id in msg.split(' ')]
    print(solution_ids)

    solutions = solution_managers[chat_id].solutions
    bot.sendMessage(chat_id, text="I'm on it, gimme a sec...")

    for solution_id in solution_ids:
        solution = solutions[solution_id]
        link_dicts = solution_managers[chat_id].get_links(solution)
        reply = 'Booking links for solution ' + str(solution_id) + ': \n'
        for link_dict in link_dicts:
            reply += "[click me]("+link_dict['Link'] + ')\n'

        bot.sendMessage(chat_id, text=reply, parse_mode='Markdown')

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def proceed(bot, update):
    handler = proceed_handlers[update.message.chat_id]
    if handler:
        handler(update.message.text)
        if proceed_handlers[update.message.chat_id] == handler:
            proceed_handlers[update.message.chat_id] = None
    else:
        bot.sendMessage(update.message.chat_id, text='wat?')

def main():
    updater = Updater(telegram_key)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("origin", add_origins, pass_args=True))
    dp.add_handler(CommandHandler("origins", add_origins, pass_args=True))
    dp.add_handler(CommandHandler("dates", get_dates, pass_args=True))
    dp.add_handler(CommandHandler("nondestination", add_tabu_destinations, pass_args=True))
    dp.add_handler(CommandHandler("nondestinations", add_tabu_destinations, pass_args=True))
    dp.add_handler(CommandHandler("destination", add_destination, pass_args=True))
    dp.add_handler(CommandHandler("davai", davai))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("pick", pick))
    dp.add_handler(MessageHandler(Filters.text, proceed))
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    origins = dict()
    dates = dict()
    solution_managers = dict()
    expecting_id = dict()
    proceed_handlers = dict()
    destinations = dict()
    tabu_destinations = dict()
    main()