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
        self.wfile.write(b"Fazi Study Bot is running 24/7!")

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

# --- AI ASSISTANT FUNCTION (ONE-TIME RESPONSE) ---
def get_ai_response(text):
    try:
        system_prompt = (
            "You are Fazi Study Bot, a helpful AI tutor on Telegram. "
            "Reply primarily in natural Roman Urdu unless English is requested. "
            "Give clear, accurate, step-by-step answers for studies, mathematics, mechanics, and general questions."
        )
        
        prompt_full = f"{system_prompt}\nUser: {text}"
        
        # Pollinations AI ki free public API (No API Key Required)
        url = f"https://text.pollinations.ai/{requests.utils.quote(prompt_full)}"
        res = requests.get(url, timeout=25)
        
        if res.status_code == 200 and res.text.strip():
            return f"🤖 **Fazi Study Bot:**\n\n{res.text.strip()}"
            
    except Exception as e:
        print(f"API exception: {e}")
    
    return f"🤖 **Fazi Study Bot:** Main aapka yeh sawal samajh gaya hoon: '{text}'. Aap mazeed tafseel pooch sakte hain!"

def main():
    print("🤖 Fazi Study Bot starting up...")
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
                    # CRITICAL: Offset ko foran update karna taake message bar bar repeat na ho
                    update_id = update["update_id"]
                    offset = update_id + 1
                    
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        
                        if text == "/start":
                            welcome_msg = (
                                "👋 **Welcome to Fazi Study Bot!**\n\n"
                                "Bot ab bilkul tayyar hai. Har sawal ka जवाब **sirf ek baar** aur bilkul theek milega!\n\n"
                                "Aap apna koi bhi sawal pooch sakte hain!"
                            )
                            send_message(chat_id, welcome_msg)
                        else:
                            # Har user message ka response sirf aik hi dafa bheja jaye ga
                            reply = get_ai_response(text)
                            send_message(chat_id, reply)
                                
        except Exception as e:
            print(f"Polling loop error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
