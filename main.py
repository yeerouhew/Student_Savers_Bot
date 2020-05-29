"""
Created on Fri May 22 15:21:17 2020

@author: yeerouhew
"""

import logging
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardMarkup
from telegram import InlineKeyboardButton
import datetime
import psycopg2

#deploy to heroku
import os

PORT = int(os.environ.get('PORT', 5000))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "1278045157:AAHCKTffFYAegrjgzTfm1KsgVuj4g0vRf78"

# DB connection
con = psycopg2.connect(user="dzwnjonhbsmqyu",
                       password="781f607ee579c427c05b3b1e3346da5d655dd8187500cbf4ab2a9d58a80c73e7",
                       host="ec2-34-232-147-86.compute-1.amazonaws.com",
                       port="5432", database="dcqfivrciptlut")
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS studentsavers.Room (id serial PRIMARY KEY, status varchar, next_availabletime timestamp);")
con.commit()

def start(update, context):
    cur.execute("INSERT INTO studentsavers.Room(status, next_availabletime) VALUES('Available', CURRENT_TIMESTAMP);")
    con.commit()

    features = [
        [InlineKeyboardButton('Event Handling', callback_data='eventhandling')],
        [InlineKeyboardButton('Room Searching', callback_data='roomsearching')]
    ]

    reply_markup = InlineKeyboardMarkup(features)
    update.message.reply_text('Hi, welcome to Studentsavers bot. Glad to have you here.What do you want to do?', reply_markup=reply_markup)
    logger.info('/start command triggered')

def inlinebutton(update, context):
    query = update.callback_query
    chat_id = query.from_user['id']

    if query.data == 'eventhandling':
        query.edit_message_text(text='You choose {}'.format('Event Handling'))
        logger.info('eventhandling option selected')

    if query.data == 'roomsearching':
        query.edit_message_text(text='You choose {}'.format('Checking room availability'))
        roomList = cur.execute("SELECT * FROM studentsavers.Room")
        roomList2 = cur.fetchone()
        con.commit()
        context.bot.send_message(chat_id, 'Room searching info: {}'.format(roomList2))
        cur.close()
        con.close()
        logger.info('roomsearching option selected')


def setCom(update, context):
    update.message.reply_text('/set <date>')

def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def echo(update, context):
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def alarm(context):
    # Send alarm message
    job = context.job
    context.bot.send_message(job.context, text='CS2030 DEADLINE')


def set_timer(update, context):
    # Add job to queue
    chat_id = update.message.chat_id

    try:
        # args[0] should contain the time for the timer in seconds
        datetimeobj = datetime.datetime.strptime(context.args[0], '%m/%d/%Y%H:%M:%S')
        today = datetime.datetime.now()
        diff = datetimeobj - today
        diffInSeconds = diff.seconds
        due = int(diffInSeconds)
        if due < 0:
            update.message.reply_text('Sorry we can not go back to future!')
            return

        # Add job to queue and stop current one if there is a timer already
        if 'job' in context.chat_data:
            old_job = context.chat_data['job']
            old_job.schedule_removal()
        new_job = context.job_queue.run_once(alarm, due, context=chat_id)
        context.chat_data['job'] = new_job

        update.message.reply_text('Timer successfully set!')

    except (IndexError, ValueError):
        update.message.reply_text('Usage: /set <date>')


def unset(update, context):
    """Remove the job if the user changed their mind."""
    if 'job' not in context.chat_data:
        update.message.reply_text('You have no active timer')
        return

    job = context.chat_data['job']
    job.schedule_removal()
    del context.chat_data['job']

    update.message.reply_text('Timer successfully unset!')

def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(inlinebutton))
    dp.add_handler(CommandHandler("help", help))

    # log all errors
    dp.add_error_handler(error)

    # set alarm for messages
    dp.add_handler(CommandHandler("set", set_timer,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("unset", unset, pass_chat_data=True))

    # Start the Bot
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN)
    updater.bot.setWebhook('https://student-saversbot.herokuapp.com/' + TOKEN)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()