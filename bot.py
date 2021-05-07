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
    if from_user.id in users['id'].values:
        bot.send_message(message.chat.id, "You are already in our database.")
    else:
        print('New user', from_user)
        users = users.append(pd.DataFrame({
            'id': [from_user.id],
            'username': [from_user.username],
            'subs': ''
        }), ignore_index=True)
        users.to_csv('db_users.csv')
        bot.send_message(message.chat.id, "Hello, we have added you to out database. Type /sub to subscribe for streamers notifications.")
    
@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, "/sub if you want to subscribe to a streamer\n/mysubs if you want to see your subscriptions\n/unsub if you want to unsubscribe to a streamer")

@bot.message_handler(commands=['sub'])
def send_sub(message):
    bot.send_message(message.chat.id, "Type username of the streamer")
    bot.register_next_step_handler(message, process_sub)

def process_sub(message):
    global streamers
    chat_id = message.chat.id
    name = message.text.lower()
    subs = users.at[users.loc[users['id']==chat_id].index[0], 'subs']
    if subs == '':
        users.at[users.loc[users['id']==chat_id].index[0], 'subs'] = name
        if name in streamers['streamername'].values:
            streamers.at[streamers.loc[streamers['streamername']==name].index[0], 'subs'] = streamers.at[streamers.loc[streamers['streamername']==name].index[0], 'subs']+' '+str(chat_id)
        else:
            streamers = streamers.append(pd.DataFrame({
               'streamername': [name],
               'subs': [chat_id],
               'is_live': False
            }), ignore_index=True)
            streamers.to_csv('db_streamers.csv')
    else:
        if name in subs.split(' '):
            bot.send_message(message.chat.id, 'You are already subscribed to '+name)
            return
        else:
            users.at[users.loc[users['id']==chat_id].index[0], 'subs'] = subs+' '+name
            if name in streamers['streamername'].values:
                streamers.at[streamers.loc[streamers['streamername']==name].index[0], 'subs'] = streamers.at[streamers.loc[streamers['streamername']==name].index[0], 'subs']+' '+str(chat_id)
                streamers.to_csv('db_streamers.csv')
            else:
                streamers = streamers.append(pd.DataFrame({
                   'streamername': [name],
                   'subs': [chat_id],
                   'is_live': False
                }), ignore_index=True)
                streamers.to_csv('db_streamers.csv')
    users.to_csv('db_users.csv')
    bot.send_message(message.chat.id, 'We subscribed you to '+name)
    
@bot.message_handler(commands=['mysubs'])
def send_subs(message):
    text = 'Your subscribtions: '+ ", ".join(users.at[users.loc[users['id']==message.chat.id].index[0], 'subs'].split(' '))
    bot.send_message(message.chat.id, text)
    
@bot.message_handler(commands=['unsub'])
def send_unsub(message):
    bot.send_message(message.chat.id, "Type username of the streamer")
    bot.register_next_step_handler(message, process_unsub)
    
def process_unsub(message):
    global streamers
    chat_id = message.chat.id
    name = message.text.lower()
    subs = users.at[users.loc[users['id']==chat_id].index[0], 'subs']
    if name in subs.split(' '):
        users.at[users.loc[users['id']==chat_id].index[0], 'subs'] = " ".join([x for x in subs.split(' ') if x!=name])
        streamers.at[streamers.loc[streamers['streamername']==name].index[0], 'subs'] = " ".join([x for x in streamers.at[streamers.loc[streamers['streamername']==name].index[0], 'subs'].split(' ') if x!=str(chat_id)])
        bot.send_message(message.chat.id, 'You are not subscribed to '+name)
    else:
        bot.send_message(message.chat.id, 'You already are not subscribed to '+name)
    streamers.to_csv('db_streamers.csv')
    users.to_csv('db_users.csv')

def checkStreamers():
    print('Cheking streamers...')
    for row in streamers.values:
        streamer = row[0]
        if row[1]=='':
            subs = []
        else:
            subs = str(row[1]).split(' ')
        is_live = row[2]
        r = getUser(streamer)
        if r is None:
            continue
        if r['is_live']==True and is_live==False:
            streamers.at[streamers.loc[streamers['streamername']==streamer].index[0], 'is_live'] = True
            for sub in subs:
                bot.send_message(sub, '{} is streaming {} at https://www.twitch.tv/{}\n{}'.format(r['display_name'], r['game_name'], r['display_name'], r['title']))
        elif r['is_live']==False:
            streamers.at[streamers.loc[streamers['streamername']==streamer].index[0], 'is_live'] = False
        streamers.to_csv('db_streamers.csv')
    print('Done')
        

t = set_interval(checkStreamers, 300)
bot.polling()