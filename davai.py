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

    bot.sendMessage(update.message.chat_id, 
                    text=dedent('''\
                                Hi!
                                (Instructions go here)
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
    pass

def main():
    updater = Updater(telegram_key)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("origin", add_origin))
    dp.add_handler(CommandHandler("dates", get_dates))
    dp.add_handler(CommandHandler("davai", davai))
    # dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    origins = dict()
    dates = dict()
    solution_managers = dict()
    main()