from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.models import *
from linebot.exceptions import InvalidSignatureError
from configparser import ConfigParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
import os, requests, time

# === 設定檔讀取 ===
config = ConfigParser()
config.read("config.ini")

LINE_CHANNEL_ACCESS_TOKEN = config['LINE']['CHANNEL_ACCESS_TOKEN']
LINE_CHANNEL_SECRET = config['LINE']['CHANNEL_SECRET']
GEMINI_API_KEY = config['GEMINI']['API_KEY']
CWB_API_KEY = config['WEATHER']['CWB_API_KEY']
PORT = int(config['SERVER']['PORT'])

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
llm = ChatGoogleGenerativeAI(
    model="models/gemini-1.5-flash",
    google_api_key=GEMINI_API_KEY
)

app = Flask(__name__)
conversation_history = {}

def gemini_generate_response(prompt):
    try:
        messages = [
            SystemMessage(content="你是一位講繁體中文的 LINE 皮卡丘，請用皮卡丘的語氣自然回應使用者。"),
            HumanMessage(content=prompt)
        ]
        result = llm.invoke(messages)
        return result.content
    except Exception as e:
        print(f"Gemini 發生錯誤：{e}")
        return "AI 回應失敗，請稍後再試～"

def save_history(user_id, user_msg, bot_msg):
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    conversation_history[user_id].append({
        "timestamp": int(time.time()),
        "user": user_msg,
        "bot": bot_msg
    })

@app.route("/history", methods=["GET"])
def get_all_history():
    all_records = []
    for uid, history in conversation_history.items():
        for entry in history:
            entry_with_user = entry.copy()
            entry_with_user["user_id"] = uid
            all_records.append(entry_with_user)
    return jsonify(all_records)

@app.route("/history", methods=["DELETE"])
def delete_all_history():
    conversation_history.clear()
    return jsonify({"message": "All conversation history deleted."})

def get_cwb_weather(city="臺北市"):
    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
    params = {
        "Authorization": CWB_API_KEY,
        "locationName": city,
        "format": "JSON"
    }
    try:
        res = requests.get(url, params=params)
        data = res.json()
        records = data["records"]["location"][0]
        weather_desc = records["weatherElement"][0]["time"][0]["parameter"]["parameterName"]
        min_temp = records["weatherElement"][2]["time"][0]["parameter"]["parameterName"]
        max_temp = records["weatherElement"][4]["time"][0]["parameter"]["parameterName"]
        summary = f"{city}目前天氣狀況：{weather_desc}，氣溫範圍：{min_temp}°C - {max_temp}°C"
        return gemini_generate_response(f"請用親切自然的方式告訴使用者以下天氣資訊：{summary}")
    except Exception as e:
        print(f"CWB API 錯誤：{e}")
        return "中央氣象局天氣查詢失敗，請稍後再試。"

def get_city_from_coords(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&accept-language=zh-TW"
        res = requests.get(url, headers={"User-Agent": "line-bot-weather"})
        data = res.json()
        address = data.get("address", {})
        return address.get("city") or address.get("town") or address.get("county") or "臺北市"
    except Exception as e:
        print(f"地理反查錯誤：{e}")
        return "臺北市"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_text = event.message.text.strip()
    user_id = event.source.user_id

    if user_text.lower() in ["貼圖", "sticker"]:
        media_message = StickerSendMessage(package_id='11537', sticker_id='52002740')
        prompt = "使用者想收到貼圖，請給他一句可愛或幽默的回應。"
        reply_text = gemini_generate_response(prompt)
        save_history(user_id, user_text, reply_text)
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=reply_text), media_message])
    elif user_text.lower() in ["圖片", "image"]:
        media_message = ImageSendMessage(
            original_content_url='https://en.meming.world/images/en/6/6e/Surprised_Pikachu.jpg',
            preview_image_url='https://en.meming.world/images/en/6/6e/Surprised_Pikachu.jpg'
        )
        prompt = "使用者請求一張圖片，請用溫暖或有趣的語氣回覆。"
        reply_text = gemini_generate_response(prompt)
        save_history(user_id, user_text, reply_text)
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=reply_text), media_message])
    elif user_text.lower() in ["影片", "video"]:
        media_message = VideoSendMessage(
            original_content_url='https://ckexun.github.io/MemeBot/material/videoplayback.mp4',
            preview_image_url='https://en.meming.world/images/en/6/6e/Surprised_Pikachu.jpg'
        )
        prompt = "使用者請求觀看影片，請用輕鬆語氣回覆。"
        reply_text = gemini_generate_response(prompt)
        save_history(user_id, user_text, reply_text)
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=reply_text), media_message])
    elif user_text.lower().startswith("天氣"):
        city = user_text.replace("天氣", "").strip() or "臺北市"
        reply_text = get_cwb_weather(city)
        save_history(user_id, user_text, reply_text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
    elif user_text in ["地址", "位置", "location"]:
        media_message = LocationSendMessage(
            title="台北 101",
            address="信義路五段7號",
            latitude=25.033964,
            longitude=121.564468
        )
        prompt = "傳送位置資訊給使用者，請自然回覆。"
        reply_text = gemini_generate_response(prompt)
        save_history(user_id, user_text, reply_text)
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=reply_text), media_message])
    else:
        reply_text = gemini_generate_response(f"使用者說：「{user_text}」，請自然回覆。")
        save_history(user_id, user_text, reply_text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

@handler.add(MessageEvent, message=(ImageMessage, VideoMessage, StickerMessage, LocationMessage))
def handle_media(event):
    msg = event.message
    user_id = event.source.user_id

    if isinstance(msg, LocationMessage):
        lat, lon = msg.latitude, msg.longitude
        city = get_city_from_coords(lat, lon)
        reply_text = get_cwb_weather(city)
        save_history(user_id, f"位置：({lat}, {lon})", reply_text)
    elif isinstance(msg, ImageMessage):
        prompt = "使用者傳了一張圖片，請用有趣的方式回覆。"
        reply_text = gemini_generate_response(prompt)
        save_history(user_id, "圖片訊息", reply_text)
    elif isinstance(msg, VideoMessage):
        prompt = "使用者傳了一段影片，請給予自然的回應。"
        reply_text = gemini_generate_response(prompt)
        save_history(user_id, "影片訊息", reply_text)
    elif isinstance(msg, StickerMessage):
        prompt = "使用者傳來貼圖，請可愛回應。"
        reply_text = gemini_generate_response(prompt)
        save_history(user_id, "貼圖訊息", reply_text)
    else:
        prompt = "使用者傳來媒體訊息，請自然回應。"
        reply_text = gemini_generate_response(prompt)
        save_history(user_id, "其他媒體訊息", reply_text)

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    app.run(port=PORT)