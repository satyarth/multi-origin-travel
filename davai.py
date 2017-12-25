from telegram.ext import Updater, CommandHandler, Job
from telegram.ext.dispatcher import run_async

from textwrap import dedent
from datetime import datetime

from branch_and_bound import solve_branch_and_bound
from manager import SolutionManager
from botutils import get_city_id, NotFound
from secret import telegram_key

from util import FORMAT

import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def start(bot, update):
    chat_id = update.message.chat_id
    
    if chat_id in origins:
        origins.pop(chat_id)
        
    if chat_id in dates:
        dates.pop(chat_id)
        
    if chat_id in solution_managers:
        solution_managers.pop(chat_id)

    if chat_id in expecting_id:
        expecting_id.pop(chat_id)

    bot.sendMessage(update.message.chat_id, 
                    text=dedent('''\
                                Hi!
                                First, pick origin cities with /origin [name]
                                e.g. /origin moscow
                                Then pick dates with /dates
                                e.g. /dates 2018-01 2018-03
                                or /dates anytime
                                Then start optimizing with /davai
                                When you see something you like, hit /stop and use /pick to get the booking links for your preferred solution.
                                Davai!'''))

def completed(bot, chat_id):
    if chat_id in dates and chat_id in origins:
        bot.sendMessage(chat_id, text="You're good to go! Start me with /davai")

def add_origin(bot, update):
    chat_id = update.message.chat_id
    city_name = update.message.text.lstrip('/addorigin').strip()

    try:
        city_id = get_city_id(city_name)

    except NotFound:
        bot.sendMessage(chat_id, text=dedent('''We couldn't find a city by that name. Sad!
                                                Usage: /origin [cityname]
                                                Example: /origin Moscow'''))
        return

    try:
        origins[chat_id].append(city_id)

    except KeyError:
        origins[chat_id] = [city_id]

    bot.sendMessage(chat_id,
                    text=city_name + " (City ID: " + city_id + ") added. All good in da hood!\n Currently on the list: " + str(origins[chat_id]))
    completed(bot, chat_id)

def get_dates(bot, update):
    print("AYY")
    chat_id = update.message.chat_id
    msg = update.message.text.lstrip('/dates').strip()
    print(msg)

    error_msg = '''Dates aren't in the right format. Examples of valid dates:
                   anytime
                   2018-01 2018-01
                   2018-02-12 2018-03-04'''

    success_msg = 'All good! Dates: '

    if msg.lower() == 'anytime':
        dates[chat_id] = ['anytime', 'anytime']
        bot.sendMessage(chat_id,
                    text="Anytime, huh? You're an eager one!")
        completed(bot, chat_id)
        return

    if len(msg.split(' ')) == 2:
        [outbound, inbound] = msg.split(' ')
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
    def solution_processor(id, solution):
        msg = "id: " + str(id) +"\nDestination city_id: " + solution.destination + "\nOutbound date: " + solution.date_come.strftime(FORMAT) + "\nInbound date: "+ solution.date_leave.strftime(FORMAT)+ "\nPrice: " + str(solution.price) + " rubles"
        bot.sendMessage(chat_id, text=msg)

    return solution_processor

@run_async
def davai(bot, update):
    chat_id = update.message.chat_id
    sp = get_solution_processor(bot, chat_id)
    solution_managers[chat_id] = SolutionManager(solve_branch_and_bound, sp)
    solution_managers[chat_id].solve(dates[chat_id][0], dates[chat_id][1], origins[chat_id])

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

def main():
    updater = Updater(telegram_key)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("origin", add_origin))
    dp.add_handler(CommandHandler("dates", get_dates))
    dp.add_handler(CommandHandler("davai", davai))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("pick", pick))
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    origins = dict()
    dates = dict()
    solution_managers = dict()
    expecting_id = dict()
    main()