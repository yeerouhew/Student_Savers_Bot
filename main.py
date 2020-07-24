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

# States for Event Handling
EVENT_DETAILS = map(chr, range(18, 19))
EVENT_DATE = map(chr, range(19, 20))
TIMER = map(chr, range(20, 21))
EVENT_DATE = map(chr, range(21, 22))
EMAIL = map(chr, range(22, 23))
CALENDAR = map(chr, range(23, 24))
CONFIRM_ADD_CAL = map(chr, range(24, 25))
EVENT_TIME = map(chr, range(25, 26))
HANDLING_EVENT2 = map(chr, range(26, 27))

import re
from scheduler import book_timeslot
from telegram_cal import create_calendar
from telegram_cal import process_calendar_selection

# Shortcut for ConversationHandler.END
END = ConversationHandler.END

bot_data = {
    'event_name': '',
    'event_detail': '',
    'event_date':'',
    'event_time':''
}

PORT = int(os.environ.get('PORT', 5000))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
# TOKEN = "1278045157:AAFjUYhhg50425eKh6cTKpF9APpzwjOdYiU"
TOKEN = "1137969152:AAGNcHP2ZAfRm2tPZmK6xJFuex1LIa_EoeM"

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


# def callNusmodApi(date, day, start_time, end_time, list_of_rooms):
#     url = "https://api.nusmods.com/v2/2019-2020/semesters/2/venueInformation.json"
#
#     http = urllib3.PoolManager()
#     json_obj = http.request('GET', url)
#     text = json.loads(json_obj.data.decode('UTF-8'))
#
#     current_weekNo = roomSearch.return_weekNo(date)
#     available_rooms = []
#
#     for rooms in list_of_rooms:
#
#         if text[rooms][0]["classes"]:
#
#             for index in range(0, len(text[rooms][0]["classes"])):
#
#                 weekNo = text[rooms][0]["classes"][index]["weeks"]
#
#                 for num in weekNo:
#
#                     if int(current_weekNo) == num:
#
#                         if text[rooms][0]["classes"][index]["day"] == day:
#
#                             start_classTime = datetime.datetime.strptime(text[rooms][0]["classes"][index]["startTime"],
#                                                                          '%H%M').time()
#
#                             end_classTime = datetime.datetime.strptime(text[rooms][0]["classes"][index]["endTime"],
#                                                                        '%H%M').time()
#
#                             if start_time < start_classTime and end_time < end_classTime:
#                                 available_rooms.append(rooms)
#                             elif available_rooms.count(rooms) > 0:
#                                 available_rooms.remove(rooms)
#                                 break
#                         else:
#                             available_rooms.append(rooms)
#
#     start_time_string = start_time.strftime("%H%M")
#     end_time_string = end_time.strftime("%H%M")
#
#     date_string = date.strftime("%Y-%m-%d")
#     values = (date_string, start_time_string, end_time_string)
#
#     cur.execute("SELECT DISTINCT room_no FROM studentsavers.rooms WHERE date=%s AND start_time=%s AND end_time=%s;",
#                 values)
#
#     sqlresult = cur.fetchall()
#     available_rooms = list(dict.fromkeys(available_rooms))
#
#     for checked_in_rooms in sqlresult:
#         checked_in_rooms = ''.join(''.join(map(str, checked_in_rooms)).split('),'))
#         for avail_room in available_rooms:
#             if avail_room == checked_in_rooms:
#                 available_rooms.remove(avail_room)
#
#     return available_rooms
#
#
# def show_data(update, context):
#     if context.chat_data["building"] == "COMS1":
#         room_label = roomSearch.com1_data(context.chat_data["level"])
#
#     else:
#         room_label = roomSearch.com2_data(context.chat_data["level"])
#         print(room_label)
#
#     available_rooms_data = callNusmodApi(context.chat_data["date"], context.chat_data["day"],
#                                          context.chat_data["start_time"], context.chat_data["end_time"],
#                                          room_label)
#     if len(available_rooms_data) > 0:
#         text = 'Rooms available are : '
#
#         for rooms in available_rooms_data:
#             text += '\n' + rooms
#
#     else:
#         text = " No available room found"
#
#     context.chat_data["avail_rooms"] = available_rooms_data
#
#     buttons = [[
#         InlineKeyboardButton(text='Check in', callback_data='check-in'),
#         InlineKeyboardButton(text='Back', callback_data=str(END))
#     ]]
#
#     keyboard = InlineKeyboardMarkup(buttons)
#
#     update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
#
#     return SHOWING
#
#
def stop(update, context):
    """End Conversation by command."""
    update.message.reply_text('See you around!')

    return END
