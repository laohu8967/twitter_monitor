import os
import requests
import json
import time
import http.client
from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)

RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY')
RAPIDAPI_HOST = os.environ.get('RAPIDAPI_HOST')
FEISHU_WEBHOOK_URL = os.environ.get('FEISHU_WEBHOOK_URL')

def get_latest_tweet(user_id):
    conn = http.client.HTTPSConnection(RAPIDAPI_HOST)
    headers = {
        'x-rapidapi-key': RAPIDAPI_KEY,
        'x-rapidapi-host': RAPIDAPI_HOST
    }
    conn.request("GET", f"/user/tweets?user_id={user_id}&limit=1&include_replies=false&include_pinned=false", headers=headers)
    res = conn.getresponse()
    data = res.read()
    tweets = json.loads(data)
    return tweets['results'][0] if 'results' in tweets and tweets['results'] else None

def send_to_feishu(content):
    headers = {
        'Content-Type': 'application/json'
    }
    payload = json.dumps({"text": content})
    response = requests.post(FEISHU_WEBHOOK_URL, headers=headers, data=payload)
    return response.status_code == 200

@app.route('/')
def index():
    with open('user_ids.txt', 'r') as f:
        user_ids = [line.strip() for line in f.readlines()]
    return render_template('index.html', user_ids=user_ids)

@app.route('/add_user_id', methods=['POST'])
def add_user_id():
    user_id = request.form['user_id']
    with open('user_ids.txt', 'a') as f:
        f.write(user_id + '\n')
    return redirect(url_for('index'))

@app.route('/delete_user_id', methods=['POST'])
def delete_user_id():
    user_id = request.form['user_id']
    with open('user_ids.txt', 'r') as f:
        user_ids = [uid.strip() for uid in f.readlines()]
    user_ids = [uid for uid in user_ids if uid != user_id]
    with open('user_ids.txt', 'w') as f:
        for uid in user_ids:
            f.write(uid + '\n')
    return redirect(url_for('index'))

def monitor_tweets():
    while True:
        with open('user_ids.txt', 'r') as f:
            user_ids = [line.strip() for line in f.readlines()]
        for user_id in user_ids:
            tweet = get_latest_tweet(user_id)
            if tweet:
                content = f"博主 {tweet['user']['name']} 发布了新推文:\n{tweet['text']}\n链接: https://twitter.com/{tweet['user']['username']}/status/{tweet['tweet_id']}"
                send_to_feishu(content)
        time.sleep(60)

if __name__ == '__main__':
    from threading import Thread
    Thread(target=monitor_tweets).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
