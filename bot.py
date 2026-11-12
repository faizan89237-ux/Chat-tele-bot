import time
import requests
import os
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- DUMMY SERVER FOR RENDER (Keeps Web Service Alive 24/7) ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Multi-AI Telegram Bot is active and running 24/7!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

server_thread = Thread(target=run_server)
server_thread.daemon = True
server_thread.start()

# --- VERIFIED API KEYS SETUP ---
TELEGRAM_TOKEN = "9026606056:AAHfAsmSJgVQ_d5fceopkINUDyJv39BEXag"
OPENAI_API_KEY = "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"
GROQ_API_KEY = "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"
DEEPSEEK_API_KEY = "sk-c87b8596a0e24072b170f85a60d27f21"

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
user_selected_model = {}

def send_message(chat_id, text, reply_markup=None, parse_mode="Markdown"):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"Telegram send error: {e}")

def send_photo(chat_id, photo_url, caption=""):
    url = f"{BASE_URL}/sendPhoto"
    payload = {"chat_id": chat_id, "photo": photo_url, "caption": caption}
    try:
        requests.post(url, json=payload, timeout=20)
    except Exception as e:
        print(f"Telegram photo error: {e}")

# --- INDIVIDUAL AI FUNCTIONS ---
def call_groq(text):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": text}]}
    res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=25)
    data = res.json()
    if "choices" in data:
        return data["choices"][0]["message"]["content"]
    raise Exception(str(data))

def call_deepseek(text):
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": text}]}
    res = requests.post("https://api.deepseek.com/chat/completions", json=payload, headers=headers, timeout=25)
    data = res.json()
    if "choices" in data:
        return data["choices"][0]["message"]["content"]
    raise Exception(str(data))

def call_chatgpt(text):
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": text}]}
    res = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=25)
    data = res.json()
    if "choices" in data:
        return data["choices"][0]["message"]["content"]
    raise Exception(str(data))

# --- SMART MULTI-MODEL FALL-BACK HANDLER ---
def get_ai_response(user_id, text):
    model = user_selected_model.get(user_id, "groq")
    
    if model == "image":
        try:
            headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
            payload = {"model": "dall-e-3", "prompt": text, "size": "1024x1024", "n": 1}
            res = requests.post("https://api.openai.com/v1/images/generations", json=payload, headers=headers, timeout=35)
            data = res.json()
            if "data" in data:
                return {"type": "photo", "url": data["data"][0]["url"], "caption": f"🎨 **Image Prompt:** {text}"}
            else:
                return {"type": "text", "text": f"❌ Image Error: {str(data)}"}
        except Exception as e:
            return {"type": "text", "text": f"❌ Image Exception: {str(e)}"}

    # Order of models to try (Primary user choice first, then auto-fallback to others)
    sequence = []
    if model == "groq":
        sequence = [("⚡ **Groq (Llama 3):**", call_groq), ("🚀 **DeepSeek (Backup):**", call_deepseek), ("🧠 **ChatGPT (Backup):**", call_chatgpt)]
    elif model == "deepseek":
        sequence = [("🚀 **DeepSeek:**", call_deepseek), ("⚡ **Groq (Llama 3 - Backup):**", call_groq), ("🧠 **ChatGPT (Backup):**", call_chatgpt)]
    elif model == "chatgpt":
        sequence = [("🧠 **ChatGPT:**", call_chatgpt), ("⚡ **Groq (Llama 3 - Backup):**", call_groq), ("🚀 **DeepSeek (Backup):**", call_deepseek)]

    # Trying one by one; if one fails, it automatically jumps to the next without crashing!
    for tag, func in sequence:
        try:
            reply = func(text)
            if reply:
                return {"type": "text", "text": f"{tag}\n\n{reply}"}
        except Exception as e:
            print(f"Model failed, switching to next. Error: {e}")
            continue

    return {"type": "text", "text": "❌ Sabhi AI models temporary busy hain. Thodi der baad dobara koshish karein."}

def main():
    print("🤖 Bulletproof Multi-AI Telegram Bot is running 24/7...")
    offset = 0
    
    model_keyboard = {
        "inline_keyboard": [
            [{"text": "⚡ Groq (Llama)", "callback_data": "model_groq"},
             {"text": "🚀 DeepSeek", "callback_data": "model_deepseek"}],
            [{"text": "🧠 ChatGPT", "callback_data": "model_chatgpt"},
             {"text": "🎨 Image Generation", "callback_data": "model_image"}]
        ]
    }

    while True:
        try:
            url = f"{BASE_URL}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(url, timeout=35)
            data = response.json()
            
            if "result" in data:
                for update in data["result"]:
                    offset = update["update_id"] + 1
                    
                    if "callback_query" in update:
                        cq = update["callback_query"]
                        user_id = cq["from"]["id"]
                        chat_id = cq["message"]["chat"]["id"]
                        data_val = cq["data"]
                        
                        if data_val == "model_groq":
                            user_selected_model[user_id] = "groq"
                            send_message(chat_id, "✅ **Model Switched:** ⚡ Groq active hai!")
                        elif data_val == "model_deepseek":
                            user_selected_model[user_id] = "deepseek"
                            send_message(chat_id, "✅ **Model Switched:** 🚀 DeepSeek active hai!")
                        elif data_val == "model_chatgpt":
                            user_selected_model[user_id] = "chatgpt"
                            send_message(chat_id, "✅ **Model Switched:** 🧠 ChatGPT active hai!")
                        elif data_val == "model_image":
                            user_selected_model[user_id] = "image"
                            send_message(chat_id, "🎨 **Mode Switched:** Image Generation active hai!\nDescription bhejen.")
                        continue

                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        user_id = update["message"]["from"]["id"]
                        text = update["message"]["text"]
                        
                        if text == "/start":
                            user_selected_model[user_id] = "groq"
                            welcome_msg = (
                                "👋 **Welcome to your Bulletproof Multi-AI Bot!**\n\n"
                                "Current Active Model: ⚡ **Groq (Llama 3)**\n\n"
                                "Neeche diye gaye buttons se model change karein:"
                            )
                            send_message(chat_id, welcome_msg, reply_markup=model_keyboard)
                        else:
                            send_message(chat_id, "⏳ AI jawab tayyar kar raha है...")
                            result = get_ai_response(user_id, text)
                            if result["type"] == "photo":
                                send_photo(chat_id, result["url"], caption=result["caption"])
                            else:
                                send_message(chat_id, result["text"])
                                
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
