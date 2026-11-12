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
        self.wfile.write(b"Multi-AI Telegram Bot is running 24/7!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

server_thread = Thread(target=run_server)
server_thread.daemon = True
server_thread.start()

# --- VERIFIED API KEYS SETUP ---
TELEGRAM_TOKEN = "9026606056:AAHfAsmSJgVQ_d5fceopkINUDyJv39BEXag"
GROQ_API_KEY = "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"
DEEPSEEK_API_KEY = "sk-c87b8596a0e24072b170f85a60d27f21"
OPENAI_API_KEY = "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"

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def send_message(chat_id, text, parse_mode="Markdown"):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"Telegram send error: {e}")

# --- INDIVIDUAL SAFE AI FUNCTIONS ---
def call_groq(text):
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": text}]}
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=25)
        data = res.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Groq exception: {e}")
    return None

def call_deepseek(text):
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": text}]}
        res = requests.post("https://api.deepseek.com/chat/completions", json=payload, headers=headers, timeout=25)
        data = res.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"DeepSeek exception: {e}")
    return None

def call_chatgpt(text):
    try:
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": text}]}
        res = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=25)
        data = res.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"ChatGPT exception: {e}")
    return None

# --- CRASH-PROOF AUTO-SWITCHING FALLBACK HANDLER ---
def get_ai_response(text):
    # Sequence: Groq (Fastest) -> DeepSeek -> ChatGPT
    sequence = [
        ("⚡ **Groq AI:**", call_groq),
        ("🚀 **DeepSeek:**", call_deepseek),
        ("🧠 **ChatGPT:**", call_chatgpt)
    ]

    for tag, func in sequence:
        reply = func(text)
        if reply:
            return f"{tag}\n\n{reply}"

    return "❌ Sabhi AI models temporary busy hain. Thodi der baad dobara koshish karein."

def main():
    print("🤖 Bulletproof Multi-AI Telegram Bot is running smoothly...")
    offset = 0

    while True:
        try:
            url = f"{BASE_URL}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(url, timeout=35)
            data = response.json()
            
            if "result" in data:
                for update in data["result"]:
                    # Crucial: Immediately advance offset to prevent loops or double replies
                    offset = update["update_id"] + 1
                    
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        
                        if text == "/start":
                            welcome_msg = (
                                "👋 **Welcome to your Multi-AI Bot!**\n\n"
                                "Bot पूरी तरह तैयार है। अब आप पढ़ाई, कोडिंग या कोई भी सवाल पूछ सकते हैं—जवाब बिल्कुल सटीक और एक बार में मिलेगा!"
                            )
                            send_message(chat_id, welcome_msg)
                        else:
                            reply = get_ai_response(text)
                            send_message(chat_id, reply)
                                
        except Exception as e:
            print(f"Polling loop error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
