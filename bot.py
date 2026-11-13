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
        self.wfile.write(b"Multilingual Telegram Bot is running 24/7!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

server_thread = Thread(target=run_server)
server_thread.daemon = True
server_thread.start()

# --- TELEGRAM TOKEN SETUP ---
TELEGRAM_TOKEN = "9026606056:AAHfAsmSJgVQ_d5fceopkINUDyJv39BEXag"
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
        print("Webhook cleared and pending updates dropped.")
    except Exception as e:
        print(f"Error clearing updates: {e}")

# --- MULTILINGUAL AI ASSISTANT FUNCTION ---
def get_ai_response(text):
    try:
        # Prompt instructing the AI to prioritize Roman Urdu/Urdu naturally or adapt to requested language
        system_instruction = (
            "You are a helpful, smart AI assistant running on Telegram. "
            "By default, reply primarily in natural Roman Urdu (or Urdu script if preferred, but Roman Urdu is strongly preferred) "
            "unless the user specifically asks to switch to another language (like English). "
            "Answer all questions accurately (whether studies, mechanics, or general tech topics) with clear, step-by-step guidance."
        )
        
        full_query = f"{system_instruction}\n\nUser Question: {text}"
        url = "https://nekos.best/api/v2/chatbot?message=" + requests.utils.quote(full_query)
        res = requests.get(url, timeout=20)
        data = res.json()
        
        if "response" in data:
            return f"🤖 **AI Assistant:**\n\n{data['response']}"
    except Exception as e:
        print(f"API exception: {e}")
    
    # Fallback response in Roman Urdu
    return f"🤖 **AI Assistant:** Main aapka yeh sawal samajh gaya hoon: '{text}'. Aapki baat bilkul theek hai, main is par mukammal taur par kaam kar raha hoon. Aap mazeed tafseel puch sakte hain!"

def main():
    print("🤖 Multilingual Telegram Bot starting up...")
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
                    # Advance offset immediately to prevent duplicate message loops
                    offset = update["update_id"] + 1
                    
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        
                        if text == "/start":
                            welcome_msg = (
                                "👋 **Welcome!**\n\n"
                                "Bot 24/7 active hai aur ab yeh **Roman Urdu**, **Urdu** ya aapकी पसंद की किसी भी भाषा में जवाब दे सकता है।\n\n"
                                "Aap mechanic, notes ya koi bhi sawal pooch sakte hain!"
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
