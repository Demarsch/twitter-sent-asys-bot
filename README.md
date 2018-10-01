# Twitter Sentiment Analysis Bot

## Summary

A simple Twitter bot written in Python that will perform sentiment analysis of tweets from specific user by request. 

## Installation

The bot can be run locally or deployed to the hosting. This repository contains all required files for the bot to be deployed to Heroku. In order to run successfully, four environment variables must be set on a target machine:

- `twitter_sent_bot_key` that contains Twitter API key

- `twitter_sent_bot_secret` that contains Twitter API secret key

- `twitter_sent_bot_token` that contains Twitter access token

- `twitter_sent_bot_token_secret` that contains access token secret

## Requirements

The bot is written in Python and requires the following dependencies:

- `tweepy == 3.6.0`

- `numpy == 1.15.1`

- `pandas == 0.23.4`

- `matplotlib == 2.2.3`

- `vaderSentiment == 2.5`

## Description

The bot is launched by using console command `python App.py`. Additionaly, an integer argument can be provided that defines the total running time in seconds (default is 360 seconds = 5 minutes). The bot will check every minute for all mentions of the current user and if it detects a tweet where it is mentioned along with another user (target user), it then loads up to 500 latest tweets of the target user, performs a sentiment analysis of them using [VADER](https://github.com/cjhutto/vaderSentiment), plot a line chart of the compound score and reply back to the original tweet posting this chart. The bot tries to prevent abuse by scanning each account only once. Below are some example of these charts

- Tweets of [@HellthyJunkFood](https://twitter.com/HellthyJunkFood)

![HealthyJunkFood](\Images\HellthyJunkFood.png)

- Tweets of [@k_huck](https://twitter.com/k_huck)

![k_huck](\Images\k_huck.png)

- Tweets of [@UCIrvine](https://twitter.com/UCIrvine)

![UCIrvine](\Images\UCIrvine.png)

## Notes

Keep in mind that Twitter will most likely not return mentions that are done by users who is likely not human e.g. if a user post something via Twitter API, do repetitive tweets or just a new user with next to no tweets of follows

P.S. The bot was developed and tested under [@ChaplyginAndrei](https://twitter.com/ChaplyginAndrei) account, follow this link to see more examples
