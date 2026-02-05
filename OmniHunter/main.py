import json
import os
import requests
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from modules.utils import ensure_chrome_ready
from modules.scanner import OmniScanner
from modules.downloader import OmniButcher
from modules.uploader import OmniCourier

# --- KONFIGURASI ---
CONFIG_FILE = "config_sessions.json"
HISTORY_FILE = "history_omni.txt"
console = Console()

# Daftar domain sampah yang PASTI bukan video (Hemat waktu)
BLACKLIST_DOMAINS = [
    "tokopedia.com", "shopee.co.id", "lazada.co.id", "bukalapak.com", 
    "blibli.com", "google.com", "maps.google", "wa.me", "linkedin.com"
]

# --- FUNGSI DATABASE ---
def load_sessions():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f: return json.load(f)
        except: return {}
    return {}

def save_session(name, token, chat_id):
    data = load_sessions()
    data[name] = {"token": token, "chat_id": chat_id}
    with open(CONFIG_FILE, 'w') as f: json.dump(data, f)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f: return set(f.read().splitlines())
    return set()

def save_history(url):
    try:
        with open(HISTORY_FILE, 'a') as f: f.write(f"{url}\n")
    except: pass

def cek_link_pintar(url):
    """
    Fungsi Pintar: Mengintip isi link t.co tanpa mendownloadnya dulu.
    Mengembalikan URL Asli jika aman, atau None jika itu Marketplace.
    """
    try:
        # Kita request HEADER saja (ringan & cepat) untuk melihat redirectnya kemana
        r = requests.head(url, allow_redirects=True, timeout=5)
        real_url = r.url.lower()
        
        # Cek apakah ini link sampah marketplace?
        for domain in BLACKLIST_DOMAINS:
            if domain in real_url:
                return None, real_url # Terdeteksi sampah
        
        return "SAFE", r.url # Aman untuk diproses
    except:
        # Kalau gagal dicek (timeout), anggap saja aman & coba download paksa
        return "SAFE", url

# --- MAIN WORKFLOW ---
def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    title_text = Text("☠️  OMNI-HUNTER: SMART MODE  ☠️", justify="center", style="bold red")
    subtitle_text = Text("Intelligent Filtering & Brutal Execution", justify="center", style="yellow")
    console.print(Panel(Text.assemble(title_text, "\n", subtitle_text), border_style="red"))

    # 1. SESSION MANAGER
    sessions = load_sessions()
    choices = list(sessions.keys()) + ["➕ Buat Sesi Baru"]
    
    selected = questionary.select("Pilih Sesi Bot:", choices=choices).ask()

    if selected == "➕ Buat Sesi Baru":
        name = questionary.text("Nama Sesi:").ask()
        token = questionary.text("Token Bot:").ask()
        chat_id = questionary.text("Chat ID:").ask()
        if name and token and chat_id:
            save_session(name, token, chat_id)
            current_session = {"token": token, "chat_id": chat_id}
            session_name = name
        else: return
    else:
        current_session = sessions[selected]
        session_name = selected

    # 2. LOAD MODULES
    console.print(f"\n[bold]⚙️  Menyiapkan Sesi: [cyan]{session_name}[/cyan]...[/bold]")
    if not ensure_chrome_ready(session_name): return

    scanner = OmniScanner()
    butcher = OmniButcher(download_folder="OMNI_HARVEST")
    courier = OmniCourier(current_session['token'], current_session['chat_id'])
    history = load_history()

    # 3. MISSION CONFIG
    keyword = questionary.text("🎯 Keyword (Enter untuk scan halaman ini):").ask()
    try:
        scrolls = int(questionary.text("🔄 Jumlah Scroll:", default="3").ask())
    except: scrolls = 3

    # 4. EXECUTION
    links = scanner.scan_page(keyword, scrolls)
    total = len(links)
    console.print(f"\n[bold green]⚔️  SCAN SELESAI. {total} Link Terdeteksi. Memulai Seleksi...[/bold green]\n")

    for idx, link in enumerate(links):
        progress = f"[bold white]Target {idx+1}/{total}:[/bold white]"
        
        if link in history:
            console.print(f"{progress} [dim]⏭️  Skip (History): {link}[/dim]")
            continue
            
        console.print(f"{progress} 🔗 Memeriksa: {link}")
        
        # --- FILTER TAHAP 1: CEK TUJUAN LINK ---
        status, real_url = cek_link_pintar(link)
        
        if status is None:
            # Ini artinya link menuju Tokopedia/Shopee/dll
            console.print(f"   🗑️  [dim]Skip Marketplace: {real_url}[/dim]\n")
            save_history(link) # Simpan biar gak dicek lagi
            continue
        
        # Kalau lolos filter, berarti ini Potensi Video atau Link Umum
        console.print(f"   ✅ Lolos Filter. Target: [cyan]{real_url}[/cyan]")
        
        # --- FILTER TAHAP 2: EKSEKUSI DOWNLOAD ---
        try:
            result = butcher.download_video(link)
            
            # Cek hasil download
            if result and len(result) == 2:
                file_path, title = result
                
                if file_path and os.path.exists(file_path):
                    # --- TAHAP 3: UPLOAD ---
                    caption = f"💀 OMNI-HUNTER\n📂 {title}\n🔗 {link}"
                    if courier.kirim_paket(file_path, caption):
                        try: os.remove(file_path)
                        except: pass
                        save_history(link)
                        console.print(f"   ✨ [bold green]SUKSES & CLEAN.[/bold green]\n")
                    else:
                        console.print(f"   ⚠️ Gagal Upload (Koneksi?). File tersimpan lokal.\n")
                else:
                    # yt-dlp selesai tapi file gak ada (jarang terjadi)
                    console.print("   ❌ File tidak ditemukan setelah proses.\n")
                    save_history(link)
            else:
                # yt-dlp gagal ekstrak (Mungkin bukan video, atau butuh login)
                console.print("   ⚠️  Gagal Ekstrak Video (Mungkin artikel/foto).\n")
                # Kita catat history supaya next run lebih cepat
                save_history(link)

        except Exception as e:
            console.print(f"   ❌ Error Sistem pada link ini: {e}\n")
            continue

    console.print(Panel("[bold green]✅ MISI SELESAI.[/bold green]", border_style="green"))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]⚠️  Force Close.[/bold red]")