#
#
# # Second level conversation callbacks
# def select_building(update, context):
#     text = 'Choose your action:'
#
#     buttons = [[
#         InlineKeyboardButton(text='COMS1', callback_data='COMS1'),
#         InlineKeyboardButton(text='COMS2', callback_data='COMS2')
#     ], [
#         InlineKeyboardButton(text='Check In', callback_data='checkin'),
#         InlineKeyboardButton(text='Check Out', callback_data='checkout')
#     ],
#         [
#             InlineKeyboardButton(text='Back', callback_data=str(END))
#         ]]
#
#     keyboard = InlineKeyboardMarkup(buttons)
#
#     update.callback_query.answer()
#     update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
#
#     return SELECT_BUILDING
#
#
# def select_building2(update, context):
#     text = 'Choose a building:'
#     buttons = [[
#         InlineKeyboardButton(text='COMS1', callback_data='COMS1_check-in'),
#         InlineKeyboardButton(text='COMS2', callback_data='COMS2_check-in')
#     ],
#         [
#             InlineKeyboardButton(text='Back', callback_data=str(END))
#         ]]
#     keyboard = InlineKeyboardMarkup(buttons)
#
#     update.callback_query.answer()
#     update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
#
#     return SELECT_BUILDING
#
#
# def select_level(update, context):
#     context.chat_data['building'] = update.callback_query.data
#
#     text = 'Choose your level: '
#
#     if update.callback_query.data == 'COMS1':
#         buttons = [[
#             InlineKeyboardButton(text='Level B1', callback_data='LevelB1'),
#             InlineKeyboardButton(text='Level 1', callback_data='Level1')
#         ], [
#             InlineKeyboardButton(text='Level 2', callback_data='Level2'),
#             InlineKeyboardButton(text='Back', callback_data=str(END))
#         ]]
#
#         keyboard = InlineKeyboardMarkup(buttons)
#
#         update.callback_query.answer()
#         update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
#
#         return SELECTING_LEVEL
#
#     elif update.callback_query.data == 'COMS1_check-in':
#         buttons = [[
#             InlineKeyboardButton(text='Level B1', callback_data='LevelB1_check-in'),
#             InlineKeyboardButton(text='Level 1', callback_data='Level1_check-in')
#         ], [
#             InlineKeyboardButton(text='Level 2', callback_data='Level2_check-in'),
#             InlineKeyboardButton(text='Back', callback_data=str(END))
#         ]]
#
#         keyboard = InlineKeyboardMarkup(buttons)
#
#         update.callback_query.answer()
#         update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
#         return SELECTING_LEVEL2
#
#     elif update.callback_query.data == 'COMS2_check-in':
#         buttons = [[
#             InlineKeyboardButton(text='Level 1', callback_data='Level1_check-in'),
#             InlineKeyboardButton(text='Level 2', callback_data='Level2_check-in'),
#         ], [
#             InlineKeyboardButton(text='Level 3', callback_data='Level3_check-in'),
#             InlineKeyboardButton(text='Level 4', callback_data='Level4_check-in')],
#         ]
#
#         keyboard = InlineKeyboardMarkup(buttons)
#
#         update.callback_query.answer()
#         update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
#         return SELECTING_LEVEL2
#
#     elif update.callback_query.data == 'checkin':
#         return SELECT_BUILDING2
#
#     elif update.callback_query.data == 'checkout':
#         buttons = [];
#
#         cur.execute("SELECT DISTINCT room_no FROM studentsavers.rooms WHERE username = %s",
#                     [context.chat_data["tele-username"]])
#
#         result = cur.fetchall()
#
#         # check if result is empty:
#         if len(result) > 0:
#             text = 'Choose a room to check out from: '
#             for room in result:
#                 rooms = ''.join(''.join(map(str, room)).split('),'))
#                 buttons.append([InlineKeyboardButton(text=str(rooms), callback_data=rooms)])
#                 keyboard = InlineKeyboardMarkup(buttons)
#                 update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
#         else:
#             text = 'No rooms to check out from'
#             update.callback_query.edit_message_text(text=text)
#
#         return CHECK_OUT
#
#     else:
#         text += '\n' + " (Data for official lesson is only available for level 1)"
#         buttons = [[
#             InlineKeyboardButton(text='Level 1', callback_data='Level1'),
#             InlineKeyboardButton(text='Level 2', callback_data='Level2'),
#         ], [
#             InlineKeyboardButton(text='Level 3', callback_data='Level3'),
#             InlineKeyboardButton(text='Level 4', callback_data='Level4')],
#         ]
#         keyboard = InlineKeyboardMarkup(buttons)
#
#         update.callback_query.answer()
#         update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
#         return SELECTING_LEVEL
#
#
# # used for check-in
# def show_all_level(update, context):
#     context.chat_data['level'] = update.callback_query.data
#     print(update.callback_query.data)
#     buttons = []
#
#     if context.chat_data["building"] == "COMS1_check-in":
#
#         all_rooms_coms1 = roomSearch.com1_data(str(update.callback_query.data).split('_')[0])
#         text = 'Choose a room to check into: '
#
#         for room in all_rooms_coms1:
#             buttons.append([InlineKeyboardButton(text=str(room), callback_data=room)])
#             keyboard = InlineKeyboardMarkup(buttons)
#             update.callback_query.answer()
#             update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
#
#     else:
#         all_rooms_coms2 = roomSearch.com2_data(str(update.callback_query.data).split('_')[0])
#         text = 'Choose a room to check into: '
#
#         for room in all_rooms_coms2:
#             buttons.append([InlineKeyboardButton(text=str(room), callback_data=room)])
#             keyboard = InlineKeyboardMarkup(buttons)
#             update.callback_query.answer()
#             update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
#
#     return FINISH_SELECTING_LEVEL2
#
#
# def finsh_selecting_level2(update, context):
#     context.chat_data['chosen_room'] = update.callback_query.data
#
#     text = 'Please enter time to check in in the following way:  HH:MM format to HH:MM format.'
#
#     update.callback_query.answer()
#     update.callback_query.edit_message_text(text=text)
#
#     return CHECK_IN_TIME
#
#
# def save_input_checkin(update, context):
#     message = update.message.text.replace("to", " ")
#     context.chat_data['start_time'] = datetime.datetime.strptime(message.split()[0], '%H:%M').time()
#     context.chat_data['end_time'] = datetime.datetime.strptime(message.split()[1], '%H:%M').time()
#
#     return confirm_time_checkin(update, context)
#
#
# def confirm_time_checkin(update, context):
#     text = 'Got it! Do click on the respective buttons to move on.'
#
#     buttons = [[
#         InlineKeyboardButton(text='Edit', callback_data='TIME'),
#         InlineKeyboardButton(text='Done', callback_data=str(END)),
#     ]]
#
#     keyboard2 = InlineKeyboardMarkup(buttons)
#
#     update.message.reply_text(text=text, reply_markup=keyboard2)
#
#     return SUCCESSFUL_CHECK_IN
#
#
# def check_out_service(update, context):
#     context.chat_data["checkout_room"] = update.callback_query.data
#     text = 'Choose timing to check-out from:'
#
#     cur.execute("SELECT DISTINCT start_time, end_time FROM studentsavers.rooms WHERE room_no = %s AND username = %s ",
#                 [update.callback_query.data, context.chat_data["tele-username"]])
#
#     time_result = cur.fetchall()
#
#     buttons = [];
#     for timing in time_result:
#         timing = ('').join(('-'.join(map(str, timing)).split('),')))
#         buttons.append([InlineKeyboardButton(text=timing, callback_data=timing)])
#
#     keyboard = InlineKeyboardMarkup(buttons)
#
#     update.callback_query.answer()
#     update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
#
#     return CHOOSE_CHECK_OUT_TIME
#
#
# def choose_check_out_time(update, context):
#     date_text = context.chat_data['date'].strftime("%Y-%m-%d")
#
#     cur.execute(
#         "DELETE FROM studentsavers.rooms WHERE room_no = %s AND start_time = %s AND end_time = %s AND date =%s AND username = %s",
#         [context.chat_data["checkout_room"], str(update.callback_query.data).split('-')[0],
#          str(update.callback_query.data).split('-')[1],
#          date_text, context.chat_data["tele-username"]])
#
#     con.commit()
#
#     text = "You have successfully check out."
#
#     buttons = [[
#         InlineKeyboardButton(text='Edit', callback_data='TIME'),
#         InlineKeyboardButton(text='Done', callback_data=str(END)),
#     ]]
#
#     keyboard2 = InlineKeyboardMarkup(buttons)
#     update.callback_query.edit_message_text(text=text, reply_markup=keyboard2)
#
#
def end_second_level(update, context):
    """Return to top level conversation."""
    start(update, context)

    return END
