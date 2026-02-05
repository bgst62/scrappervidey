import os
import re
import time
import requests
import subprocess
import shutil
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# --- KONFIGURASI PERMANEN ---
TOKEN_BOT = "8215131409:AAE6PQuyfdJ4DXXxG7PWh2yyABYBrmy_HBA"
CHAT_ID = "7988374944"
DB_FILE = "history_panen.txt"

class XHunterProgress:
    def __init__(self):
        self.start_time = datetime.now()
        self.total_session_panen = 0
        self.status_sekarang = "Standby 😴"
        self.folder = "panen_x_videy"
        
        if not os.path.exists(self.folder): os.makedirs(self.folder)
        self.history = self.load_history()
        self.ensure_chrome_open()
        
        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def load_history(self):
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f: return set(f.read().splitlines())
        return set()

    def ensure_chrome_open(self):
        try:
            requests.get("http://127.0.0.1:9222/json", timeout=2)
        except:
            chrome_bin = shutil.which("google-chrome") or shutil.which("google-chrome-stable")
            user_data = os.path.expanduser("~/.config/king_persistent_x")
            subprocess.Popen([
                chrome_bin, "--remote-debugging-port=9222", 
                f"--user-data-dir={user_data}", "https://x.com/login"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(8)

    def kirim_telegram(self, pesan, is_video=False, file_path=None):
        """Kirim dengan sistem retry & Notifikasi Upload"""
        url = f"https://api.telegram.org/bot{TOKEN_BOT}/" + ("sendVideo" if is_video else "sendMessage")
        
        # Jika video, beri tahu user sebelum proses upload dimulai
        if is_video and file_path:
            size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)
            self.kirim_telegram(f"🚀 *Uploading:* `{os.path.basename(file_path)}` ({size_mb} MB)...")

        for i in range(3):
            try:
                if is_video:
                    with open(file_path, 'rb') as v:
                        r = requests.post(url, data={'chat_id': CHAT_ID, 'caption': pesan}, files={'video': v}, timeout=180)
                else:
                    r = requests.post(url, data={'chat_id': CHAT_ID, 'text': pesan, 'parse_mode': 'Markdown'}, timeout=30)
                
                if r.status_code == 200: return True
            except:
                time.sleep(5)
        return False

    def sedot_file_verifikasi(self, v_id):
        if v_id in self.history: return
        
        filename = os.path.join(self.folder, f"{v_id}.mp4")
        cdn_url = f"https://cdn.videy.co/{v_id}.mp4"
        
        try:
            response = self.session.get(cdn_url, stream=True, headers={'Referer': 'https://videy.co/'}, timeout=30)
            total_size = int(response.headers.get('content-length', 0))
            size_mb = round(total_size / (1024 * 1024), 2)
            
            if response.status_code == 200:
                # Progress Notifier: Downloading
                print(f"⬇️ Mengunduh: {v_id} ({size_mb} MB)")
                self.kirim_telegram(f"⬇️ *Downloading:* `{v_id}.mp4` ({size_mb} MB)")
                
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024*1024):
                        if chunk: f.write(chunk)
                
                # Verifikasi & Kirim
                if os.path.getsize(filename) >= total_size:
                    if self.kirim_telegram(f"🎯 Panen: {v_id}", is_video=True, file_path=filename):
                        os.remove(filename)
                        with open(DB_FILE, "a") as f: f.write(f"{v_id}\n")
                        self.history.add(v_id)
                        self.total_session_panen += 1
                else:
                    os.remove(filename)
        except: pass

    def jalankan_perintah(self, keyword):
        self.status_sekarang = f"Berburu: {keyword} 🏹"
        self.driver.get(f"https://x.com/search?q={keyword}&f=live")
        time.sleep(7)
        
        for i in range(10):
            tweets = self.driver.find_elements(By.XPATH, "//div[@data-testid='tweetText']")
            found_ids = []
            for tweet in tweets:
                matches = re.findall(r'cdn\.videy\.co/([a-zA-Z0-9]+)\.mp4|id=([a-zA-Z0-9]+)', tweet.text)
                for m in matches:
                    v_id = m[0] if m[0] else m[1]
                    if v_id and v_id not in self.history: found_ids.append(v_id)
            
            if found_ids:
                # Hilangkan duplikat di satu layar
                found_ids = list(dict.fromkeys(found_ids))
                self.kirim_telegram(f"🔎 *Scan {i+1}:* Ditemukan {len(found_ids)} video baru.")
                for v_id in found_ids:
                    self.sedot_file_verifikasi(v_id)
            
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)
            
        self.status_sekarang = "Standby 😴"
        self.kirim_telegram(f"✅ Selesai panen: *{keyword}*")

    def listen_telegram(self):
        # Abaikan chat lama saat bot baru nyala
        url_init = f"https://api.telegram.org/bot{TOKEN_BOT}/getUpdates"
        res_init = requests.get(url_init).json()
        updates = res_init.get("result", [])
        last_id = updates[-1]["update_id"] if updates else 0
        
        self.kirim_telegram("🔥 *Bot Hunter Aktif!*\nKirim `/panen [keyword]`")
        print("🤖 Bot Ready!")

        while True:
            try:
                url = f"https://api.telegram.org/bot{TOKEN_BOT}/getUpdates?offset={last_id + 1}"
                res = requests.get(url, timeout=10).json()
                for update in res.get("result", []):
                    last_id = update["update_id"]
                    msg = update.get("message", {}).get("text", "")
                    if msg == "/status": self.kirim_status()
                    elif msg.startswith("/panen"):
                        kw = msg.split(" ")[1] if len(msg.split(" ")) > 1 else "videy.co"
                        self.jalankan_perintah(kw)
            except: pass
            time.sleep(3)

    def kirim_status(self):
        uptime = str(datetime.now() - self.start_time).split('.')[0]
        msg = f"👑 *STATUS REPORT*\n🕒 Uptime: `{uptime}`\n📊 Kondisi: `{self.status_sekarang}`\n🎥 Total Panen: `{self.total_session_panen}`"
        self.kirim_telegram(msg)

if __name__ == "__main__":
    XHunterProgress().listen_telegram()