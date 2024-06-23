import http.client
import json
import requests
import time
import os
from threading import Thread
from flask import Flask, request, render_template_string, redirect, url_for

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")
FEISHU_WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL")

USER_IDS_FILE = 'user_ids.txt'

app = Flask(__name__)


@app.route('/')
def index():
    with open(USER_IDS_FILE, 'r') as f:
        user_ids = f.readlines()
    return render_template_string('''
        <h1>Twitter User ID Monitor</h1>
        <form action="/add" method="post">
            <input type="text" name="user_id" placeholder="Enter User ID" required>
            <input type="submit" value="Add">
        </form>
        <h2>Monitored User IDs</h2>
        <ul>
            {% for user_id in user_ids %}
            <li>{{ user_id }} <a href="{{ url_for('remove', user_id=user_id) }}">Remove</a></li>
            {% endfor %}
        </ul>
    ''', user_ids=[user_id.strip() for user_id in user_ids])


@app.route('/add', methods=['POST'])
def add_user():
    user_id = request.form['user_id']
    with open(USER_IDS_FILE, 'a') as f:
        f.write(user_id + '\n')
    return redirect(url_for('index'))


@app.route('/remove/<user_id>')
def remove_user(user_id):
    user_id = user_id.strip()
    with open(USER_IDS_FILE, 'r') as f:
        user_ids = f.readlines()
    user_ids = [id.strip() for id in user_ids if id.strip() != user_id]
    with open(USER_IDS_FILE, 'w') as f:
        for id in user_ids:
            f.write(id + '\n')
    return redirect(url_for('index'))


def get_user_tweets(user_id):
    conn = http.client.HTTPSConnection(RAPIDAPI_HOST)
    headers = {
        'x-rapidapi-key': RAPIDAPI_KEY,
        'x-rapidapi-host': RAPIDAPI_HOST
    }
    conn.request("GET", f"/user/tweets?user_id={user_id}&limit=1&include_replies=false&include_pinned=false",
                 headers=headers)
    res = conn.getresponse()
    data = res.read()
    if res.status == 200:
        return json.loads(data.decode("utf-8"))
    else:
        print(f"Error: Received status code {res.status}")
        print(f"Response content: {data.decode('utf-8')}")
        return None


def send_feishu_notification(message):
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        "msg_type": "text",
        "content": {
            "text": message
        }
    }
    proxies = {
        "http": None,
        "https": None,
    }
    response = requests.post(FEISHU_WEBHOOK_URL, headers=headers, data=json.dumps(payload), proxies=proxies)
    if response.status_code != 200:
        print(f"Failed to send notification. Status code: {response.status_code}, Response: {response.text}")


def monitor_user_tweets(interval=60):
    last_tweet_ids = {}
    while True:
        print("Fetching updated user list...")
        with open(USER_IDS_FILE, 'r') as f:
            user_ids = [line.strip() for line in f.readlines()]

        for user_id in user_ids:
            if user_id not in last_tweet_ids:
                last_tweet_ids[user_id] = None

            tweets = get_user_tweets(user_id)
            if tweets and "results" in tweets:
                latest_tweet = tweets["results"][0]
                if latest_tweet['tweet_id'] != last_tweet_ids[user_id]:
                    last_tweet_ids[user_id] = latest_tweet['tweet_id']
                    tweet_url = f"https://twitter.com/{latest_tweet['user']['username']}/status/{latest_tweet['tweet_id']}"
                    message = (
                        f"博主 {latest_tweet['user']['username']} 的新推文:\n"
                        f"内容: {latest_tweet['text']}\n"
                        f"链接: {tweet_url}\n"
                        f"发布时间: {latest_tweet['creation_date']}"
                    )
                    print(message)
                    send_feishu_notification(message)
            else:
                print(f"Failed to get tweets for user ID {user_id}")
        time.sleep(interval)


def main():
    if not os.path.exists(USER_IDS_FILE):
        open(USER_IDS_FILE, 'w').close()

    monitor_thread = Thread(target=monitor_user_tweets)
    monitor_thread.start()

    app.run(host='0.0.0.0', port=5000)


if __name__ == "__main__":
    main()
