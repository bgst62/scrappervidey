import os
import re
import time
from telethon import TelegramClient
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# --- DATA API & TARGET ---
API_ID = 36726942
API_HASH = 'ee214f506f24bdee3de2686ceb75dd72'
GROUP_TARGET = 'misterikalten' 
SAVE_FOLDER = os.path.abspath("hasil_sedotan_asli")
SESSION_FOLDER = "sesi_telegram"

if not os.path.exists(SAVE_FOLDER): os.makedirs(SAVE_FOLDER)
if not os.path.exists(SESSION_FOLDER): os.makedirs(SESSION_FOLDER)

# --- SETUP CHROME ---
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

prefs = {
    "download.default_directory": SAVE_FOLDER,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": False
}
chrome_options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": SAVE_FOLDER})

# FIXED: Hanya satu inisialisasi client agar file sesi masuk folder
client = TelegramClient(os.path.join(SESSION_FOLDER, 'sesi_misteri_fix'), API_ID, API_HASH)

async def main():
    await client.start()
    print(f"📡 Menyisir grup: {GROUP_TARGET}...")
    
    entity = await client.get_entity(GROUP_TARGET)
    total_berhasil = 0

    async for message in client.iter_messages(entity, limit=500):
        if total_berhasil >= 30: break
        
        pp_urls = []
        if message.text:
            pp_urls.extend(re.findall(r'https?://pastepad\.net/[a-zA-Z0-9]+', message.text))
        
        if message.reply_markup:
            for row in message.reply_markup.rows:
                for btn in row.buttons:
                    if hasattr(btn, 'url') and 'pastepad.net' in btn.url:
                        pp_urls.append(btn.url)

        for pp_url in list(set(pp_urls)):
            if total_berhasil >= 30: break
            
            print(f"🎯 Membuka Pastepad: {pp_url}")
            driver.get(pp_url)
            time.sleep(5) 
            
            content = driver.page_source
            mf_links = re.findall(r'https?://(?:www\.)?mediafires\.co/file/[a-zA-Z0-9]+', content)

            for mf_url in list(dict.fromkeys(mf_links)):
                if total_berhasil >= 30: break # FIXED: Sinkronisasi ke 30
                
                print(f"   🔎 Membuka Mediafire: {mf_url}")
                driver.get(mf_url)
                time.sleep(5)

                try:
                    download_btn = driver.find_element(By.XPATH, "//a[contains(@href, '/download/')]")
                    direct_link = download_btn.get_attribute('href')
                    file_name = direct_link.split('/')[-1]
                    path_tujuan = os.path.join(SAVE_FOLDER, file_name)

                    if os.path.exists(path_tujuan):
                        print(f"   ⏩ Skip: {file_name} (Sudah ada)")
                        continue 

                    print(f"   🔗 Link Asli Ketemu: {file_name}")
                    driver.get(direct_link)
                    
                    total_berhasil += 1
                    
                    # LOGIKA DEWA: Monitor proses download (Smart Wait)
                    print(f"   📥 Sedang menyedot ({total_berhasil}/30)...", end="", flush=True)
                    start_time = time.time()
                    while True:
                        # Cek apakah ada file .crdownload di folder
                        files = os.listdir(SAVE_FOLDER)
                        is_downloading = any(".crdownload" in f for f in files)
                        
                        if not is_downloading and (time.time() - start_time) > 5:
                            # Jika tidak ada .crdownload dan sudah jalan minimal 5 detik
                            print(" ✅ Selesai!")
                            break
                        
                        if (time.time() - start_time) > 120: # Timeout 2 menit
                            print(" ⚠️ Waktu habis, lanjut ke file berikutnya.")
                            break
                        
                        time.sleep(2) # Cek tiap 2 detik
                        print(".", end="", flush=True)

                except Exception as e:
                    print(f"   ❌ Gagal: {e}")

with client:
    try:
        client.loop.run_until_complete(main())
    finally:
        driver.quit()
        print(f"\n✨ Selesai! Semua video di '{SAVE_FOLDER}' sudah rapi.")