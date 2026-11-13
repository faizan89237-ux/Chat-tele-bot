import os
import time
import requests
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- DUMMY SERVER FOR RENDER ---
class SimpleHandler(BaseHTTPRequestHandler):
    def _ok(self, body=True):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        if body:
            self.wfile.write(b"Fazi Study Bot is running!")

    def do_GET(self):
        self._ok()

    # UptimeRobot etc. often use HEAD requests
    def do_HEAD(self):
        self._ok(body=False)

    def log_message(self, *args):
        pass  # logs ka spam band


def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), SimpleHandler).serve_forever()


Thread(target=run_server, daemon=True).start()

# --- TELEGRAM SETUP ---
# Token ko code mein mat likho. Render > Environment mein TELEGRAM_TOKEN set karo.
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise SystemExit("TELEGRAM_TOKEN environment variable set nahi hai!")

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
MAX_LEN = 4000  # Telegram limit 4096 hai

SYSTEM_PROMPT = (
    "You are Fazi Study Bot, a helpful AI tutor on Telegram. "
    "Reply primarily in natural Roman Urdu unless English is requested. "
    "Give clear, accurate, step-by-step answers for studies, mathematics, "
    "mechanics, and general questions. Do not use markdown formatting."
)


def send_message(chat_id, text):
    """Plain text bhejta hai (Markdown se errors aate the). Lambe text ko tukdon mein todta hai."""
    for i in range(0, len(text), MAX_LEN):
        chunk = text[i:i + MAX_LEN]
        try:
            r = requests.post(
                f"{BASE_URL}/sendMessage",
                json={"chat_id": chat_id, "text": chunk},
                timeout=15,
            )
            if not r.ok:
                print(f"Telegram send failed: {r.status_code} {r.text}")
        except Exception as e:
            print(f"Telegram send error: {e}")


def send_typing(chat_id):
    try:
        requests.post(
            f"{BASE_URL}/sendChatAction",
            json={"chat_id": chat_id, "action": "typing"},
            timeout=5,
        )
    except Exception:
        pass


def clear_pending_updates():
    try:
        requests.get(
            f"{BASE_URL}/deleteWebhook?drop_pending_updates=true", timeout=10
        )
        print("Webhook cleared and pending updates dropped.")
    except Exception as e:
        print(f"Error clearing updates: {e}")


# --- AI FUNCTION (Pollinations, no API key) ---
def get_ai_response(text):
    # Method 1: POST (lambe/special characters wale sawalon ke liye sahi)
    try:
        res = requests.post(
            "https://text.pollinations.ai/openai",
            json={
                "model": "openai",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
            },
            timeout=40,
        )
        if res.status_code == 200:
            answer = res.json()["choices"][0]["message"]["content"].strip()
            if answer:
                return answer
        else:
            print(f"Pollinations POST status: {res.status_code}")
    except Exception as e:
        print(f"Pollinations POST error: {e}")

    # Method 2: GET fallback (safe='' taake "/" waghera URL na tode)
    try:
        prompt = f"{SYSTEM_PROMPT}\nUser: {text}"
        url = "https://text.pollinations.ai/" + requests.utils.quote(prompt, safe="")
        res = requests.get(url, timeout=40)
        if res.status_code == 200 and res.text.strip():
            return res.text.strip()
        print(f"Pollinations GET status: {res.status_code}")
    except Exception as e:
        print(f"Pollinations GET error: {e}")

    return "Maafi chahta hoon, abhi AI server jawab nahi de raha. Thori der baad dobara try karein."


def handle_update(update):
    msg = update.get("message")
    if not msg or "text" not in msg:
        return

    chat_id = msg["chat"]["id"]
    text = msg["text"]

    if text.startswith("/start"):
        send_message(
            chat_id,
            "👋 Welcome to Fazi Study Bot!\n\n"
            "Aap apna koi bhi sawal pooch sakte hain: studies, maths, mechanics ya general.",
        )
        return

    send_typing(chat_id)
    send_message(chat_id, "🤖 Fazi Study Bot:\n\n" + get_ai_response(text))


def main():
    print("🤖 Fazi Study Bot starting up...")
    clear_pending_updates()

    offset = 0
    print("🤖 Polling loop started...")

    while True:
        try:
            r = requests.get(
                f"{BASE_URL}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=40,
            )
            data = r.json()

            if not data.get("ok"):
                # Aam wajah: 409 = bot ka doosra instance bhi chal raha hai
                print(f"getUpdates error: {data}")
                time.sleep(5)
                continue

            for update in data["result"]:
                offset = update["update_id"] + 1
                # Har message alag thread mein, taake AI ke intezar mein bot atke nahi
                Thread(target=handle_update, args=(update,), daemon=True).start()

        except requests.exceptions.ReadTimeout:
            continue
        except Exception as e:
            print(f"Polling loop error: {e}")
            time.sleep(3)


if __name__ == "__main__":
    main()
