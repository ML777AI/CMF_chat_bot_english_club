import logging
import random
import time
import threading
from itertools import zip_longest
from pathlib import Path
from telbot_constants import admin_chat_id, admin_username, admin_link, hyper_troll_text, author1, author2, hyper_text_slack

import yaml
from telebot import types

logger_lib_py = logging.getLogger('lib.py')  # define a logger for lib.py

file_lock = threading.Lock()
user_independence_lock = threading.Lock()

# TODO
# ----1) сделать отдельный файл с объявлениями ф-ий (
# 2) PyTest (или ст питоновский юнит тест import unittest (test.py)...
# 3) ПРОБЛЕМА прога зависит от того, когда я её запустил - нужен график выполнения функции round_create...
# ----4) JSON либо yaml - под хранение БД
# ----5) сделать write_active_participants()
# ----6) что если один чел в конце останется? - будет тройка (один + предыдущая пара)
# 7) если YAML пустой на моменте вызова ф-ии read(), то всё падает...
# ----8) file threads safety! Mutex?
# ----9) в main() процесс не идёт дальше bot.poling - а оно и не нужно)
# ----10) create random_pairing()
# 11) В round_create отказаться от использования Usernames -> Перейти на парсинг только [Chat_Id, first_name, last_name]
# ----12) Hide sensitive data
# ----13) Сделать систему логирования
# 14) Сделать подсчёт уникальных юзеров для последующей статистики


def read_users():
    """
    read users from db/users.yaml
    """
    with file_lock:
        with open('db/users.yaml') as f:
            users = yaml.safe_load(f)
    logger_lib_py.info(f'Reading users: {type(users)} {users}')
    return users


def add_user(user: dict):
    """
    read users from db/users.yaml,
    add new_user in buffer dic,
    rewrite the BD.
    """
    with user_independence_lock:
        users = read_users()
        logger_lib_py.info(f'Adding user: {user}')
        users.update(user)
        logger_lib_py.info(f'New list is: {users = }')
        write_users(users)


def remove_user(user):
    """
    reads current BD,
    deleting delUser from buffer dict,
    rewriting the BD.
    """
    with user_independence_lock:
        users = read_users()
        logger_lib_py.info(f'Removing user: {user}')
        del users[user]
        logger_lib_py.info(f'New list is: {users = }')
        write_users(users)


def write_users(users):
    """
    write to db/users.yaml
    """
    with file_lock:
        with Path('db', 'users.yaml').open('w') as f:
            yaml.safe_dump(users, f)
    logger_lib_py.info(f'Rewriting the users list: {users}')


def handle_text(bot, message):
    """
    User's message processing:
    'GO' - puts the user's ID and user's chat ID into the DB (users.yaml)
    'STOP' - take it away from the DB
    """
    if message.text.strip() == 'GO':
        logger_lib_py.info(f'@{message.from_user.username} sent GO')
        users = read_users()
        if message.from_user.username not in users:
            new_user = {message.from_user.username: message.chat.id}
            add_user(new_user)
            logger_lib_py.info(f'@{message.from_user.username} added!')
            bot.send_message(
                message.chat.id,
                f'Congrats, {message.from_user.first_name} {message.from_user.last_name}!\n'
                'You have been registered for the nearest round!\n'
                'Please, wait while Bot will find a partner for you)'
            )
            logger_lib_py.info(f'@{message.from_user.username} received an adding confirmation!')
        elif message.from_user.username in users:
            logger_lib_py.info(f'@{message.from_user.username} is already registered!')
            bot.send_message(
                message.chat.id,
                f'Hey, {message.from_user.first_name}!\n'
                'You are already registered!\n'
                'Be patient) The Bot will message you soon!'
            )
            logger_lib_py.info(f'@{message.from_user.username} received an adding rejection!')
    elif message.text.strip() == 'STOP':
        logger_lib_py.info(f'@{message.from_user.username} sent STOP')
        users = read_users()
        if message.from_user.username in users:
            del_user = message.from_user.username
            remove_user(del_user)
            logger_lib_py.info(f'@{message.from_user.username} deleted!')
            bot.send_message(
                message.chat.id,
                f'Ok, {message.from_user.first_name}! The Bot will not interrupt you anymore.\n'
                'If you want back, just press /start here again\n\n'
                'See you!'
            )
            logger_lib_py.info(f'@{message.from_user.username} received a deleting confirmation!')
        elif message.from_user.username not in users:
            logger_lib_py.info(f'@{message.from_user.username} is not in a list yet!')
            bot.send_message(
                message.chat.id,
                f'Hey, {message.from_user.first_name}!\n'
                'You are not registered yet!\n'
                'You should type GO first!'
            )
            logger_lib_py.info(f'@{message.from_user.username} received a deleting rejection!')
    elif message.text.strip() == 'control':
        logger_lib_py.info(f'@{message.from_user.username} sent control!')
        if message.from_user.username == admin_username:
            logger_lib_py.info('access granted!')
            round_create(bot, message)
            logger_lib_py.info('invites sent!')
        else:
            bot.send_message(message.chat.id, 'access denied')
            logger_lib_py.info(f'access denied for @{message.from_user.username}')
    else:
        bot.send_message(message.chat.id, 'Sorry?')
        logger_lib_py.info(f'@{message.from_user.username} sent trash (sorry?)')


