# Imports and setup
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import os
import pandas as pd
import sys
import time
import tweepy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

since_id_file = 'since.id'

def inf(text):
    print(f'{datetime.now():%Y%m%d %H:%M:%S.%f} INFO  {text}', flush=True)
    
def err(text):
    print(f'{datetime.now():%Y%m%d %H:%M:%S.%f}ERROR {text}', flush=True)

def get_image_folder():
    img_folder = 'Analyses'
    if not os.path.exists(img_folder):
        os.mkdir(img_folder)
        inf(f'Created "\\{img_folder}" to save analyses charts to')
    else:
        inf(f'Folder "\\{img_folder}" for analyses charts already exists')
    return img_folder

def auth_in_twitter():
    # Get config variable from environment variables
    consumer_key = os.environ.get('twitter_sent_bot_key')
    consumer_secret = os.environ.get('twitter_sent_bot_secret')
    access_token = os.environ.get('twitter_sent_bot_token')
    access_token_secret = os.environ.get('twitter_sent_bot_token_secret')
    if None in [consumer_key, consumer_secret, access_token, access_token_secret]:
        err('Twitter auth tokens are not set as enviroment variables')
        exit(1)
    else:
        inf('Twitter auth tokens are configured')
    # Setup Tweepy API Authentication
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())
    inf('Twitter authentication is performed successfully')
    # Retrieve bot's username
    self_user = api.me()
    self_username = self_user['screen_name']
    inf(f'The application is ran under {self_username} Twitter user')
    return api, self_username

def get_mentions(api, self_username, since_id=None):
    mention_count = 100
    if since_id:
        inf(f'Retrieving last {mention_count} mentions of user "{self_username}" done after {since_id}...')
    else:
        inf(f'Retrieving last {mention_count} mentions of user "{self_username}"')
    mentions = api.search(f'@{self_username}',rpp=mention_count, since_id=since_id).get('statuses')
    mentions = [{
        'id': mention['id'],
        'text': mention['text'],
        'user_mentions': [user_mention['screen_name'] for user_mention in mention['entities']['user_mentions']],
        'user' : mention['user']['screen_name']        
    } for mention in mentions]
    if len(mentions) == 0:
        inf(f'No mentions of "{self_username}" were retrieved at this time')
    else:
        inf(f'Retrieved {len(mentions)} mentions of user "{self_username}"')
    return mentions    

def get_tweets(api, target_username):
    max_id = None
    all_tweets = []
    pages = 1
    tweets_per_page = 100
    for page in range(1, pages + 1):
        try:
            tweets = api.user_timeline(target_username, page=page, count=tweets_per_page, max_id=max_id)
            tweets = [ {
                'id': tweet['id'],
                'text': tweet['text'],
            } for tweet in tweets]
            inf(f'Retrieved next {len(tweets)} tweets of "{target_username}" user')
            all_tweets += tweets
            if not max_id and len(tweets) > 0:
                max_id = tweets[0]['id']
            if len(tweets) < tweets_per_page:
                break
        except Exception as e:
            err(f'Failed to retrieve tweets of "{target_username}" user')
            err(e)
    inf(f'Totally {len(all_tweets)} were retrieved for "{target_username}" user')
    return all_tweets 

def analyze_tweets(api, target_username):
    inf(f'Analyzing tweets of "{target_username}" user')
    tweets = get_tweets(api, target_username)
    analyzer = SentimentIntensityAnalyzer()
    scores = [analyzer.polarity_scores(tweet['text'])['compound'] for tweet in tweets]
    return pd.DataFrame(scores, columns=['Polarity'], index=[-i for i in range(0, len(tweets))])

def get_polarity_color(polarity):
    return (0, polarity, 0) if polarity >= 0 else (-polarity, 0, 0)

def plot_analysis(data, target_username, img_folder):
    inf(f'Plotting the analysis of tweets of "{target_username}" user')
    plt.figure(figsize=(16, 8))
    avg_polarity = data['Polarity'].mean()
    avg_polarity_text = 'Very Positive' if avg_polarity >= 0.75 else                         'Positive' if avg_polarity >= 0.5 else                         'Positively Neutral' if avg_polarity >= 0 else                         'Negatively Neutral' if avg_polarity >= -0.5 else                         'Negative' if avg_polarity >= -0.75 else                         'Very Negative'
    inf(f'Average polarity of "{target_username}" tweets is {avg_polarity} and he is considered {avg_polarity_text}')
    color = get_polarity_color(avg_polarity)
    plt.plot(data.index, data['Polarity'], c=color, linewidth=1, linestyle='solid', marker='o', markersize=3)
    plt.xlim(-len(data.index) + 1, 0)
    plt.xlabel('Tweets Age', fontsize=16)
    plt.ylabel('Tweet Polarity', fontsize=16)
    plt.xticks(fontsize=16)
    plt.yticks([-1, -0.5, 0, 0.5, 1], ['Strongly\nNegative', 'Likely\nNegative', 'Neutral', 'Likely\nPositive', 'Strongly\nPositive'], fontsize=16, ma='left')
    plt.title(f'Sentiment Analysis of @{target_username} Tweets ({datetime.strftime(datetime.now(), "%M/%D/%Y")}\n(Generally, a {avg_polarity_text} User)',fontsize=16)
    plt.grid(alpha=0.3)    
    file_name = os.path.join(img_folder, f'{target_username}.png')
    plt.savefig(file_name)
    inf(f'Chart for analysis of "{target_username}" tweets is saved to "{file_name}"')
    return file_name

