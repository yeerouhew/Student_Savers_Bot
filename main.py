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
SELECT_BUILDING2 = map(chr, range(6, 7))
SELECTING_LEVEL2 = map(chr, range(7, 8))
FINISH_SELECTING_LEVEL2 = map(chr, range(8, 9))
CHECK_IN_TIME = map(chr, range(9, 10))
SUCCESSFUL_CHECK_IN = map(chr, range(10, 11))
CHECK_OUT = map(chr, range(11, 12))
CHOOSE_CHECK_OUT_TIME = map(chr, range(12, 13))

# State definitions for descriptions conversation
TYPING, SAVE_TIMING = map(chr, range(13, 15))

SELECTED_ROOM = map(chr, range(15, 16))

# Meta states
STOPPING, SHOWING = map(chr, range(16, 18))

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


# Top level conversation callbacks
def start(update, context):
    text = 'Hi, welcome to Studentsavers bot. Glad to have you here. What do you want to do? Room Searching is only ' \
           'available for SoC buildings. To abort, simply type /stop.'
    buttons = [[
        InlineKeyboardButton(text='Event Handling', callback_data=str(EVENT_HANDLING)),
        InlineKeyboardButton(text='Room Searching', callback_data=str(ROOM_SEARCHING))
    ]]

    context.chat_data["tele-username"] = update.message.from_user.username

    context.chat_data["date"] = datetime.datetime.now(pytz.timezone('Asia/Singapore'))
    context.chat_data["day"] = datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime("%A")

    keyboard = InlineKeyboardMarkup(buttons)

    update.message.reply_text(text=text, reply_markup=keyboard)

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

    start_time_string = start_time.strftime("%H%M")
    end_time_string = end_time.strftime("%H%M")

    date_string = date.strftime("%Y-%m-%d")
    values = (date_string, start_time_string, end_time_string)

    cur.execute("SELECT DISTINCT room_no FROM studentsavers.rooms WHERE date=%s AND start_time=%s AND end_time=%s;",
                values)

    sqlresult = cur.fetchall()
    available_rooms = list(dict.fromkeys(available_rooms))

    for checked_in_rooms in sqlresult:
        checked_in_rooms = ''.join(''.join(map(str, checked_in_rooms)).split('),'))
        for avail_room in available_rooms:
            if avail_room == checked_in_rooms:
                available_rooms.remove(avail_room)

    return available_rooms


def show_data(update, context):
    if context.chat_data["building"] == "COMS1":
        room_label = roomSearch.com1_data(context.chat_data["level"])

    else:
        room_label = roomSearch.com2_data(context.chat_data["level"])
        print(room_label)

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
    text = 'Choose your action:'

    buttons = [[
        InlineKeyboardButton(text='COMS1', callback_data='COMS1'),
        InlineKeyboardButton(text='COMS2', callback_data='COMS2')
    ], [
        InlineKeyboardButton(text='Check In', callback_data='checkin'),
        InlineKeyboardButton(text='Check Out', callback_data='checkout')
    ],
        [
            InlineKeyboardButton(text='Back', callback_data=str(END))
        ]]

    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return SELECT_BUILDING


def select_building2(update, context):
    text = 'Choose a building:'
    buttons = [[
        InlineKeyboardButton(text='COMS1', callback_data='COMS1_check-in'),
        InlineKeyboardButton(text='COMS2', callback_data='COMS2_check-in')
    ],
        [
            InlineKeyboardButton(text='Back', callback_data=str(END))
        ]]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return SELECT_BUILDING