def start(bot, message):
    """
    START command processing
    Sends the message (describing the Bot's functionality) to the User
    """
    logger_lib_py.info(f'@{message.from_user.username} sent /start')
    if message.from_user.last_name is None:
        message.from_user.last_name = ' '
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)  # 2 buttons creating
    item1 = types.KeyboardButton('GO')
    item2 = types.KeyboardButton('STOP')
    markup.add(item1)
    markup.add(item2)
    if message.chat.id == admin_chat_id:
        item3 = types.KeyboardButton('control')
        markup.add(item3)
    bot.send_message(message.chat.id,
                     f'Hi there, {message.from_user.first_name} {message.from_user.last_name}\!\n\n'
                     'Press:\n'
                     'GO \- to start working in the nearest round \(the Bot will remind you every 3 days\)\n'
                     'STOP \- to stop working \(the bot will not interrupt you anymore\)\n'
                     'Notice this Bot is running on free server\.\n'
                     'It means it can be interrupted at any moment\.\n'
                     f'In a case, please feel free to contact the {admin_link}',
                     parse_mode='MarkdownV2',
                     disable_web_page_preview=True,
                     reply_markup=markup
                     )


def help(bot, message):
    """
    HELP command processing
    Sends the message (trolling) to the User
    """
    logger_lib_py.info(f'@{message.from_user.username} sent /help')
    bot.send_message(message.chat.id,
                     "You can visit our {} It has all useful information about Bot's Installation, "
                     "Configuration, Partnerships and other\.".format(hyper_troll_text),
                     parse_mode='MarkdownV2',
                     disable_web_page_preview=True)
    time.sleep(10)
    bot.send_message(message.chat.id, 'Never gonna give you up!')
    time.sleep(2)
    bot.send_message(message.chat.id, 'Never gonna let you down!')
    time.sleep(2)
    bot.send_message(message.chat.id, 'Never gonna run arooooooouuuund and desert you!😆))')
    logger_lib_py.info(f'@{message.from_user.username} has been trolled successfully!')


def info(bot, message):
    """
    INFO command processing
    Sends the message (authors info) to the User
    """
    logger_lib_py.info(f'@{message.from_user.username} sent /info')
    bot.send_message(message.chat.id, f'Bot made by {author1} and {author2}',
                     parse_mode='MarkdownV2',
                     )


# disable_web_page_preview = True,


def feedback(bot, message):
    """
    INFO command processing
    Sends the message (link to Slack English Club Channel) to the User
    """
    logger_lib_py.info(f'@{message.from_user.username} sent /feedback')
    bot.send_message(message.chat.id,
                     "You can write your feedback at {}".format(hyper_text_slack),
                     parse_mode='MarkdownV2',
                     disable_web_page_preview=True)


def parse(bot, message):
    bot.send_message(message.chat.id,
                     message,
                     parse_mode='html',
                     disable_web_page_preview=True)


def round_create(bot, m):
    """
    Create round when admin say to
    Send messages to each person in a pair at the round's beginning
    """
    logger_lib_py.info('round_create start')
    users = read_users()
    user_list = list(users.keys())
    random.shuffle(user_list)
    user_shuffle_dict = {user: users[user] for user in user_list}
    users = user_shuffle_dict
    logger_lib_py.info(f'shuffled {users = }')
    it = iter(users)
    pairs = list(zip_longest(it, it))
    logger_lib_py.info(f'{pairs = }')
    if pairs[-1][-1] is None:
        pairs[-2] += (pairs[-1][0],)
        pairs.pop()
    logger_lib_py.info('for pair in pairs:')
    index = 0
    for pair in pairs:
        logger_lib_py.info(f'pair {index}: {pair}')
        index += 1
    for pair in pairs:
        for user in pair:
            partners = set(pair) - {user}
            bros = [
                f'[{bro}](tg://user?id={users[bro]})'
                for bro in partners
            ]
            # try:
            #     bot.send_message(users[user],
            #                  f'Hi, {user}\! {" and ".join(bros)} is\(are\) waiting for you to speak\!\n'
            #                  'Please\, contact your chat partner and plan your call within the next 3 days\.\n'
            #                  'Have a nice meet\!',
            #                  parse_mode='MarkdownV2',
            #                  disable_web_page_preview=True)
            # except:
            #      2022-04-05 17:49:09,424 (__init__.py:688 MainThread) ERROR - TeleBot: "A request to the Telegram API was unsuccessful. Error code: 403. Description: Forbidden: bot was blocked by the user"

            bot.send_message(users[user],
                             f'Hi, {user}\! {" and ".join(bros)} is\(are\) waiting for you to speak\!\n'
                             'Please\, contact your chat partner and plan your call within the next 3 days\.\n'
                             'Have a nice meet\!',
                             parse_mode='MarkdownV2',
                             disable_web_page_preview=True)

    logger_lib_py.info('round_create finish')
