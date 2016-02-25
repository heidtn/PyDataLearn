#Import the necessary methods from tweepy library
from tweepy import OAuthHandler
import tweepy

import time
import json

import os

import nltk
from nltk.tag.perceptron import PerceptronTagger
tagger = PerceptronTagger()

#Variables that contains the user credentials to access Twitter API 
#I've defined these as environment variables so dirty github bots can't steal my sweet sweet twitter credentials
access_token = os.environ["ACCESS_TOKEN"]
access_token_secret = os.environ["ACCESS_TOKEN_SECRET"]
consumer_key = os.environ["CONSUMER_KEY"]
consumer_secret = os.environ["CONSUMER_KEY_SECRET"]

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
            tokens = nltk.word_tokenize(tweet)
            tagset = None
            nouns = [word for word, val in nltk.tag._pos_tag(tokens, tagset, tagger) if val in ["NN", "NNP"]]
            for noun in nouns:
                if "http" in noun or "www" in noun or noun == "RT" or noun == "@" or "t.co" in noun:
                    continue
                noun = noun.replace("!", "").replace("?","").replace(",","")
                noun = noun.lower()
                collections.setdefault(key, {})
                collections[key].setdefault(noun, 0)
                collections[key][noun] += 1
                if noun not in allnouns:
                    allnouns.append(noun)

    return collections, allnouns

def saveresults(collections, words, filename="twittervecs.csv"):
    f = open(filename, 'w')
    words.sort()
    f.write("users\t")
    for word in words:
        f.write(repr(word))
        f.write('\t')
    f.write('\n')
    for user, collection in collections.iteritems():
        f.write(user)
        for word in words:
            if word in collection:
                f.write(repr(collection[word]))
            else:
                f.write('0')
            f.write('\t')
        f.write('\n')

def getapi():
    #This handles Twitter authetification and the connection to Twitter Streaming API
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)

    return api

if __name__ == '__main__':
    api = getapi()

    friends = getfollowers(api)

    collections, nouns = parsetweets(friends)

    saveresults(collections, nouns)