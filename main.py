# -*- coding: utf-8 -*-

from flask import Flask, request, render_template
import requests
import json
import logging
import os

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FEISHU_WEBHOOK_URL = "YOUR_FEISHU_WEBHOOK_URL"
RAPIDAPI_KEY = "YOUR_RAPIDAPI_KEY"
RAPIDAPI_HOST = "YOUR_RAPIDAPI_HOST"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/add', methods=['POST'])
def add_user():
    user_id = request.form['user_id']
    with open('user_ids.txt', 'a') as f:
        f.write(f"{user_id}\n")
    logger.info(f"Added user ID: {user_id}")
    return "User ID added."

@app.route('/remove', methods=['POST'])
def remove_user():
    user_id = request.form['user_id']
    with open('user_ids.txt', 'r') as f:
        lines = f.readlines()
    with open('user_ids.txt', 'w') as f:
        for line in lines:
            if line.strip() != user_id:
                f.write(line)
    logger.info(f"Removed user ID: {user_id}")
    return "User ID removed."

def fetch_tweets(user_id):
    url = f"https://twitter154.p.rapidapi.com/user/tweets?user_id={user_id}&limit=1"
    headers = {
        'x-rapidapi-key': RAPIDAPI_KEY,
        'x-rapidapi-host': RAPIDAPI_HOST
    }
    response = requests.get(url, headers=headers)
    logger.info(f"Fetched tweets for user ID: {user_id}")
    return response.json()

def notify_feishu(message):
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        "msg_type": "text",
        "content": {
            "text": message
        }
    }
    response = requests.post(FEISHU_WEBHOOK_URL, headers=headers, data=json.dumps(data))
    logger.info("Sent notification to Feishu")
    return response.json()

@app.route('/check_tweets', methods=['GET'])
def check_tweets():
    with open('user_ids.txt', 'r') as f:
        user_ids = [line.strip() for line in f.readlines()]
    for user_id in user_ids:
        tweets = fetch_tweets(user_id)
        if tweets:
            tweet = tweets[0]  # 假设最新的一条推文
            message = f"New Tweet from {user_id}: {tweet['text']}"
            notify_feishu(message)
    return "Checked tweets and sent notifications."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
