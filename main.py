import json
import logging
import os

from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackQueryHandler)
from telegram import InlineKeyboardMarkup
from telegram import InlineKeyboardButton
import datetime
import psycopg2
import pytz
import urllib3
import roomSearch

# State definitions for top level conversation
SELECTING_ACTION, ROOM_SEARCHING, EVENT_HANDLING, HANDLING_EVENT = map(chr, range(4))
# State definitions for second level conversation
SELECT_BUILDING, SELECTING_LEVEL = map(chr, range(4, 6))
# State definitions for descriptions conversation
SELECTING_FEATURE, TYPING = map(chr, range(6, 8))

SELECTED_ROOM, SUCCESSFUL_CHECK_IN = map(chr, range(10, 12))

# Meta states
STOPPING, SHOWING = map(chr, range(8, 10))

# Shortcut for ConversationHandler.END
END = ConversationHandler.END

PORT = int(os.environ.get('PORT', 5000))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
TOKEN = "1278045157:AAFjUYhhg50425eKh6cTKpF9APpzwjOdYiU"

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

    context.chat_data["date"] = datetime.datetime.now(pytz.timezone('Asia/Singapore'))
    context.chat_data["day"] = datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime("%A")

    keyboard = InlineKeyboardMarkup(buttons)

    # If we're starting over we don't need do send a new message
    if context.user_data.get('START_OVER'):
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    else:
        update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data['START_OVER'] = False

    logger.info('/start command triggered')

    return SELECTING_ACTION


def event_handling(update, context):
    update.callback_query.edit_message_text(text='Please set a date')

    return HANDLING_EVENT


def callNusmodApi(date, day, start_time, end_time, list_of_rooms):
    url = "https://api.nusmods.com/v2/2019-2020/semesters/2/venueInformation.json"

    http = urllib3.PoolManager()
    json_obj = http.request('GET', url)
    text = json.loads(json_obj.data.decode('UTF-8'))

    current_weekNo = roomSearch.return_weekNo(date)
    available_rooms = []

    for rooms in list_of_rooms:

        if text[rooms][0]["classes"]:

            for index in range(0, len(text[rooms][0]["classes"])):

                weekNo = text[rooms][0]["classes"][index]["weeks"]

                for num in weekNo:

                    if int(current_weekNo) == num:

                        if text[rooms][0]["classes"][index]["day"] == day:

                            start_classTime = datetime.datetime.strptime(text[rooms][0]["classes"][index]["startTime"],
                                                                         '%H%M').time()

                            end_classTime = datetime.datetime.strptime(text[rooms][0]["classes"][index]["endTime"],
                                                                       '%H%M').time()

                            if start_time < start_classTime and end_time < end_classTime:
                                available_rooms.append(rooms)
                            elif available_rooms.count(rooms) > 0:
                                available_rooms.remove(rooms)
                                break
                        else:
                            available_rooms.append(rooms)

    available_rooms = list(dict.fromkeys(available_rooms))

    return available_rooms


def show_data(update, context):
    if context.chat_data["building"] == "COMS1":
        room_label = roomSearch.com1_data(context.chat_data["level"])

    else:
        room_label = roomSearch.com2_data(context.chat_data["level"])

    available_rooms_data = callNusmodApi(context.chat_data["date"], context.chat_data["day"],
                                         context.chat_data["start_time"], context.chat_data["end_time"],
                                         room_label)

    if len(available_rooms_data) > 0:
        text = 'Rooms available are : '

        for rooms in available_rooms_data:
            text += '\n' + rooms

    else:
        text = " No available room found"

    context.chat_data["avail_rooms"] = available_rooms_data

    buttons = [[
        InlineKeyboardButton(text='Check in', callback_data='check-in'),
        InlineKeyboardButton(text='Back', callback_data=str(END))
    ]]

    keyboard = InlineKeyboardMarkup(buttons)

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

    message = update.message.text.replace("to", " ")
    context.chat_data['start_time'] = datetime.datetime.strptime(message.split()[0], '%H:%M').time()
    context.chat_data['end_time'] = datetime.datetime.strptime(message.split()[1], '%H:%M').time()

    context.user_data['START_OVER'] = True

    return select_feature(update, context)


def select_available_room(update, context):
    text = 'Choose a room: '

    buttons = [];
    if len(context.chat_data["avail_rooms"]) > 0:
        for rooms in context.chat_data["avail_rooms"]:
            buttons.append([InlineKeyboardButton(text=rooms, callback_data=rooms)])

    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return SELECTED_ROOM


def show_check_in_data(update, context):
    print("hello check in data")
    print(update.callback_query.data)

    context.chat_data['chosen_room'] = update.callback_query.data

    builing_text = context.chat_data['building']
    level_text = context.chat_data['level']
    room_no_text = context.chat_data['chosen_room']
    start_time_text = context.chat_data['start_time'].strftime("%H%M")
    end_time_text = context.chat_data['end_time'].strftime("%H%M")

    date_text = context.chat_data['date'].strftime("%y-%m-%d")

    val = (builing_text, level_text, room_no_text, start_time_text, end_time_text, date_text)
    cur.execute("INSERT INTO"
                " studentsavers.rooms(building, level, room_no, start_time,end_time,date) VALUES (%s,%s,%s,%s, "
                "%s,%s) "
                , val)

    con.commit()

    return SUCCESSFUL_CHECK_IN


def show_successful_check_in_msg(update, context):
    text = 'You have successfully check in to ' + context.chat_data['chosen_room'] \
           + ' from ' + context.chat_data['start_time'] + ' to ' + context.chat_data['end_time']

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text)


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

    checking_in_convo = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_available_room, pattern='^check-in$')],

        states={
            SELECTED_ROOM: [CallbackQueryHandler(show_check_in_data)],
            SUCCESSFUL_CHECK_IN: [MessageHandler(Filters.text, ask_for_input)]

        },

        fallbacks=[
            CallbackQueryHandler(show_check_in_data),
            CommandHandler('stop', stop_nested)
        ],

        map_to_parent={
            # Return to second level menu
            END: select_feature,
            # End conversation alltogether
            STOPPING: STOPPING,
        }
    )

    # Set up third level ConversationHandler (collecting features)
    input_time_convo = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_feature,
                                           pattern='^' + 'Level B1' + '$|^' + 'Level 1' + '$|^' +
                                                   'Level 2' + '$|^' + 'Level 3' + '$|^' + 'Level 4' + '$')],

        states={
            SELECTING_FEATURE: [CallbackQueryHandler(ask_for_input,
                                                     pattern='^(?!' + str(END) + ').*$')],
            TYPING: [MessageHandler(Filters.text, save_input)],
            SHOWING: [checking_in_convo]

        },

        fallbacks=[
            CallbackQueryHandler(show_data),
            CommandHandler('stop', stop_nested)
        ],

        map_to_parent={
            # Return to second level menu
            END: SELECTING_LEVEL,
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


if __name__ == '__main__':
    main()
