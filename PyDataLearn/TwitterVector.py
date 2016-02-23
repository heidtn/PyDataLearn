#Import the necessary methods from tweepy library
from tweepy import OAuthHandler
import tweepy

import time
import json

from nltk.tag import pos_tag

#Variables that contains the user credentials to access Twitter API 
access_token = "724753142-XedFlg9sid5gV3lHQY1IT43qrUpSc6EQknPNCVBU"
access_token_secret = ""
consumer_key = "GdQRiElw0Nb89whjxJ0C1Lndv"
consumer_secret = ""

def getfollowerstweets(api):
    friends = {}
    ids = []

    for page in tweepy.Cursor(api.followers_ids, screen_name="natessoscience").pages():
        ids.extend(page)
        time.sleep(60)

    screen_names = [user.screen_name for user in api.lookup_users(user_ids=ids)]

    print screen_names

    for i in xrange(len(screen_names)):
        try:
            friends[screen_names[i]] = api.user_timeline(id=ids[i])
        except Exception:
            print screen_names[i], "has protected tweets.  Not adding"
        time.sleep((15.0*60.0)/180.0) #180 user_timeline requests per 15-min block

    #we only want the text in the usernames right now
    for key in friends:
        tweets = []
        for tweet in friends[key]:
            tweets.append(tweet.text)
        friends[key] = tweets

    return friends

def parsetweets(tweets):
    allnouns = []
    collections = {}

    for key in tweets:
        print "parsing for", key
        for tweet in tweets[key]:
            nouns = [word for word, val in pos_tag(tweet.split()) if val == "NN"]
            for noun in nouns:
                if "http" in noun or "www" in noun:
                    continue
                noun.replace("!", "").replace("?","").replace(",","")
                collections.setdefault(key, {})
                collections[key].setdefault(noun, 0)
                collections[key][noun] += 1
                if noun not in allnouns:
                    allnouns.append(noun)



    return collections, allnouns

def getapi():
    #This handles Twitter authetification and the connection to Twitter Streaming API
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)

    return api

if __name__ == '__main__':
    api = getapi()

    getfollowers(api)
