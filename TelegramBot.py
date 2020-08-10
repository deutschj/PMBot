from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import logging
import pyodbc
import os
import telegram
import random
from datetime import datetime, date
import re
import time
import _thread
from flashtext import KeywordProcessor
from telegram.ext import MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
updater = Updater(
    token='1298615678:AAGUe-rqG2A8tQnlTPwQB6GUFZfqKIze1Kk', use_context=True)
bot = telegram.Bot(token='1298615678:AAGUe-rqG2A8tQnlTPwQB6GUFZfqKIze1Kk')

dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

dbpath = os.path.abspath("ConfigDB.accdb")
conn = pyodbc.connect(
    r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ='+dbpath+';')
cursor = conn.cursor()


def ChangeLanguage(update, context):
    global bot
    bot = context.bot
    userId = update.effective_chat.id
    # Tastatur soll die Namen der Sprachentabelle zurückgeben
    keyboard = [[InlineKeyboardButton("Deutsch", callback_data="LanguageSet;GPM_Prince_DE"),
                 InlineKeyboardButton("English", callback_data="LanguageSet;GPM_Prince_EN")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "Bitte wählen Sie Ihre Sprache / Please select your language: ", reply_markup=reply_markup)

def get_user_language(userId):
    cursor.execute("SELECT LanguageSet FROM Users WHERE UserId = ?", userId)
    return cursor.fetchone().LanguageSet.strip().strip(",")
    
def check_user_offline():
    while True:
        
        now = datetime.timestamp(datetime.now())
        cursor.execute("SELECT * FROM Users")
        last_messages = [(x.UserId, x.LastMessageSent)
                         for x in cursor.fetchall()]

        for last_message in last_messages:
            time_dif = now - last_message[1]
            if time_dif >= 1296000:  # time in seconds (15 days = 1296000 sec)
                if "GPM_Prince_DE" in get_user_language(last_message[0]):
                    response ="Es sind mindestens 15 Tage seit der letzten Interaktion vergangen.\nMit /quiz kann ein kurzes Quiz gestartet werden."
                else:
                    response = "It has been 15 days since your last interaction.\nYou can start a short quiz with /quiz." 
                bot.send_message(chat_id=last_message[0], text = response)
        time.sleep(86400)


if __name__ == "__main__":
    _thread.start_new_thread(check_user_offline) # separate thread for counting the time since last Bot usage


def AskDepartment(update, context):
    userId = update.effective_chat.id
    keyboard = []
    language = get_user_language(userId)
    if "GPM_Prince_DE" in language:
        cursor.execute("SELECT DepartmentDe FROM Department")
        dp = [departments.DepartmentDe for departments in cursor.fetchall()]
    else:
        cursor.execute("SELECT DepartmentEn FROM Department")
        dp = [departments.DepartmentEn for departments in cursor.fetchall()]
    temp = []
    for counter, departments in enumerate(dp):
        temp.append(InlineKeyboardButton(departments.strip().strip(","),
                                         callback_data="Department;" + departments.strip().strip(",")))
        if counter % 2 == 1:
            keyboard.append(temp)

    reply_markup = InlineKeyboardMarkup(keyboard)
    if "GPM_Prince_DE" in language:
        response = "Bitte wählen Sie Ihre Abteilung: "
    else:
        response = "Please select your department: "
    update.message.reply_text(
        response, reply_markup=reply_markup)


def check_user_existing(update):
    userId = update.effective_chat.id
    cursor.execute("SELECT UserId FROM Users")
    for userIdRow in cursor.fetchall():
        if userIdRow.UserId == userId:
            return True
    return False


def update_time(update):
    userId = update.effective_chat.id
    time = update.message.date
    timestamp = int(datetime.timestamp(time))
    cursor.execute(
        "UPDATE Users SET LastMessageSent = ? WHERE UserId = ?", timestamp, userId)
    conn.commit()


def start(update, context):
    bot = context.bot
    userId = update.effective_chat.id    
    if check_user_existing(update):
        language = get_user_language(userId)
        if "GPM_Prince_DE" in language:
            response = "Willkommen zurück, "
        else:
            response = "Welcome back, "
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text= response + str(update.message.chat.first_name))
    else:       
        cursor.execute(
            "INSERT INTO Users(UserId, LanguageSet) VALUES (?,?);", userId, "GPM_Prince_DE")
        conn.commit()
        language = get_user_language(userId)
        ChangeLanguage(update, context)
        AskDepartment(update, context)
        if "GPM_Prince_DE" in language:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                text="Um die Sprache zu ändern tippen Sie /language.\nUm die Abteilung zu wechseln tippen Sie /department")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                text="To change your language, please type /language.\nTo change your department, please type /department.\nTo get an overview over all commands type /help")
        
        if "GPM_Prince_DE" in language:
            response = "Hallo, ich bin der PMBot.\nBitte geben Sie zunächst Ihre Abteilung an:"
        else:
            response = "Hello, I am the PMBot.\nPlease select your department first:"
        context.bot.send_message(chat_id=update.effective_chat.id, text= response)
        
        conn.commit()

