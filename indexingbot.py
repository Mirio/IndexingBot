import os
import sys
import re
import logging
from datetime import datetime
from config import tgram_token, algolia_id, algolia_secret
from time import sleep
from urlparse import urlparse

# Fix lambda dep
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             "./lib"))
import telebot
from algoliasearch import algoliasearch

# Init telebot
logger = telebot.logger
bot = telebot.TeleBot(tgram_token, threaded=False)
telebot.logger.setLevel(logging.INFO)

# Init algolia
algolia = algoliasearch.Client(algolia_id, algolia_secret)

def cleantext(msg):
    ''' Clear text from malicius data '''
    return re.sub(r"[^a-z|A-Z|0-9 ]", "", msg)

def lambda_handler(event, context):
    ''' Lambda Handler (webhook via api gateway) '''
    update = telebot.types.Update.de_json(event["body"])
    bot.process_new_updates([update])
    return {
        "body": "ok",
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"}
    }

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    ''' Handler for callbacks, run the function insert on call.data '''
    getattr(sys.modules[__name__], call.data)(call)

@bot.message_handler(commands=['help', 'start'])
def start_helper(message):
    ''' Helper for first command '''
    markup = telebot.types.InlineKeyboardMarkup()
    try:
        if "it" in message.from_user.language_code:
            desc = ("Ciao %s, questo bot e' stato creato al fine di 'unificare'"
                    "tutti i vari gruppi presenti nei network in un'unica "
                    "directory (aggiornata e manutenuta) dove tutti gli "
                    "utenti possono cercare i canali liberamente.\n"
                    "Regole:\n- NO gruppi porno o simili.\n"
                    "- NO gruppi che supportano Warez e qualsiasi altro illecito."
                    "\n\nPer qualsiasi dubbi o domanda contatta @Mirioo" %
                    message.from_user.first_name)
            markup.add(telebot.types.InlineKeyboardButton(
                "Richiedi l'aggiunta del tuo gruppo",
                callback_data="add_helper"))
            markup.add(telebot.types.InlineKeyboardButton(
                "Guarda la lista dei gruppi", callback_data="showlist"))
            markup.add(telebot.types.InlineKeyboardButton(
                "Ricerca gruppo", callback_data="search"))
        else:
            raise TypeError
    except TypeError:
        desc = ("Ciao %s, this bot was created with the purpose to index "
                "all network groups in one single directory (maintained "
                "and updated) where users can freely search.\nRules:\n"
                "- No porno group or something like that.\n"
                "- No Warez group or any illecit group.\n"
                "If you have doubt please contact @Mirioo" %
                message.from_user.first_name)
        markup.add(telebot.types.InlineKeyboardButton(
            "Submit your group.", callback_data="add_helper"))
        markup.add(telebot.types.InlineKeyboardButton(
            "Show the group listed", callback_data="showlist"))
        markup.add(telebot.types.InlineKeyboardButton(
            "Search Group", callback_data="search"))
    bot.send_message(message.from_user.id, (desc), reply_markup=markup)

@bot.message_handler(commands=['showlist'])
def showlist(message):
    ''' Show the group listed via algolia '''
    algolia_index = algolia.init_index("groups")
    msgout = ""
    res = algolia_index.search(
        "", {"filters": 'enabled = 1', "hitsPerPage": 500})
    for group in res["hits"]:
        msgout += "--\nName: %s\nDescription: %s\nLink: %s\n" % (
            group["name"], group["desc"], group["url"])

    # Fix split large message
    splitted_text = telebot.util.split_string(msgout, 3000)
    for text in splitted_text:
        bot.send_message(message.from_user.id, (text),
                         disable_web_page_preview=True)

@bot.message_handler(commands=['waitlist'])
def waitlist(message):
    ''' Show the group in wait list via algolia '''
    algolia_index = algolia.init_index("groups")
    msgout = ""
    res = algolia_index.search(
        "", {"filters": 'enabled = 0', "hitsPerPage": 500})
    for group in res["hits"]:
        msgout += "--\nName: %s\nDescription: %s\nLink: %s\n" % (
            group["name"], group["desc"], group["url"])

    # Fix split large message
    splitted_text = telebot.util.split_string(msgout, 3000)
    for text in splitted_text:
        bot.send_message(message.from_user.id, (text),
                         disable_web_page_preview=True)

