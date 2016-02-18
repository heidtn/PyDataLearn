#Import the necessary methods from tweepy library
from tweepy import OAuthHandler
import tweepy

import time
import json

#Variables that contains the user credentials to access Twitter API 
access_token = ""
access_token_secret = ""
consumer_key = ""
consumer_secret = ""

def getfollowers(api):
    friends = {}

    me = api.me()
    c = tweepy.Cursor(api.friends)

    for ret in c.pages():
        for friend in ret:
            friends[friend.screen_name] = friend.timeline
        time.sleep(1)

    print friends

if __name__ == '__main__':
    #This handles Twitter authetification and the connection to Twitter Streaming API
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)

    getfollowers(api)
