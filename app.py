from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent
from apscheduler.schedulers.background import BackgroundScheduler
import csv
import os
from pytz import timezone

bangkok = timezone('Asia/Bangkok')
app = Flask(__name__)

# Using environment variables for tokens and secrets
LINE_ACCESS_TOKEN = os.environ.get('LINE_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def init_csv():
    try:
        with open('users.csv', 'x', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["user_id", "display_name"])
    except FileExistsError:
        pass

init_csv()

def user_exists(user_id):
    users = read_users_from_csv()
    return any(user['user_id'] == user_id for user in users)

def add_user_to_csv(user_id, display_name):
    if not user_exists(user_id):
        with open('users.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([user_id, display_name])

def read_users_from_csv():
    users = []
    with open('users.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            users.append({'user_id': row[0], 'display_name': row[1]})
    return users

def send_morning_message():
    for user in read_users_from_csv():
        message = f"อรุณสวัสดิ์ยามเช้าค่ะ คุณ{user['display_name']} เช้านี้ขอให้เป็นเช้าที่สดใสของท่าน เรามาบริหารร่างกายไปด้วยกันนะคะ"
        line_bot_api.push_message(user['user_id'], TextSendMessage(text=message))

def send_evening_exercise_invitation():
    for user in read_users_from_csv():
        message = f"เย็นนี้คุณ{user['display_name']} มาออกกำลังกายกันเถอะ! การออกกำลังกายส่วนสั้น ๆ จะช่วยให้ร่างกายแข็งแรงและสุขภาพดี"
        line_bot_api.push_message(user['user_id'], TextSendMessage(text=message))

scheduler = BackgroundScheduler(timezone=bangkok)
scheduler.add_job(send_morning_message, 'cron', hour=7, minute=0)
scheduler.add_job(send_evening_exercise_invitation, 'cron', hour=17, minute=0)
scheduler.start()

@handler.add(FollowEvent)
def handle_follow(event):
    profile = line_bot_api.get_profile(event.source.user_id)
    add_user_to_csv(profile.user_id, profile.display_name)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="Thanks for adding me!"))

@app.route("/webhook", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except:
        return jsonify({'status':'failed'}), 500

    return jsonify({'status':'success'}), 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))

@app.route("/")
def check():
    return "Hello, your app is running!"

if __name__ == "__main__":
    app.run()
