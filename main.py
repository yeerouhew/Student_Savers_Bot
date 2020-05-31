import logging
import os

from telegram import (InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackQueryHandler)
from telegram import InlineKeyboardMarkup
from telegram import InlineKeyboardButton
import datetime
import psycopg2

# State definitions for top level conversation
SELECTING_ACTION, ROOM_SEARCHING, EVENT_HANDLING, HANDLING_EVENT = map(chr, range(4))
# State definitions for second level conversation
SELECT_BUILDING, SELECTING_LEVEL = map(chr, range(4, 6))
# State definitions for descriptions conversation
SELECTING_FEATURE, TYPING = map(chr, range(6, 8))
# Meta states
STOPPING, SHOWING = map(chr, range(8, 10))
# Shortcut for ConversationHandler.END
END = ConversationHandler.END

PORT = int(os.environ.get('PORT', 5000))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
TOKEN = "1278045157:AAHCKTffFYAegrjgzTfm1KsgVuj4g0vRf78"

# DB connection
con = psycopg2.connect(user="dzwnjonhbsmqyu",
                       password="781f607ee579c427c05b3b1e3346da5d655dd8187500cbf4ab2a9d58a80c73e7",
                       host="ec2-34-232-147-86.compute-1.amazonaws.com",
                       port="5432", database="dcqfivrciptlut")
cur = con.cursor()
# cur.execute(
#   "CREATE TABLE IF NOT EXISTS studentsavers.Room (id serial PRIMARY KEY, status varchar, next_availabletime timestamp);")
con.commit()


# Top level conversation callbacks
def start(update, context):
    text = 'Hi, welcome to Studentsavers bot. Glad to have you here.What do you want to do? Room Searching is only ' \
           'available for SoC buildings. To abort, simply type /stop.'
    buttons = [[
        InlineKeyboardButton(text='Event Handling', callback_data=str(EVENT_HANDLING)),
        InlineKeyboardButton(text='Room Searching', callback_data=str(ROOM_SEARCHING))
    ]]

    keyboard = InlineKeyboardMarkup(buttons)

    # If we're starting over we don't need do send a new message
    if context.user_data.get('START_OVER'):
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    else:
        update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data['START_OVER'] = False

    cur.execute("INSERT INTO studentsavers.Room(status, next_availabletime) VALUES('Available', CURRENT_TIMESTAMP);")
    con.commit()

    logger.info('/start command triggered')

    return SELECTING_ACTION

def get_roomData(update, context):
    query = update.callback_query
    chat_id = query.from_user['id']

    query.edit_message_text(text='You choose {}'.format('Checking room availability'))
    roomList = cur.execute("SELECT * FROM studentsavers.Room")
    roomList2 = cur.fetchall()
    con.commit()
    context.bot.send_message(chat_id, 'Room searching info: {}'.format(roomList2))
    print("get room_data called")
    cur.close()
    con.close()
    logger.info('roomsearching option selected')



def event_handling(update, context):
    update.callback_query.edit_message_text(text='Please set a date')

    return HANDLING_EVENT