def select_level(update, context):
    context.chat_data['building'] = update.callback_query.data

    text = 'Choose your level: '

    if update.callback_query.data == 'COMS1':
        buttons = [[
            InlineKeyboardButton(text='Level B1', callback_data='LevelB1'),
            InlineKeyboardButton(text='Level 1', callback_data='Level1')
        ], [
            InlineKeyboardButton(text='Level 2', callback_data='Level2'),
            InlineKeyboardButton(text='Back', callback_data=str(END))
        ]]

        keyboard = InlineKeyboardMarkup(buttons)

        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

        return SELECTING_LEVEL

    elif update.callback_query.data == 'COMS1_check-in':
        buttons = [[
            InlineKeyboardButton(text='Level B1', callback_data='LevelB1_check-in'),
            InlineKeyboardButton(text='Level 1', callback_data='Level1_check-in')
        ], [
            InlineKeyboardButton(text='Level 2', callback_data='Level2_check-in'),
            InlineKeyboardButton(text='Back', callback_data=str(END))
        ]]

        keyboard = InlineKeyboardMarkup(buttons)

        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
        return SELECTING_LEVEL2

    elif update.callback_query.data == 'COMS2_check-in':
        buttons = [[
            InlineKeyboardButton(text='Level 1', callback_data='Level1_check-in'),
            InlineKeyboardButton(text='Level 2', callback_data='Level2_check-in'),
        ], [
            InlineKeyboardButton(text='Level 3', callback_data='Level3_check-in'),
            InlineKeyboardButton(text='Level 4', callback_data='Level4_check-in')],
        ]

        keyboard = InlineKeyboardMarkup(buttons)

        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
        return SELECTING_LEVEL2

    elif update.callback_query.data == 'checkin':
        return SELECT_BUILDING2

    elif update.callback_query.data == 'checkout':
        buttons = [];

        cur.execute("SELECT DISTINCT room_no FROM studentsavers.rooms WHERE username = %s",
                    [context.chat_data["tele-username"]])

        result = cur.fetchall()

        # check if result is empty:
        if len(result) > 0:
            text = 'Choose a room to check out from: '
            for room in result:
                rooms = ''.join(''.join(map(str, room)).split('),'))
                buttons.append([InlineKeyboardButton(text=str(rooms), callback_data=rooms)])
                keyboard = InlineKeyboardMarkup(buttons)
                update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
        else:
            text = 'No rooms to check out from'
            update.callback_query.edit_message_text(text=text)

        return CHECK_OUT

    else:
        text += '\n' + " (Data for official lesson is only available for level 1)"
        buttons = [[
            InlineKeyboardButton(text='Level 1', callback_data='Level1'),
            InlineKeyboardButton(text='Level 2', callback_data='Level2'),
        ], [
            InlineKeyboardButton(text='Level 3', callback_data='Level3'),
            InlineKeyboardButton(text='Level 4', callback_data='Level4')],
        ]
        keyboard = InlineKeyboardMarkup(buttons)

        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
        return SELECTING_LEVEL


# used for check-in
def show_all_level(update, context):
    context.chat_data['level'] = update.callback_query.data
    print(update.callback_query.data)
    buttons = []

    if context.chat_data["building"] == "COMS1_check-in":

        all_rooms_coms1 = roomSearch.com1_data(str(update.callback_query.data).split('_')[0])
        text = 'Choose a room to check into: '

        for room in all_rooms_coms1:
            buttons.append([InlineKeyboardButton(text=str(room), callback_data=room)])
            keyboard = InlineKeyboardMarkup(buttons)
            update.callback_query.answer()
            update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    else:
        all_rooms_coms2 = roomSearch.com2_data(str(update.callback_query.data).split('_')[0])
        text = 'Choose a room to check into: '

        for room in all_rooms_coms2:
            buttons.append([InlineKeyboardButton(text=str(room), callback_data=room)])
            keyboard = InlineKeyboardMarkup(buttons)
            update.callback_query.answer()
            update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return FINISH_SELECTING_LEVEL2


def finsh_selecting_level2(update, context):
    context.chat_data['chosen_room'] = update.callback_query.data

    text = 'Please enter time to check in in the following way:  HH:MM format to HH:MM format.'

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text)

    return CHECK_IN_TIME


