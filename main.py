#!/usr/bin/env python
import configparser
import datetime
import io
import logging
import re
import subprocess


from telegram import MessageEntity
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          CallbackQueryHandler )

# logging initialize
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# config initializing
config = configparser.ConfigParser()
print("Reading config...")
config.read('config.ini')
try:
    updater = Updater(token=config['DEFAULT']['token'])
    print("Configuration initialized!")
except KeyError:
    print("Make sure you copied sample config.ini and replaced TOKEN in it")
    print("Exiting...")
    exit()


class BadURL(Exception):
    pass


# telegram bot initializing
dispatcher = updater.dispatcher


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
        text="This bot receives youtube links and sends you it's m4a audio ")
    bot.send_message(chat_id=update.message.chat_id,
        text='Please, send valid youtube video address')


def url_verify(text: str) -> str:
    """
    Checks if url is a youtube one, extracts video ID and returns it, otherwise raises exception
    """
    yt_pattern = re.compile(r'''
    (?:http(?:s)?://)?(?:www\.)                                # non-capturing prefix match
    ?(?:youtu\.be/|youtube\.com/                               # non-capturing domain match
    (?:(?:watch)?\?(?:.*&)?v(?:i)?=|(?:embed|v|vi|user)/))     # non-capturing pre-vid ID syntax
    ([^?&\"'<> #]+)                                            # captures video ID
    ''', re.VERBOSE)

    try:
        parsed_url = yt_pattern.search(text).groups()
        return parsed_url[0]
    except:
        raise BadURL


def vidlink(bot, update):
    """
    Upon receiving video url verifies it and feeds it to youtube-dl
    """
    url = update.message.text
    try:
        vidcode = url_verify(url)
    except BadURL:
        bot.send_message(chat_id=update.message.chat_id,
                         text='Not a valid youtube link, sorry!')
        return

    ytp = subprocess.Popen(["youtube-dl", "-f", "140", 'https://youtu.be/' + vidcode , "-q", "-o", "-"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, errorc = ytp.communicate()
    errorc = errorc.decode('cp437')
    if len(errorc) != 0:
        bot.send_message(chat_id=update.message.chat_id,
                         text=f"Command failed with {errorc}")
        return

    media_file = io.BytesIO(out)

    ytp = subprocess.Popen(["youtube-dl", "-e", update.message.text],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, errorc = ytp.communicate()
    out = out.decode('utf-8').replace(" ", "_")

    bot.send_document(chat_id=update.message.chat_id,
                      filename=f"{out}.m4a",
                      document=media_file)

def unknown(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Unknown command.")


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


# ------------------------ MAIN LOOP -------------------------------


def main():
    print("Adding handlers...")
    start_handler = CommandHandler('start', start)
    link_handler = MessageHandler(
            Filters.text & (Filters.entity(MessageEntity.URL) |
                           Filters.entity(MessageEntity.TEXT_LINK)),
            vidlink)
    unknown_handler = MessageHandler(Filters.command, unknown)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(link_handler)
    dispatcher.add_error_handler(error)
    # Unknown handler should go last!
    dispatcher.add_handler(unknown_handler)

    print("Bot is ready!")
    updater.start_polling()


if __name__ == '__main__':
    main()