#
#
# def ask_for_input(update, context):
#     """Prompt user to input data for selected feature."""
#     text = 'Please enter time in the following way:  HH:MM format to HH:MM format.'
#
#     context.chat_data['level'] = update.callback_query.data
#
#     update.callback_query.answer()
#     update.callback_query.edit_message_text(text=text)
#
#     return TYPING
#
#
# def save_input(update, context):
#     """Save input for time """
#
#     message = update.message.text.replace("to", " ")
#     context.chat_data['start_time'] = datetime.datetime.strptime(message.split()[0], '%H:%M').time()
#     context.chat_data['end_time'] = datetime.datetime.strptime(message.split()[1], '%H:%M').time()
#
#     return confirm_time(update, context)
#
#
# def confirm_time(update, context):
#     text = 'Got it! Do click on the respective buttons to move on.'
#
#     buttons = [[
#         InlineKeyboardButton(text='Edit', callback_data='TIME'),
#         InlineKeyboardButton(text='Done', callback_data=str(END)),
#     ]]
#
#     keyboard2 = InlineKeyboardMarkup(buttons)
#
#     update.message.reply_text(text=text, reply_markup=keyboard2)
#
#     return SAVE_TIMING
#
#
# def check_in_successfully(update, context):
#     builing_text = str(context.chat_data['building']).split("_")[0]
#     level_text = context.chat_data['level']
#     room_no_text = context.chat_data['chosen_room']
#     start_time_text = context.chat_data['start_time'].strftime("%H%M")
#     end_time_text = context.chat_data['end_time'].strftime("%H%M")
#
#     date_text = context.chat_data['date'].strftime("%Y-%m-%d")
#     username_text = context.chat_data["tele-username"]
#
#     val = (
#         builing_text, level_text, room_no_text, start_time_text, end_time_text, date_text,
#         username_text)
#     cur.execute("INSERT INTO"
#                 " studentsavers.rooms(building, level, room_no, start_time, end_time, date, username) "
#                 "VALUES (%s,%s,%s,%s,%s,%s,%s) "
#                 , val)
#     con.commit()
#
#     text = 'You have successfully check in to ' + room_no_text \
#            + ' from ' + start_time_text + ' to ' + end_time_text
#
#     update.callback_query.answer()
#     update.callback_query.edit_message_text(text=text)
#
#
# def select_available_room(update, context):
#     text2 = 'Choose a room:'
#
#     buttons = [];
#     if len(context.chat_data["avail_rooms"]) > 0:
#         for rooms in context.chat_data["avail_rooms"]:
#             buttons.append([InlineKeyboardButton(text=rooms, callback_data=rooms)])
#
#     keyboard = InlineKeyboardMarkup(buttons)
#
#     update.callback_query.answer()
#     update.callback_query.edit_message_text(text=text2, reply_markup=keyboard)
#
#     return SELECTED_ROOM
#
#
# def checking_in(update, context):
#     context.chat_data['chosen_room'] = update.callback_query.data
#
#     builing_text = context.chat_data['building']
#     level_text = context.chat_data['level']
#     room_no_text = context.chat_data['chosen_room']
#     start_time_text = context.chat_data['start_time'].strftime("%H%M")
#     end_time_text = context.chat_data['end_time'].strftime("%H%M")
#
#     date_text = context.chat_data['date'].strftime("%Y-%m-%d")
#
#     val = (
#         builing_text, level_text, room_no_text, start_time_text, end_time_text, date_text,
#         context.chat_data["tele-username"])
#     cur.execute("INSERT INTO"
#                 " studentsavers.rooms(building, level, room_no, start_time, end_time, date, username) "
#                 "VALUES (%s,%s,%s,%s,%s,%s,%s) "
#                 , val)
#
#     con.commit()
#
#     text2 = 'You have successfully check in to ' + room_no_text \
#             + ' from ' + start_time_text + ' to ' + end_time_text
#
#     buttons = [[
#         InlineKeyboardButton(text='Done')
#     ]]
#
#     keyboard = InlineKeyboardMarkup(buttons)
#     update.callback_query.edit_message_text(text=text2, reply_markup=keyboard)
#
#
def stop_nested(update, context):
    """Completely end conversation from within nested conversation."""
    update.message.reply_text('Hope to see you again!.')

    return STOPPING