def show_data(update, context):
    buttons = [[
        InlineKeyboardButton(text='Back', callback_data=str(END))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    text = '\n\n Selected building: ' + context.chat_data["building"]
    text += '\n\n Selected level: ' + context.chat_data["level"]
    text += '\n\n Selected time frame :' + context.chat_data["time"]

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return SHOWING


def stop(update, context):
    """End Conversation by command."""
    update.message.reply_text('See you around!')

    return END


# Second level conversation callbacks
def select_building(update, context):
    text = 'Choose a building'
    buttons = [[
        InlineKeyboardButton(text='COMS1', callback_data='COMS1'),
        InlineKeyboardButton(text='COMS2', callback_data='COMS2')
    ], [
        InlineKeyboardButton(text='Back', callback_data=str(END))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return SELECT_BUILDING


def select_level(update, context):
    context.chat_data['building'] = update.callback_query.data

    text = 'Choose your level'

    if update.callback_query.data == 'COMS1':
        buttons = [[
            InlineKeyboardButton(text='Level B1', callback_data='Level B1'),
            InlineKeyboardButton(text='Level 1', callback_data='Level 1')
        ], [
            InlineKeyboardButton(text='Level 2', callback_data='Level 2'),
            InlineKeyboardButton(text='Back', callback_data=str(END))
        ]]

    else:
        buttons = [[
            InlineKeyboardButton(text='Level 2', callback_data='Level 2'),
            InlineKeyboardButton(text='Level 3', callback_data='Level 3')
        ], [
            InlineKeyboardButton(text='Level 4', callback_data='Level 4'),
            InlineKeyboardButton(text='Back', callback_data=str(END))
        ]]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return SELECTING_LEVEL


def end_second_level(update, context):
    """Return to top level conversation."""
    context.user_data['START_OVER'] = True
    start(update, context)

    return END


# Third level callbacks
def select_feature(update, context):
    if not context.user_data['START_OVER']:
        context.chat_data['level'] = update.callback_query.data

    # If we collect features for a new person, clear the cache and save the gender
    if not context.user_data['START_OVER']:

        update.callback_query.answer()
    # But after we do that, we need to send a new message
    else:
        text = 'Got it! Do click on the respective buttons to move on.'

        buttons = [[
            InlineKeyboardButton(text='Edit', callback_data='TIME'),
            InlineKeyboardButton(text='Done', callback_data=str(END)),
        ]]

        keyboard2 = InlineKeyboardMarkup(buttons)

        update.message.reply_text(text=text, reply_markup=keyboard2)

    context.user_data['START_OVER'] = False
    return SELECTING_FEATURE


def ask_for_input(update, context):
    """Prompt user to input data for selected feature."""
    text = 'Please enter time in the following way:  HH:MM format to HH:MM format.'

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text)

    return TYPING


def save_input(update, context):
    """Save input for time """

    context.chat_data['time'] = update.message.text

    context.user_data['START_OVER'] = True

    return select_feature(update, context)


def stop_nested(update, context):
    """Completely end conversation from within nested conversation."""
    update.message.reply_text('Hope to see you again!.')

    return STOPPING


def setCom(update, context):
    update.message.reply_text('/set <date>')


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


def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


# Error handler
def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Set up third level ConversationHandler (collecting features)
    input_time_convo = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_feature,
                                           pattern='^' + 'Level B1' + '$|^' + 'Level 1' + '$|^' +
                                                   'Level 2' + '$|^' + 'Level 3' + '$|^' + 'Level 4' + '$')],

        states={
            SELECTING_FEATURE: [CallbackQueryHandler(ask_for_input,
                                                     pattern='^(?!' + str(END) + ').*$')],
            TYPING: [MessageHandler(Filters.text, save_input)],
        },

        fallbacks=[
            CallbackQueryHandler(show_data, pattern='^' + str(END) + '$'),
            CommandHandler('stop', stop_nested)
        ],

        map_to_parent={
            # Return to second level menu
            END: SELECTING_FEATURE,
            # End conversation alltogether
            STOPPING: STOPPING,
        }
    )

    # Set up second level ConversationHandler (selecting building)
    choose_building_convo = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_building,
                                           pattern='^' + str(ROOM_SEARCHING) + '$')],

        states={
            SELECT_BUILDING: [CallbackQueryHandler(select_level,
                                                   pattern='^{0}$|^{1}$'.format('COMS1',
                                                                                'COMS2'))],
            SELECTING_LEVEL: [input_time_convo]
        },

        fallbacks=[
            CallbackQueryHandler(end_second_level, pattern='^' + str(END) + '$'),
            CommandHandler('stop', stop_nested)
        ],

        map_to_parent={
            # After showing data return to top level menu
            SHOWING: SHOWING,
            # Return to top level menu
            END: SELECTING_ACTION,
            # End conversation alltogether
            STOPPING: END,
        }
    )

    # Set up top level ConversationHandler (selecting action)
    # Because the states of the third level conversation map to the ones of the second level
    # conversation, we need to make sure the top level conversation can also handle them
    selection_handlers = [
        choose_building_convo,
        CallbackQueryHandler(event_handling, pattern='^' + str(EVENT_HANDLING) + '$'),
    ]
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            SHOWING: [CallbackQueryHandler(start, pattern='^' + str(END) + '$')],
            SELECTING_ACTION: selection_handlers,
            SELECT_BUILDING: selection_handlers,
            HANDLING_EVENT: [input_time_convo],
            STOPPING: [CommandHandler('start', start)],
        },

        fallbacks=[
            CommandHandler('stop', stop)],
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler("h", help))
    dp.add_handler(CommandHandler("retrieve", get_roomData))

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
    updater.idle()

if __name__ == '__main__':
    main()
