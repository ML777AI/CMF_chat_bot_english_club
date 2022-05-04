import time
from pathlib import Path
import telebot
import lib
import logging
import requests
from urllib.parse import quote_plus

token = Path('config', 'token.txt').read_text().rstrip()  # token reading
bot = telebot.TeleBot(token)  # bot creating

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s.%(msecs)03d %(name)-8s %(levelname)-2s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='events.log',
                    )
logger_main_py = logging.getLogger('main.py')  # define a logger for main.py


@bot.message_handler(commands=['start'])
def start(message):
    lib.start(bot, message)


@bot.message_handler(commands=['help'])
def help(message):
    lib.help(bot, message)


@bot.message_handler(commands=['info'])
def info(message):
    lib.info(bot, message)


@bot.message_handler(commands=['feedback'])
def feedback(message):
    lib.feedback(bot, message)


@bot.message_handler(commands=['parse'])
def parse(message):
    #lib.parse(bot, message)
    response = message

    bot.send_message(message.chat.id, response.chat, parse_mode='html')


@bot.message_handler(content_types=['text'])
def handle_text(message):
    lib.handle_text(bot, message)


def main():
    logger_main_py.info('Program started')
    # bot.polling(none_stop=True, interval=0)  # bot startup
    bot.polling(none_stop=True)  # bot startup
    logger_main_py.info('Program finished')


if __name__ == '__main__':
    main()