# Sending reminders

def event_handling(update, context):
    """Prompt users for event name"""
    text = 'Please enter the event name'

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text)

    return HANDLING_EVENT

def edit_event_name(update, context):
    text = 'Please enter the event name'

    update.message.reply_text(text=text)

    return HANDLING_EVENT2


def set_event_name(update, context):
    message = update.message.text
    context.chat_data['event_name'] = message

    text = 'Please enter the event detail:'

    update.message.reply_text(text=text)

    return EVENT_DETAILS


def set_event_details(update, context):
    message = update.message.text
    context.chat_data['event_detail'] = message

    text = 'Please select a date'

    update.message.reply_text(text=text, reply_markup=create_calendar())

    return EVENT_DATE


def set_event_date(update, context):
    bot = context.bot

    selected, date = process_calendar_selection(update, context)

    context.chat_data['event_date'] = date.strftime("%Y-%m-%d")

    bot.send_message(chat_id=update.callback_query.from_user.id,
                     text="You selected %s" % (date.strftime("%Y-%m-%d")))

    text = 'Please enter the time in the following format: HH:MM'

    bot.send_message(chat_id=update.callback_query.from_user.id, text=text)

    return EVENT_TIME


def set_event_time(update, context):
    message = update.message.text

    context.chat_data['event_time'] = message

    text = 'Please send /confirm to continue, otherwise /edit'

    context.bot.send_message(chat_id = update.message.chat_id, text=text)

    # update.message.reply_text(text=text)

    return TIMER


