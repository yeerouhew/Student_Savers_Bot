import logging
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters
from telegram import InlineKeyboardMarkup
from telegram import InlineKeyboardButton
import datetime
import psycopg2

# deploy to heroku
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
cur.execute(
    "CREATE TABLE IF NOT EXISTS studentsavers.Room (id serial PRIMARY KEY, status varchar, next_availabletime timestamp);")
con.commit()

# State definitions for top level conversation
SELECTING_ACTION, ROOM_SEARCHING, ADDING_SELF, DESCRIBING_SELF = map(chr, range(4))
# State definitions for second level conversation
SELECT_BUILDING, SELECTING_LEVEL = map(chr, range(4, 6))
# State definitions for descriptions conversation
SELECTING_FEATURE, TYPING = map(chr, range(6, 8))
# Meta states
STOPPING, SHOWING = map(chr, range(8, 10))
# Shortcut for ConversationHandler.END
END = ConversationHandler.END

# Different constants for this example
(COMS1, COMS2, EVENT, GENDER, LEVELB1, LEVEL1, LEVEL2, TIME, START_OVER, FEATURES,
 CURRENT_FEATURE, CURRENT_LEVEL) = map(chr, range(10, 22))


# Top level conversation callbacks
def start(update, context):
    """Select an action: Adding parent/child or show data."""
    text = 'Hi, welcome to Studentsavers bot. Glad to have you here.What do you want to do? Room Searching is only ' \
           'available for SoC buildings. To abort, simply type /stop.'
    buttons = [[
        InlineKeyboardButton(text='Event Handling', callback_data=str(ADDING_SELF)),
        InlineKeyboardButton(text='Room Searching', callback_data=str(ROOM_SEARCHING))
    ], [
        InlineKeyboardButton(text='Done', callback_data=str(END))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    # If we're starting over we don't need do send a new message
    if context.user_data.get(START_OVER):
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    else:

        update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START_OVER] = False
    return SELECTING_ACTION


def adding_self(update, context):
    """Add information about youself."""
    context.user_data[CURRENT_LEVEL] = EVENT
    text = 'Okay, please tell me about yourself.'
    button = InlineKeyboardButton(text='Add info', callback_data=str(LEVELB1))
    keyboard = InlineKeyboardMarkup.from_button(button)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return DESCRIBING_SELF


def show_data(update, context):
    """Pretty print gathered data."""

    def prettyprint(user_data, level):
        location = user_data.get(level)
        if not location:
            return '\nNo information yet.'

        text = ''
        if level == EVENT:
            text += ''
        else:

            for location in user_data[level]:
                text += location.get(TIME)

        return text

    ud = context.user_data
    text = '\n\n ' + prettyprint(ud, COMS1)
    text += '\n\n' + prettyprint(ud, COMS2)

    buttons = [[
        InlineKeyboardButton(text='Back', callback_data=str(END))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    ud[START_OVER] = True

    return SHOWING


def stop(update, context):
    """End Conversation by command."""
    update.message.reply_text('Okay, bye.')

    return END


def end(update, context):
    """End conversation from InlineKeyboardButton."""
    update.callback_query.answer()

    text = 'See you around!'
    update.callback_query.edit_message_text(text=text)

    return END


# Second level conversation callbacks
def select_building(update, context):
    """Choose to add a parent or a child."""
    text = 'Choose a building'
    buttons = [[
        InlineKeyboardButton(text='COMS1', callback_data=str(COMS1)),
        InlineKeyboardButton(text='COMS2', callback_data=str(COMS2))
    ], [
        InlineKeyboardButton(text='Show data', callback_data=str(SHOWING)),
        InlineKeyboardButton(text='Back', callback_data=str(END))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return SELECT_BUILDING


def select_level(update, context):
    """Choose levels in the building"""
    level = update.callback_query.data
    context.user_data[CURRENT_LEVEL] = level

    text = 'Choose your level'

    buttons = [[
        InlineKeyboardButton(text='Level B1', callback_data=str(LEVELB1)),
        InlineKeyboardButton(text='Level 1', callback_data=str(LEVEL1))
    ], [
        InlineKeyboardButton(text='Level 2', callback_data=str(LEVEL2)),
        InlineKeyboardButton(text='Back', callback_data=str(END))
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return SELECTING_LEVEL


def end_second_level(update, context):
    """Return to top level conversation."""
    context.user_data[START_OVER] = True
    start(update, context)

    return END


# Third level callbacks
def select_feature(update, context):
    buttons = [[
        InlineKeyboardButton(text='Time', callback_data=str(TIME)),
        InlineKeyboardButton(text='Done', callback_data=str(END)),
    ]]
    keyboard = InlineKeyboardMarkup(buttons)

    # If we collect features for a new person, clear the cache and save the gender
    if not context.user_data.get(START_OVER):
        context.user_data[FEATURES] = {TIME: update.callback_query.data}
        text = 'Please click time to input data '

        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    # But after we do that, we need to send a new message
    else:
        text = 'Got it! Please enter time in HH:MM format to edit.'
        update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START_OVER] = False
    return SELECTING_FEATURE


def ask_for_input(update, context):
    """Prompt user to input data for selected feature."""
    context.user_data[CURRENT_FEATURE] = update.callback_query.data
    text = 'Please enter time in HH:MM format to edit.'

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text)

    return TYPING


def save_input(update, context):
    """Save input for feature and return to feature selection."""
    ud = context.user_data
    ud[FEATURES][ud[CURRENT_FEATURE]] = update.message.text

    ud[START_OVER] = True

    return select_feature(update, context)


def end_describing(update, context):
    """End gathering of features and return to parent conversation."""
    ud = context.user_data
    level = ud[CURRENT_LEVEL]
    if not ud.get(level):
        ud[level] = []
    ud[level].append(ud[FEATURES])

    # Print upper level menu
    if level == EVENT:
        ud[START_OVER] = True
        start(update, context)
    else:
        select_building(update, context)

    return END


def stop_nested(update, context):
    """Completely end conversation from within nested conversation."""
    update.message.reply_text('Okay, bye.')

    return STOPPING


# Error handler
def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def setCom(update, context):
    update.message.reply_text('/set <date>')


def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


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
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Set up third level ConversationHandler (collecting features)
    InputTime_Convo = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_feature,
                                           pattern='^' + str(LEVELB1) + '$|^' + str(LEVEL1) + '$')],

        states={
            SELECTING_FEATURE: [CallbackQueryHandler(ask_for_input,
                                                     pattern='^(?!' + str(END) + ').*$')],
            TYPING: [MessageHandler(Filters.text, save_input)],
        },

        fallbacks=[
            CallbackQueryHandler(end_describing, pattern='^' + str(END) + '$'),
            CallbackQueryHandler(show_data, pattern='^' + str(SHOWING) + '$'),
            CommandHandler('stop', stop_nested)
        ],

        map_to_parent={
            # After showing data return to top level menu
            SHOWING: SHOWING,
            # End conversation alltogether
            STOPPING: STOPPING,
        }
    )

    # Set up second level ConversationHandler (adding a person)
    add_member_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_building,
                                           pattern='^' + str(ROOM_SEARCHING) + '$')],

        states={
            SELECT_BUILDING: [CallbackQueryHandler(select_level,
                                                   pattern='^{0}$|^{1}$'.format(str(COMS1),
                                                                                str(COMS2)))],
            SELECTING_LEVEL: [InputTime_Convo]
        },

        fallbacks=[
            CallbackQueryHandler(show_data, pattern='^' + str(SHOWING) + '$'),
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
        add_member_conv,
        CallbackQueryHandler(show_data, pattern='^' + str(SHOWING) + '$'),
        CallbackQueryHandler(adding_self, pattern='^' + str(ADDING_SELF) + '$'),
        CallbackQueryHandler(end, pattern='^' + str(END) + '$'),
    ]
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            SHOWING: [CallbackQueryHandler(start, pattern='^' + str(END) + '$')],
            SELECTING_ACTION: selection_handlers,
            SELECT_BUILDING: selection_handlers,
            DESCRIBING_SELF: [InputTime_Convo],
            STOPPING: [CommandHandler('start', start)],
        },

        fallbacks=[
            CommandHandler('stop', stop)],
    )

    dp.add_handler(conv_handler)

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
