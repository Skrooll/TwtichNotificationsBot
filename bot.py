from settings import token
import telebot
import requests
import pandas as pd
from telebot import types
import threading
from TwitchAPI import getUser
import atexit

def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t

bot = telebot.TeleBot(token, parse_mode=None)

users = pd.read_csv('db_users.csv', index_col=0, dtype={'subs': 'str', 'id': 'int'}).fillna('')
streamers = pd.read_csv('db_streamers.csv', index_col=0, dtype={'subs': 'str'}).fillna('')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    global users
    from_user = message.from_user
    if False:#from_user.id in users['id'].values:
        bot.reply_to(message, "You are already in our database.")
    else:
        users = users.append(pd.DataFrame({
            'id': [from_user.id],
            'username': [from_user.username],
            'subs': ''
        }), ignore_index=True)
        users.to_csv('db_users.csv')
        bot.reply_to(message, "Hello, we have added you to out database. Type /sub to subscribe for streamers notifications.")
    
@bot.message_handler(commands=['sub'])
def send_welcome(message):
    bot.reply_to(message, "What streamer you want to subscribe to?")
    bot.register_next_step_handler(message, process_sub)

def process_sub(message):
    global streamers
    chat_id = message.chat.id
    name = message.text
    subs = users.at[users.loc[users['id']==chat_id].index[0], 'subs']
    
    if subs == '':
        users.at[users.loc[users['id']==chat_id].index[0], 'subs'] = name
        if name in streamers['streamername'].values:
            streamers.at[streamers.loc[streamers['streamername']==name].index[0], 'subs'] = streamers.at[streamers.loc[streamers['streamername']==name].index[0], 'subs']+' '+chat_id
        else:
            streamers = streamers.append(pd.DataFrame({
               'streamername': [name],
               'subs': [chat_id],
               'is_live': False
            }), ignore_index=True)
            streamers.to_csv('db_streamers.csv')
    else:
        if name in subs.split(' '):
            bot.reply_to(message, 'You are already subscribed to '+name)
            return
        else:
            users.at[users.loc[users['id']==chat_id].index[0], 'subs'] = subs+' '+name
            if name in streamers['streamername'].values:
                streamers.at[streamers.loc[streamers['streamername']==name].index[0], 'subs'] = streamers.at[streamers.loc[streamers['streamername']==name].index[0], 'subs']+' '+chat_id
            else:
                streamers = streamers.append(pd.DataFrame({
                   'streamername': [name],
                   'subs': [chat_id],
                   'is_live': False
                }), ignore_index=True)
                streamers.to_csv('db_streamers.csv')
    users.to_csv('db_users.csv')
    
    bot.reply_to(message, 'We subscribed you to '+name)
    
def checkStreamers():
    for row in streamers.values:
        streamer = row[0]
        if row[1]=='':
            subs = []
        else:
            subs = str(row[1]).split(' ')
        is_live = row[2]
        print(streamer, subs, is_live)
        r = getUser(streamer)
        if r['is_live']==True and is_live==False:
            streamers.at[streamers.loc[streamers['streamername']==streamer].index[0], 'is_live'] = True
            for sub in subs:
                bot.send_message(sub, '{} is streaming {} at https://www.twitch.tv/{}\n{}'.format(r['display_name'], r['game_name'], r['display_name'], r['title']))
        else:
            streamers.at[streamers.loc[streamers['streamername']==streamer].index[0], 'is_live'] = False
        streamers.to_csv('db_streamers.csv')
        

t = set_interval(checkStreamers, 300)
bot.polling()