def quiz(update, context):
    userId = update.effective_chat.id
    language = get_user_language(userId)
    cursor.execute("SELECT Titel FROM " + language)
    temp = []
    keyboard = []
    if "DE" in language:
        dp = [x.Titel.capitalize() for x in cursor.fetchall()]
    else:
        dp = [x.Titel for x in cursor.fetchall()]

    random.shuffle(dp)
    dp = set(dp)
    dp = list(dp)
    dp = dp[:5]
    right_answer = random.randrange(0, 4)
    cursor.execute("SELECT Definition FROM " + language +
                   " WHERE Titel = ?", dp[right_answer])
    question = cursor.fetchone().Definition
    question = question.replace(dp[right_answer], "****")
    cursor.execute("SELECT Datenbasis FROM " + language +
                   " WHERE Titel = ?", dp[right_answer])
    database = cursor.fetchone().Datenbasis
    for i in range(0, 4):
        if i == right_answer:
            temp.append(InlineKeyboardButton(dp[i].strip().strip(","),
                                             callback_data="right_answer;" + dp[right_answer].strip().strip(",")))
        else:
            temp.append(InlineKeyboardButton(dp[i].strip().strip(","),
                                             callback_data="wrong_answer;" + dp[right_answer].strip().strip(",")))

        if i % 2 == 1:
            keyboard.append(temp)
            temp = []

    reply_markup = InlineKeyboardMarkup(keyboard)
    if "GPM_Prince_DE" in language:
            response = "Welches Keyword passt zur Definition der Datenbasis "
    else:
        response = "Which keyword matches the definition from the database "
    question = response + database.upper() + "?\n\n" + question
    update.message.reply_text(
        question, reply_markup=reply_markup)


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
    update_time(update)
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
        #Nach 3 mal weiterleiten
        response = database.capitalize() + " Schlüsselwörter / keywords: \n"
        response += ";  ".join([k.capitalize() for k in keywords])
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=response)


def button(update, context):
    query = update.callback_query
    query.answer()
    userId = update.effective_chat.id
    language = get_user_language(userId)
    Data = query.data.split(";")

    if "answer" in Data[0]:
        if Data[0] == "right_answer":
            query.edit_message_reply_markup(inline_message_id=query.inline_message_id, reply_markup=None)
            if "GPM_Prince_DE" in language:
                response = "Richtige Antwort!"
            else:
                response = "That's correct!"
            context.bot.send_message(chat_id=update.effective_chat.id, text= response)
        else:
            query.edit_message_reply_markup(inline_message_id=query.inline_message_id, reply_markup=None)
            if "GPM_Prince_DE" in language:
                response = "Falsche Antwort. Richtig wäre " + Data[1] + " gewesen."
            else:
                response = "Wrong answer. " + Data[1] + "would have been correct."
            context.bot.send_message(chat_id=update.effective_chat.id, text= response)
    else:
        cursor.execute("UPDATE Users SET " +
                       str(Data[0]) + " = ? WHERE UserId = ?", Data[1], userId)
        conn.commit()
        query.edit_message_text(text="✅")


start_handler = CommandHandler('start', start)
language_handler = CommandHandler('language', ChangeLanguage) 
department_handler = CommandHandler('department', AskDepartment)
quiz_handler = CommandHandler('quiz', quiz)
dispatcher.add_handler(CallbackQueryHandler(button))
dispatcher.add_handler(start_handler)
dispatcher.add_handler(language_handler)
dispatcher.add_handler(quiz_handler)
dispatcher.add_handler(department_handler)

echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
dispatcher.add_handler(echo_handler)

updater.start_polling()
updater.idle()