def save_input_checkin(update, context):
    message = update.message.text.replace("to", " ")
    context.chat_data['start_time'] = datetime.datetime.strptime(message.split()[0], '%H:%M').time()
    context.chat_data['end_time'] = datetime.datetime.strptime(message.split()[1], '%H:%M').time()

    return confirm_time_checkin(update, context)


def confirm_time_checkin(update, context):
    text = 'Got it! Do click on the respective buttons to move on.'

    buttons = [[
        InlineKeyboardButton(text='Edit', callback_data='TIME'),
        InlineKeyboardButton(text='Done', callback_data=str(END)),
    ]]

    keyboard2 = InlineKeyboardMarkup(buttons)

    update.message.reply_text(text=text, reply_markup=keyboard2)

    return SUCCESSFUL_CHECK_IN


def check_out_service(update, context):
    context.chat_data["checkout_room"] = update.callback_query.data
    text = 'Choose timing to check-out from:'

    cur.execute("SELECT DISTINCT start_time, end_time FROM studentsavers.rooms WHERE room_no = %s AND username = %s ",
                [update.callback_query.data, context.chat_data["tele-username"]])

    time_result = cur.fetchall()

    buttons = [];
    for timing in time_result:
        timing = ('').join(('-'.join(map(str, timing)).split('),')))
        buttons.append([InlineKeyboardButton(text=timing, callback_data=timing)])

    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return CHOOSE_CHECK_OUT_TIME


def choose_check_out_time(update, context):
    date_text = context.chat_data['date'].strftime("%Y-%m-%d")

    cur.execute(
        "DELETE FROM studentsavers.rooms WHERE room_no = %s AND start_time = %s AND end_time = %s AND date =%s AND username = %s",
        [context.chat_data["checkout_room"], str(update.callback_query.data).split('-')[0],
         str(update.callback_query.data).split('-')[1],
         date_text, context.chat_data["tele-username"]])

    con.commit()

    text = "You have successfully check out."

    buttons = [[
        InlineKeyboardButton(text='Edit', callback_data='TIME'),
        InlineKeyboardButton(text='Done', callback_data=str(END)),
    ]]

    keyboard2 = InlineKeyboardMarkup(buttons)
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard2)


def end_second_level(update, context):
    """Return to top level conversation."""
    start(update, context)

    return END


def ask_for_input(update, context):
    """Prompt user to input data for selected feature."""
    text = 'Please enter time in the following way:  HH:MM format to HH:MM format.'

    context.chat_data['level'] = update.callback_query.data

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text)

    return TYPING


def save_input(update, context):
    """Save input for time """

    message = update.message.text.replace("to", " ")
    context.chat_data['start_time'] = datetime.datetime.strptime(message.split()[0], '%H:%M').time()
    context.chat_data['end_time'] = datetime.datetime.strptime(message.split()[1], '%H:%M').time()

    return confirm_time(update, context)


def confirm_time(update, context):
    text = 'Got it! Do click on the respective buttons to move on.'

    buttons = [[
        InlineKeyboardButton(text='Edit', callback_data='TIME'),
        InlineKeyboardButton(text='Done', callback_data=str(END)),
    ]]

    keyboard2 = InlineKeyboardMarkup(buttons)

    update.message.reply_text(text=text, reply_markup=keyboard2)

    return SAVE_TIMING


def check_in_successfully(update, context):
    builing_text = str(context.chat_data['building']).split("_")[0]
    level_text = context.chat_data['level']
    room_no_text = context.chat_data['chosen_room']
    start_time_text = context.chat_data['start_time'].strftime("%H%M")
    end_time_text = context.chat_data['end_time'].strftime("%H%M")

    date_text = context.chat_data['date'].strftime("%Y-%m-%d")
    username_text = context.chat_data["tele-username"]

    val = (
        builing_text, level_text, room_no_text, start_time_text, end_time_text, date_text,
        username_text)
    cur.execute("INSERT INTO"
                " studentsavers.rooms(building, level, room_no, start_time, end_time, date, username) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s) "
                , val)
    con.commit()

    text = 'You have successfully check in to ' + room_no_text \
           + ' from ' + start_time_text + ' to ' + end_time_text

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text)