def post_analysis(api, file_name, target_username, in_reply_to_username, in_reply_to_status_id):
    tweet_text = f'Hi @{in_reply_to_username} here is the analysis of @{target_username} tweets'
    try:        
        api.update_with_media(file_name, tweet_text, in_reply_to_status_id=in_reply_to_status_id)
        inf(f'Successfully posted a tweet "{tweet_text}"')
    except Exception as e:
        err(f'Failed to post the following tweet "{tweet_text}"')
        err(e)

def post_already_analyzed_notifiction(api, target_user, reply_to_user, in_reply_to_status_id):
    tweet_text = f'Hi @{reply_to_user}, I\'ve already analyzed @{target_user} tweets, find it in my timeline'
    try:
        api.update_status(tweet_text, in_reply_to_status_id)
        inf(f'Successfully posted a tweet "{tweet_text}"')
    except Exception as e:
        err(f'Failed to post the following tweet "{tweet_text}"')
        err(e)    

def post_no_self_analysis_notification(api, reply_to_user, in_reply_to_status_id):
    tweet_text = f'Hi @{reply_to_user}, sorry, but I\'m not going to analyze my own tweets'
    try:
        api.update_status(tweet_text, in_reply_to_status_id)
        inf(f'Successfully posted a tweet "{tweet_text}"')
    except Exception as e:
        err(f'Failed to post the following tweet "{tweet_text}"')
        err(e) 

def post_no_multi_analysis_notification(api, reply_to_user, in_reply_to_status_id):
    tweet_text = f'Hi @{reply_to_user}, sorry, but I\'m not going to analyze multiple users at a time'
    try:
        api.update_status(tweet_text, in_reply_to_status_id)
        inf(f'Successfully posted a tweet "{tweet_text}"')
    except Exception as e:
        err(f'Failed to post the following tweet "{tweet_text}"')
        err(e)

def get_last_since_id():
    if os.path.exists(since_id_file):
        with open(since_id_file, 'r') as file:
            result = file.read()
            if result:
                return int(result)
    return None

def save_last_since_id(since_id):
    if since_id:
        try:
            with open(since_id_file, 'w') as file:
                file.write(str(since_id))        
        except:
            err(f'Failed to save last since_id. Make sure that the file "{since_id_file}" is not open')

def main(threshold_wait_time):
    img_folder = get_image_folder()
    api,self_username = auth_in_twitter()
    analyzed_users = set()
    notified_users = {}
    self_analysis_notified_users = set()
    multi_analysis_notified_users = set()
    since_id = get_last_since_id()
    # This is how often the bot will check for new mentions (in seconds)
    wait_time = 60    
    # This is how long the bot has been running (in seconds)
    total_wait_time = 0
    while True:
        if total_wait_time >= threshold_wait_time:
            inf(f'Bot is shutting down now')
            break
        inf('-' * 40)
        mentions = get_mentions(api, self_username, since_id)
        if len(mentions) > 0:
            since_id = mentions[0]['id']        
        for mention in mentions:        
            tweet_text = mention['text']
            requested_by = mention['user']
            inf(f'Processing tweet "{tweet_text}" done by {requested_by}')
            self_tweet = requested_by == self_username
            if self_tweet:
                inf(f'Tweet "{tweet_text}" is done by the bot itself, so no need to react to it')
                continue
            all_mentions = mention['user_mentions']
            other_users_mentions = set(all_mentions)  
            other_users_mentions.discard(self_username)
            self_analysis = len(all_mentions) > 1 and len(other_users_mentions) == 0
            if self_analysis:
                inf(f'Tweet "{tweet_text}" is done by "{requested_by}" but asks bot to analyze himself')
                if requested_by not in self_analysis_notified_users:
                    self_analysis_notified_users.add(requested_by)
                    post_no_self_analysis_notification(api, requested_by, mention['id'])
                continue
            if len(other_users_mentions) > 1:
                inf(f'Tweet "{tweet_text}" is done by "{requested_by}" but asks bot to analyze multiple user')
                if requested_by not in multi_analysis_notified_users:
                    multi_analysis_notified_users.add(requested_by)
                    post_no_multi_analysis_notification(api, requested_by, mention['id'])
                continue
            if len(other_users_mentions) == 0:
                inf(f'Tweet "{tweet_text}" has a mention of bot but no other users, skipping it')
                continue
            target_username = other_users_mentions.pop()
            # First we check if we've already analyzed the target user
            if target_username in analyzed_users:
                # If we did, then we check if we've already notified the requestor about it
                notified_requestor_about = notified_users.setdefault(requested_by, set())
                # If we did then we do nothing (so we don't duplicate the notification)
                if target_username in notified_requestor_about:
                    continue
                else:
                    notified_requestor_about.add(target_username)
                    post_already_analyzed_notifiction(api, target_username, requested_by, mention['id'])
                    continue
            else:
                analyzed_users.add(target_username)                
            # Peform the analysis
            tweets_analysis = analyze_tweets(api, target_username)
            chart_image = plot_analysis(tweets_analysis, target_username, img_folder)
            post_analysis(api, chart_image, target_username, requested_by, mention['id'])
        save_last_since_id(since_id)
        inf(f'Preparing to wait for {wait_time} seconds')
        time.sleep(wait_time)
        total_wait_time += wait_time
        inf(f'Totally waited for {total_wait_time}/{threshold_wait_time} ({total_wait_time/threshold_wait_time:.2%})')

if __name__ == "__main__":
    # We'll configure the total run time to come from command line or default to 5 minutes
    threshold_wait_time = int(sys.argv[1]) if len(sys.argv) > 1 else 5 * 60
    inf(f'The bot has started and will run for {threshold_wait_time} seconds')
    main(threshold_wait_time)