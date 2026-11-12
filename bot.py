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
        self.wfile.write(b"Stable Groq AI Telegram Bot is running 24/7!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

server_thread = Thread(target=run_server)
server_thread.daemon = True
server_thread.start()

# --- VERIFIED API KEY SETUP ---
TELEGRAM_TOKEN = "9026606056:AAHfAsmSJgVQ_d5fceopkINUDyJv39BEXag"
GROQ_API_KEY = "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"

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def send_message(chat_id, text, parse_mode="Markdown"):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"Telegram send error: {e}")

# --- FAST, DETAILED & STABLE AI FUNCTION ---
def get_ai_response(text):
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        # Structured prompt to ensure normal length, clear formatting, and good detail
        prompt_text = f"{text}\n\n(Note: Provide a clear, well-structured, and appropriately detailed response in a normal readable length.)"
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt_text}]
        }
        
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=30)
        data = res.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            reply = data["choices"][0]["message"]["content"]
            return f"⚡ **Groq AI:**\n\n{reply}"
        elif "error" in data:
            err_msg = data["error"].get("message", "Unknown API error")
            return f"❌ **API Error:** {err_msg}"
        else:
            return f"❌ **Response Error:** {str(data)}"
            
    except Exception as e:
        return f"❌ **Connection Exception:** {str(e)}"

def main():
    print("🤖 Stable Groq Telegram Bot is running smoothly...")
    offset = 0

    while True:
        try:
            url = f"{BASE_URL}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(url, timeout=35)
            data = response.json()
            
            if "result" in data:
                for update in data["result"]:
                    # Immediately advance offset so messages never duplicate or loop
                    offset = update["update_id"] + 1
                    
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        
                        if text == "/start":
                            welcome_msg = (
                                "👋 **Welcome to your Super-Fast AI Bot!**\n\n"
                                "Bot पूरी तरह तैयार है। अब आप पढ़ाई, कोडिंग या कोई भी सवाल भेज सकते हैं—जवाब बिल्कुल सटीक और एक बार में मिलेगा!"
                            )
                            send_message(chat_id, welcome_msg)
                        else:
                            reply = get_ai_response(text)
                            send_message(chat_id, reply)
                                
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
