from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import logging
import pyodbc
import os
import time
from telegram.ext import MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
updater = Updater(token='1298615678:AAGUe-rqG2A8tQnlTPwQB6GUFZfqKIze1Kk', use_context=True)


dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

dbpath = os.path.abspath("ConfigDB.accdb")
conn = pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ='+dbpath+';')
cursor = conn.cursor()

def AskLanguage(update, context):
    userId = update.effective_chat.id
    # context.bot.send_message(chat_id=update.effective_chat.id, text="Hello, " + str(update.message.chat.first_name) + " I'm a bot")
    # Tastatur soll die Namen der Sprachentabelle zurückgeben
    keyboard = [[InlineKeyboardButton("Deutsch", callback_data="LanguageSet;GPM_Prince_DE"), 
    InlineKeyboardButton("English", callback_data="LanguageSet;GPM_Prince_EN")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Bitte wählen Sie Ihre Sprache: ', reply_markup=reply_markup)

    #cursor.execute("UPDATE Users SET LanguageSet = ? WHERE UserId = ?", , userId)

def AskDepartment(update, context):
    userId = update.effective_chat.id
    keyboard = []

    cursor.execute("SELECT DepartmentDe FROM Department")
    temp = []
    for counter, departments in enumerate(cursor.fetchall()):
        dp = departments.DepartmentDe
        temp.append(InlineKeyboardButton(dp.strip().strip(","), callback_data="Department;" + dp.strip().strip(",")))
        if counter % 2 == 1:
            keyboard.append(temp)

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Bitte wählen Sie Ihre Abteilung: ', reply_markup=reply_markup)

def check_user_existing(update):
    userId = update.effective_chat.id
    cursor.execute("SELECT UserId FROM Users")
    for userIdRow in cursor.fetchall():
        if userIdRow.UserId == userId:
            return True
    return False
    
def start(update, context):
    userId = update.effective_chat.id   
    if check_user_existing(update):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Willkommen zurück, " + str(update.message.chat.first_name))
    else:
        cursor.execute("INSERT INTO Users(UserId, LanguageSet) VALUES (?,?);", userId, "GPM_Prince_DE")
        conn.commit()
        context.bot.send_message(chat_id=update.effective_chat.id, text="Hallo, ich bin der PMBot. Bitte geben Sie zunächst Ihre Abteilung an:")
        AskDepartment(update, context)

        

def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

# def abc(update, context):
#     context.bot.send_message(chat_id=update.effective_chat.id, text="You said abc :D")
def button(update, context):
    query = update.callback_query
    query.answer()
    userId = update.effective_chat.id   

    Data = query.data.split(";")
    # for i in Data:
    #     print(i)
    #     print(type(i))

    cursor.execute("UPDATE Users SET " + str(Data[0]) + " = ? WHERE UserId = ?", Data[1], userId)
    conn.commit()
    # query.edit_message_text(text="Selected answer: {}".format(query.data))

    # cursor.execute("INSERT INTO Users(UserId, LanguageSet) VALUES (?,?);", userId, query.data)
    # conn.commit() 
    # print("committed INSERT...")

start_handler = CommandHandler('start', start)
dispatcher.add_handler(CallbackQueryHandler(button))
dispatcher.add_handler(start_handler)

echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
dispatcher.add_handler(echo_handler)

# abc_handler = CommandHandler('abc', abc)
# dispatcher.add_handler(abc_handler)
updater.start_polling()
updater.idle()