def set_timer(update, context):
    # Add job to queue
    chat_id = update.message.chat_id

    context.chat_data['chat_id'] = chat_id

    event_datetime = context.chat_data['event_date'] + ' ' + context.chat_data['event_time']

    try:
        datetimeobj = datetime.datetime.strptime(event_datetime, '%Y-%m-%d %H:%M')
        # datetimeobj2 = datetimeobj - datetime.timedelta(days=1)
        today = datetime.datetime.now()
        diff = datetimeobj - today
        due = diff.total_seconds()
        logger.info(due)
        if due < 0:
            update.message.reply_text('Sorry we can not go back!')
            return

        event_name = context.chat_data['event_name']
        event_detail = context.chat_data['event_detail']
        event_date = context.chat_data['event_date']
        event_time = context.chat_data['event_time']

        customize_stuff = {
            'chat_id': chat_id,
            'event_name': event_name,
            'event_detail': event_detail,
            'event_date': event_date,
            'event_time': event_time
        }

        new_job = context.job_queue.run_once(alarm, due, context=customize_stuff)
        context.chat_data['job'] = new_job

        val = (event_name, event_detail, event_date, event_time, context.chat_data["tele-username"], chat_id)
        cur.execute("INSERT INTO"
                    " studentsavers.event(event_name, event_details, event_date, event_time, username, chat_id ) "
                    "VALUES (%s,%s,%s,%s,%s,%s) "
                    , val)
        con.commit()

        update.message.reply_text('Reminder has been successfully set for ' + event_name)

        return add_to_calendar(update, context)

    except (IndexError, ValueError):
        return EVENT_DETAILS


