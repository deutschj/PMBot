from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import logging
import pyodbc
import os
import re
from flashtext import KeywordProcessor
import time
from telegram.ext import MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
updater = Updater(
    token='1298615678:AAGUe-rqG2A8tQnlTPwQB6GUFZfqKIze1Kk', use_context=True)


dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

dbpath = os.path.abspath("ConfigDB.accdb")
conn = pyodbc.connect(
    r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ='+dbpath+';')
cursor = conn.cursor()


def ChangeLanguage(update, context):
    userId = update.effective_chat.id
    # context.bot.send_message(chat_id=update.effective_chat.id, text="Hello, " + str(update.message.chat.first_name) + " I'm a bot")
    # Tastatur soll die Namen der Sprachentabelle zurückgeben
    keyboard = [[InlineKeyboardButton("Deutsch", callback_data="LanguageSet;GPM_Prince_DE"),
                 InlineKeyboardButton("English", callback_data="LanguageSet;GPM_Prince_EN")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        'Bitte wählen Sie Ihre Sprache: ', reply_markup=reply_markup)

    # cursor.execute("UPDATE Users SET LanguageSet = ? WHERE UserId = ?", , userId)


def AskDepartment(update, context):
    userId = update.effective_chat.id
    keyboard = []

    cursor.execute("SELECT DepartmentDe FROM Department")
    temp = []
    for counter, departments in enumerate(cursor.fetchall()):
        dp = departments.DepartmentDe
        temp.append(InlineKeyboardButton(dp.strip().strip(","),
                                         callback_data="Department;" + dp.strip().strip(",")))
        if counter % 2 == 1:
            keyboard.append(temp)

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        'Bitte wählen Sie Ihre Abteilung: ', reply_markup=reply_markup)


def check_user_existing(update):
    userId = update.effective_chat.id
    cursor.execute("SELECT UserId FROM Users")
    for userIdRow in cursor.fetchall():
        if userIdRow.UserId == userId:
            return True
    return False


def update_time(update):
    userId = update.effective_chat.id


def start(update, context):
    userId = update.effective_chat.id
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Um die Sprache zu ändern tippen Sie /language")
    if check_user_existing(update):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Willkommen zurück, " + str(update.message.chat.first_name))
    else:
        cursor.execute(
            "INSERT INTO Users(UserId, LanguageSet) VALUES (?,?);", userId, "GPM_Prince_DE")
        conn.commit()
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Hallo, ich bin der PMBot.\nBitte geben Sie zunächst Ihre Abteilung an:")
        AskDepartment(update, context)


def quiz(update, context):
    markup = ReplyKeyboardMarkup(
        keyboard=[['1', '2']], one_time_keyboard=True, resize_keyboard=True)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="/1 Test 1 \n /2 Test 2", reply_markup=markup)


def select_base(userId, stripped_text, language):

    print(language)
    if "gpm" in stripped_text:
        cursor.execute("SELECT Titel FROM " + language +
                       " WHERE Datenbasis= ?", "gpm")
        database = "gpm"
    else:
        cursor.execute("SELECT Titel FROM " + language +
                       " WHERE Datenbasis = ?;", "prince2")
        database = "prince2"
    return database


def compare(input_string, keywords):
    keyword_processor = KeywordProcessor()
    [keyword_processor.add_keyword(k) for k in keywords]
    return keyword_processor.extract_keywords(input_string)


def echo(update, context):
    userId = update.effective_chat.id
    cursor.execute("SELECT LanguageSet FROM Users WHERE UserId = ?", userId)
    language = cursor.fetchone().LanguageSet
    stripped_text = re.sub('[^A-Za-z0-9 ]+', '', update.message.text)
    # Endungen bei input beachten
    # Umlaute, Satzzeichen,
    database = select_base(userId, stripped_text, language)
    keywords = cursor.fetchall()
    keywords = [x.Titel for x in keywords]
    responses = compare(stripped_text, keywords)

    if len(responses) > 0:
        for keyword in responses:
            print(keyword)
            cursor.execute("SELECT Definition FROM " + language +
                           " WHERE Titel = ? AND Datenbasis = ?", keyword, database)
            print("success!")
            response = keyword.capitalize() + " (" + database.capitalize() + ")" + ":\n"
            response += str(cursor.fetchone().Definition)
            context.bot.send_message(
                chat_id=update.effective_chat.id, text=response)
    else:
        response = database.capitalize() + " Schlüsselwörter: \n"
        response += ";  ".join([k.capitalize() for k in keywords])
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=response)


def button(update, context):
    query = update.callback_query
    query.answer()
    userId = update.effective_chat.id

    Data = query.data.split(";")

    cursor.execute("UPDATE Users SET " +
                   str(Data[0]) + " = ? WHERE UserId = ?", Data[1], userId)
    conn.commit()
    query.edit_message_text(text="Eingabe gespeichert")


start_handler = CommandHandler('start', start)
language_handler = CommandHandler('language', ChangeLanguage)
quiz_handler = CommandHandler('quiz', quiz)
dispatcher.add_handler(CallbackQueryHandler(button))
dispatcher.add_handler(start_handler)
dispatcher.add_handler(language_handler)
dispatcher.add_handler(quiz_handler)

echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
dispatcher.add_handler(echo_handler)

updater.start_polling()
updater.idle()