@bot.message_handler(commands=['search'])
def search(message):
    ''' Show the group listed via algolia '''
    try:
        msg_split = message.text.split("search ")
        if len(msg_split) <= 2:
            algolia_index = algolia.init_index("groups")
            msgout = ""
            res = algolia_index.search(
                cleantext(msg_split[1]),
                {"filters": 'enabled = 1', "hitsPerPage": 500})
            for group in res["hits"]:
                try:
                    if "it" in message.from_user.language_code:
                        msgout += "--\nNome: %s\nDescrizione: %s\nLink: %s\n" % (
                            group["name"], group["desc"], group["url"])
                    else:
                        raise TypeError
                except TypeError:
                    msgout += "--\nName: %s\nDescription: %s\nLink: %s\n" % (
                        group["name"], group["desc"], group["url"])
            if not msgout:
                msgout = "No group found."
            # Fix split large message
            splitted_text = telebot.util.split_string(msgout, 3000)
            for text in splitted_text:
                bot.send_message(message.from_user.id, (text),
                                 disable_web_page_preview=True)
            return
        else:
            raise KeyError
    except (KeyError, IndexError, AttributeError):
        try:
            if "it" in message.from_user.language_code:
                msgout = "Usa: /search <nome da cercare>"
            else:
                raise TypeError
        except TypeError:
            msgout = "Use: /search <name to search>"
        bot.send_message(message.from_user.id, (msgout))

@bot.message_handler(commands=['add'])
def add_helper(message):
    ''' Submit group to list '''
    try:
        algolia_index = algolia.init_index("groups")
        msg_split = message.text.split("add ")[1].split("|")
        if len(msg_split) == 3:
            url = urlparse(msg_split[0]).geturl()
            name = cleantext(msg_split[1])
            desc = cleantext(msg_split[2])

            # Check if url is correclty formatted
            if not url.startswith("https://t.me/"):
                try:
                    if "it" in message.from_user.language_code:
                        bot.send_message(message.from_user.id,
                                         ("Utilizza un url t.me valido."
                                          " (usa https:// prima)"))
                        return
                    else:
                        raise TypeError
                except TypeError:
                    bot.send_message(message.from_user.id,
                                     ("Use the t.me format for URL."
                                      " (use schema https)"))
                    return

            # Check if url is already present
            res = algolia_index.search(url)
            for group in res["hits"]:
                if group["url"] == url:
                    try:
                        if "it" in message.from_user.language_code:
                            bot.send_message(message.from_user.id,
                                             ("Gruppo gia' presente."))
                            return
                        else:
                            raise TypeError
                    except TypeError:
                        bot.send_message(message.from_user.id,
                                         ("Group already present."))
                        return


            # Check if name is already taken
            res = algolia_index.search(name)
            for group in res["hits"]:
                if group["name"] == name:
                    try:
                        if "it" in message.from_user.language_code:
                            bot.send_message(message.from_user.id,
                                             ("Nome gia' presente."))
                            return
                        else:
                            raise TypeError
                    except TypeError:
                        bot.send_message(message.from_user.id,
                                         ("Name already taken."))
                        return

            # Adding new items
            timenow = datetime.now().isoformat()
            algolia_index.add_object({
                "name": name,
                "desc": desc,
                "url": url,
                "owner_id": message.from_user.id,
                "owner_username": message.from_user.username,
                "submit_date": timenow,
                "update_date": timenow,
                "category": "Main",
                "enabled": False
            })
            try:
                if "it" in message.from_user.language_code:
                    msgout = "%s correttamente aggiunto." % name
                else:
                    raise TypeError
            except TypeError:
                msgout = "%s added." % name
        else:
            raise KeyError
    except (KeyError, IndexError, AttributeError):
        try:
            if "it" in message.from_user.language_code:
                msgout = ("Usa: /add <url>|<Nome del gruppo>|"
                          "<descrizione(max 100)>")
            else:
                raise TypeError
        except TypeError:
            msgout = "Use: /add <url>|<Groupname>|<description (max 100)>"
    bot.send_message(message.from_user.id, (msgout))