def select_available_room(update, context):
    text2 = 'Choose a room:'

    buttons = [];
    if len(context.chat_data["avail_rooms"]) > 0:
        for rooms in context.chat_data["avail_rooms"]:
            buttons.append([InlineKeyboardButton(text=rooms, callback_data=rooms)])

    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text2, reply_markup=keyboard)

    return SELECTED_ROOM


def checking_in(update, context):
    context.chat_data['chosen_room'] = update.callback_query.data

    builing_text = context.chat_data['building']
    level_text = context.chat_data['level']
    room_no_text = context.chat_data['chosen_room']
    start_time_text = context.chat_data['start_time'].strftime("%H%M")
    end_time_text = context.chat_data['end_time'].strftime("%H%M")

    date_text = context.chat_data['date'].strftime("%Y-%m-%d")

    val = (
        builing_text, level_text, room_no_text, start_time_text, end_time_text, date_text,
        context.chat_data["tele-username"])
    cur.execute("INSERT INTO"
                " studentsavers.rooms(building, level, room_no, start_time, end_time, date, username) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s) "
                , val)

    con.commit()

    text2 = 'You have successfully check in to ' + room_no_text \
            + ' from ' + start_time_text + ' to ' + end_time_text

    buttons = [[
        InlineKeyboardButton(text='Done')
    ]]

    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.edit_message_text(text=text2, reply_markup=keyboard)


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
        entry_points=[CallbackQueryHandler(show_data)],

        states={
            SHOWING: [CallbackQueryHandler(select_available_room)],
            SELECTED_ROOM: [CallbackQueryHandler(checking_in)]
        },

        fallbacks=[
            CallbackQueryHandler(checking_in),
            CommandHandler('stop', stop_nested)
        ],

        map_to_parent={
            # Return to second level menu
            # END:,
            # End conversation alltogether
            STOPPING: STOPPING,
        }
    )

    # Set up third level ConversationHandler (collecting features)
    input_time_convo = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_for_input,
                                           pattern='^{0}$|^{1}$|^{2}$|^${3}|^${4}|$'
                                           .format('LevelB1',
                                                   'Level1',
                                                   'Level2',
                                                   'Level3',
                                                   'Level4'
                                                   ))],

        states={
            TYPING: [MessageHandler(Filters.text, save_input)],
            SAVE_TIMING: [checking_in_convo]
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
                                                   pattern='^{0}$|^{1}$|^{2}$|^{3}$|^{4}$|^{5}$'.format('COMS1',
                                                                                                        'COMS2',
                                                                                                        'checkin',
                                                                                                        'checkout',
                                                                                                        'COMS1_check-in',
                                                                                                        'COMS2_check-in'
                                                                                                        ))],
            SELECT_BUILDING2: [CallbackQueryHandler(select_building2)],
            CHECK_OUT: [CallbackQueryHandler(check_out_service)],
            CHOOSE_CHECK_OUT_TIME: [CallbackQueryHandler(choose_check_out_time)],
            SELECTING_LEVEL2: [CallbackQueryHandler(show_all_level, pattern='^{0}$|^{1}$|^{2}$|^{3}$|^{4}$'
                                                    .format('LevelB1_check-in',
                                                            'Level1_check-in',
                                                            'Level2_check-in',
                                                            'Level3_check-in',
                                                            'Level4_check-in'))],
            FINISH_SELECTING_LEVEL2: [CallbackQueryHandler(finsh_selecting_level2)],
            CHECK_IN_TIME: [MessageHandler(Filters.text, save_input_checkin)],
            SUCCESSFUL_CHECK_IN: [CallbackQueryHandler(check_in_successfully)],

            SELECTING_LEVEL: [input_time_convo]
        },

        fallbacks=[
            CallbackQueryHandler(end_second_level, pattern='^' + str(END) + '$'),
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
