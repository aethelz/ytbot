#!/usr/bin/env python
import configparser
import datetime
import io
import logging
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


# telegram bot initializing
dispatcher = updater.dispatcher


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
        text="This bot recieves youtube links and sends you it's m4a audio ")
    bot.send_message(chat_id=update.message.chat_id,
        text='Please, send valid youtube video adress')


def vidlink(bot, update):
    """
    Upon recieving video url feeds it to youtube-dl
    """
    ytp = subprocess.Popen(["youtube-dl", "-f", "140", update.message.text, "-q", "-o", "-"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, error = ytp.communicate()
    error = error.decode('cp437')
    if len(error) != 0:
        bot.send_message(chat_id=update.message.chat_id,
                         text=f"Command failed with {error}")
        return

    media_file = io.BytesIO(out)

    ytp = subprocess.Popen(["youtube-dl", "-e", update.message.text],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, error = ytp.communicate()
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
