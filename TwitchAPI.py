from settings import clientID, client_secret
import json
import requests
import pandas as pd

def getAccessToken():
    url = 'https://id.twitch.tv/oauth2/token?client_id={}&client_secret={}&grant_type=client_credentials'.format(clientID, client_secret)
    r = requests.post(url)
    access_token = json.loads(r.text)['access_token']
    return access_token

def getUser(user):
    access_token = getAccessToken()
    url = 'https://api.twitch.tv/helix/search/channels?query={}'.format(user)
    headers = {
        'Authorization': 'Bearer {}'.format(access_token),
        'client-id': clientID,
    }
    r = json.loads(requests.get(url, headers = headers).text)
    l = [x for x in r['data'] if x['display_name'].lower()==user.lower()]
    if len(l)==0:
        return None
    return l[0]

if __name__ == '__main__':
    print(getUser('riotgamesru'))
    
    streamers = pd.read_csv('db_streamers.csv', index_col=0, dtype={'subs': 'str'}).fillna('')
    print(streamers.values)