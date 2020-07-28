from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import logging
import pyodbc
from telegram.ext import MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
updater = Updater(token='1298615678:AAGUe-rqG2A8tQnlTPwQB6GUFZfqKIze1Kk', use_context=True)


dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

conn = pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=F:\Schule\Semester 2\Anwendungsprojekt\Code\TestDatabase.accdb;')
cursor = conn.cursor()
cursor.execute('select * from Tabelle1')
   
for row in cursor.fetchall():
    print (row)

def start(update, context):
    global first_name
    first_name = update.message.chat.first_name
    context.bot.send_message(chat_id=update.effective_chat.id, text="hello, " + str(first_name) + " I'm a bot")

    keyboard = [[InlineKeyboardButton("Deutsch", callback_data='1'), InlineKeyboardButton("English", callback_data='2')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose: ', reply_markup=reply_markup)

def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

# def abc(update, context):
#     context.bot.send_message(chat_id=update.effective_chat.id, text="You said abc :D")
def button(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(text="Selected option: {}".format(query.data))
    cursor.execute("INSERT INTO Tabelle1(user, lang) VALUES ('" + first_name + "', '" + query.data + "');")
    conn.commit()
    print("committed...")

start_handler = CommandHandler('start', start)
dispatcher.add_handler(CallbackQueryHandler(button))
dispatcher.add_handler(start_handler)

echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
dispatcher.add_handler(echo_handler)

# abc_handler = CommandHandler('abc', abc)
# dispatcher.add_handler(abc_handler)
updater.start_polling()
updater.idle()