def alarm(context):
    event = 'Reminder \n\n' + context.job.context['event_name'] + '\n' + context.job.context['event_detail'] + '\non ' + context.job.context['event_date'] + ' at ' + context.job.context['event_time']

    context.bot.send_message(context.job.context['chat_id'], text=event)


# Adding to google calendar

def add_to_calendar(update, context):
    text = 'Would you like to add the event to Google Calendar? \n/yes to continue and /no to go back to main menu.'

    update.message.reply_text(text=text)

    return CONFIRM_ADD_CAL


def check_email(email):
    regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
    if(re.search(regex, email)):
        logger.info("Valid email")
        return True
    else:
        logger.info("Invalid email")
        return False

def ask_confirm_add_cal(update, context):
    message = update.message.text

    context.chat_data['confirm_add_cal'] = message

    text = 'Please enter your email address. Otherwise, send /cancel'

    update.message.reply_text(text=text)

    return EMAIL

def ask_for_email(update, context):
    message = update.message.text

    context.chat_data['user_email'] = message

    text = 'Got it! Please send /confirm to add event to Google Calendar. \nOtherwise, send /cancel'

    update.message.reply_text(text=text)

    return CALENDAR

def confirm_add_to_calendar(update, context):
    input_email = context.chat_data['user_email']
    event_name = context.chat_data['event_name']
    event_detail = context.chat_data['event_detail']
    event_date = context.chat_data['event_date']
    event_time = context.chat_data['event_time']

    if(check_email(input_email) == True):
        response = book_timeslot(event_name, event_detail, event_date, event_time, input_email)
        if (response == True):
            text = 'Event has been added to Google Calendar'
        else:
            text = 'Errors'

        update.message.reply_text(text)
    else:
        text = 'Please enter a valid email'
        update.message.reply_text(text)


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

    # checking_in_convo = ConversationHandler(
    #     entry_points=[CallbackQueryHandler(show_data)],
    #
    #     states={
    #         SHOWING: [CallbackQueryHandler(select_available_room)],
    #         SELECTED_ROOM: [CallbackQueryHandler(checking_in)]
    #     },
    #
    #     fallbacks=[
    #         CallbackQueryHandler(checking_in),
    #         CommandHandler('stop', stop_nested)
    #     ],
    #
    #     map_to_parent={
    #         # Return to second level menu
    #         # END:,
    #         # End conversation alltogether
    #         STOPPING: STOPPING,
    #     }
    # )

    # Set up third level ConversationHandler (collecting features)
    # input_time_convo = ConversationHandler(
    #     entry_points=[CallbackQueryHandler(ask_for_input,
    #                                        pattern='^{0}$|^{1}$|^{2}$|^${3}|^${4}|$'
    #                                        .format('LevelB1',
    #                                                'Level1',
    #                                                'Level2',
    #                                                'Level3',
    #                                                'Level4'
    #                                                ))],
    #
    #     states={
    #         TYPING: [MessageHandler(Filters.text, save_input)],
    #         SAVE_TIMING: [checking_in_convo]
    #     },
    #
    #     fallbacks=[
    #         CallbackQueryHandler(show_data),
    #         CommandHandler('stop', stop_nested)
    #     ],
    #
    #     map_to_parent={
    #         # Return to second level menu
    #         END: SELECTING_LEVEL,
    #         # End conversation alltogether
    #         STOPPING: STOPPING,
    #     }
    # )

    # Set up second level ConversationHandler (selecting building)
    # choose_building_convo = ConversationHandler(
    #     entry_points=[CallbackQueryHandler(select_building,
    #                                        pattern='^' + str(ROOM_SEARCHING) + '$')],
    #
    #     states={
    #         SELECT_BUILDING: [CallbackQueryHandler(select_level,
    #                                                pattern='^{0}$|^{1}$|^{2}$|^{3}$|^{4}$|^{5}$'.format('COMS1',
    #                                                                                                     'COMS2',
    #                                                                                                     'checkin',
    #                                                                                                     'checkout',
    #                                                                                                     'COMS1_check-in',
    #                                                                                                     'COMS2_check-in'
    #                                                                                                     ))],
    #         SELECT_BUILDING2: [CallbackQueryHandler(select_building2)],
    #         CHECK_OUT: [CallbackQueryHandler(check_out_service)],
    #         CHOOSE_CHECK_OUT_TIME: [CallbackQueryHandler(choose_check_out_time)],
    #         SELECTING_LEVEL2: [CallbackQueryHandler(show_all_level, pattern='^{0}$|^{1}$|^{2}$|^{3}$|^{4}$'
    #                                                 .format('LevelB1_check-in',
    #                                                         'Level1_check-in',
    #                                                         'Level2_check-in',
    #                                                         'Level3_check-in',
    #                                                         'Level4_check-in'))],
    #         FINISH_SELECTING_LEVEL2: [CallbackQueryHandler(finsh_selecting_level2)],
    #         CHECK_IN_TIME: [MessageHandler(Filters.text, save_input_checkin)],
    #         SUCCESSFUL_CHECK_IN: [CallbackQueryHandler(check_in_successfully)],
    #
    #         SELECTING_LEVEL: [input_time_convo]
    #     },
    #
    #     fallbacks=[
    #         CallbackQueryHandler(end_second_level, pattern='^' + str(END) + '$'),
    #         CallbackQueryHandler(end_second_level, pattern='^' + str(END) + '$'),
    #         CommandHandler('stop', stop_nested)
    #     ],
    #
    #     map_to_parent={
    #         # After showing data return to top level menu
    #         SHOWING: SHOWING,
    #         # Return to top level menu
    #         END: SELECTING_ACTION,
    #         # End conversation alltogether
    #         STOPPING: END,
    #     }
    # )


    # Event handling ConversationHandler
    event_handling_convo = ConversationHandler(
        entry_points=[CallbackQueryHandler(event_handling,
                                           pattern='^' + str(EVENT_HANDLING) + '$')],
        states={
            HANDLING_EVENT: [MessageHandler(Filters.text, set_event_name)],
            EVENT_DETAILS: [MessageHandler(Filters.text, set_event_details)],
            EVENT_DATE: [CallbackQueryHandler(set_event_date)],
            EVENT_TIME: [MessageHandler(Filters.text, set_event_time)],
            TIMER: [
                CommandHandler('confirm', set_timer, pass_args=True, pass_job_queue=True , pass_chat_data=True),
                CommandHandler('edit', edit_event_name)
            ],
            CONFIRM_ADD_CAL: [
                CommandHandler('yes', ask_confirm_add_cal),
                CommandHandler('no', end_second_level)
                # MessageHandler(Filters.text, ask_confirm_add_cal)
            ],
            EMAIL: [
                CommandHandler('cancel', end_second_level),
                MessageHandler(Filters.text, ask_for_email)
            ],
            CALENDAR: [
                CommandHandler('confirm', confirm_add_to_calendar),
                CommandHandler('cancel', end_second_level)
            ],
            HANDLING_EVENT2: [MessageHandler(Filters.text, set_event_name)],
        },

        fallbacks=[
            # CallbackQueryHandler(end_second_level, pattern='^' + str(END) + '$'),
            CommandHandler('stop', stop_nested)
        ],

        map_to_parent = {
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
        # choose_building_convo,
        event_handling_convo
    ]

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            SELECTING_ACTION: selection_handlers,
            SELECT_BUILDING: selection_handlers,
            HANDLING_EVENT: selection_handlers,
            STOPPING: [CommandHandler('start', start)],
        },

        fallbacks=[
            CommandHandler('stop', stop)],
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler("h", help))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    # updater.start_polling()
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN)
    # updater.bot.setWebhook('https://student-saversbot.herokuapp.com/' + TOKEN)
    updater.bot.setWebhook('https://student-savers-testing24.herokuapp.com/' + TOKEN)

if __name__ == '__main__':
    main()