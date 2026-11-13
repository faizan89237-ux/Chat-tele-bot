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
        self.wfile.write(b"Gemini Telegram Bot is running 24/7!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

server_thread = Thread(target=run_server)
server_thread.daemon = True
server_thread.start()

# --- CONFIGURATION ---
TELEGRAM_TOKEN = "9026606056:AAHfAsmSJgVQ_d5fceopkINUDyJv39BEXag"
GEMINI_API_KEY = "AQ.Ab8RN6IBnU303Lm5mHobwVUxHh7wVtfE0Q6XL060aH1fx2VCrg"

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def send_message(chat_id, text, parse_mode="Markdown"):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"Telegram send error: {e}")

# --- CLEAR PENDING UPDATES TO PREVENT LOOPING ---
def clear_pending_updates():
    try:
        requests.get(f"{BASE_URL}/deleteWebhook?drop_pending_updates=true", timeout=10)
        print("Webhook cleared successfully.")
    except Exception as e:
        print(f"Error clearing updates: {e}")

# --- GEMINI AI API CALL ---
def call_gemini(text):
    try:
        # Using Gemini Flash model endpoint with custom header key
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": GEMINI_API_KEY
        }
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": text}
                    ]
                }
            ]
        }
        res = requests.post(url, json=payload, headers=headers, timeout=30)
        data = res.json()
        
        if "candidates" in data and len(data["candidates"]) > 0:
            content = data["candidates"][0]["content"]
            if "parts" in content and len(content["parts"]) > 0:
                return content["parts"][0]["text"]
        elif "error" in data:
            return f"❌ Gemini API Error: {data['error'].get('message', 'Unknown error')}"
            
        return "❌ Maaf kijiye, Gemini se koi jawab nahi mil paaya."
    except Exception as e:
        print(f"Gemini exception: {e}")
        return f"❌ Connection Exception: {str(e)}"

def main():
    print("🤖 Gemini Telegram Bot starting up...")
    clear_pending_updates()
    
    offset = 0
    print("🤖 Polling loop started successfully...")

    while True:
        try:
            url = f"{BASE_URL}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(url, timeout=35)
            data = response.json()
            
            if "result" in data:
                for update in data["result"]:
                    # Instantly advance offset to avoid message loops/duplicates
                    offset = update["update_id"] + 1
                    
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        
                        if text == "/start":
                            welcome_msg = (
                                "👋 **Welcome to your Gemini AI Bot!**\n\n"
                                "Bot पूरी तरह एक्टिव है। अब आप कोई भी सवाल पूछ सकते हैं—जवाब बिल्कुल सटीक और एक बार में मिलेगा!"
                            )
                            send_message(chat_id, welcome_msg)
                        else:
                            reply = call_gemini(text)
                            send_message(chat_id, reply)
                                
        except Exception as e:
            print(f"Polling loop error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
