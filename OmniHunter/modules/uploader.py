import os
import requests
import asyncio
from rich.console import Console

# --- JANTUNG BUATAN (MONKEY PATCH) ---
# Ini WAJIB ada di paling atas sebelum import Mega
# Fungsinya untuk menghidupkan kembali fitur lama yang dihapus di Python 3.12
if not hasattr(asyncio, 'coroutine'):
    asyncio.coroutine = lambda x: x
# -------------------------------------

try:
    from mega import Mega
except ImportError:
    print("Library 'mega.py' belum diinstall. Jalankan: pip install mega.py")
    exit()

console = Console()

class OmniCourier:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{token}/sendMessage"
        
        # --- KONFIGURASI MEGA ---
        # Ganti dengan akun aslimu!
        self.email = "sixk5265@gmail.com"
        self.password = "YTTA_mawon"
        
        self.mega = Mega()
        self.m = None
        
        # Langsung login saat bot nyala
        self.login_mega()

    def kirim_notif_tele(self, pesan):
        try:
            requests.post(self.api_url, data={'chat_id': self.chat_id, 'text': pesan, 'parse_mode': 'Markdown'})
        except: pass

    def login_mega(self):
        """Sistem Login dengan Retry"""
        console.print(f"   ☁️  [yellow]Mencoba Login MEGA ({self.email})...[/yellow]")
        
        try:
            # Login User
            self.m = self.mega.login(self.email, self.password)
            
            # Cek Quota untuk memastikan login valid
            quota = self.m.get_storage_space(giga=True)
            console.print(f"   ✅ [green]Login Sukses![/green] Sisa Storage: {quota['used']:.2f} GB / {quota['total']:.2f} GB")
            return True
            
        except Exception as e:
            console.print(f"   ❌ [red]Gagal Login MEGA:[/red] {e}")
            console.print("      👉 Tips: Pastikan 2FA Mati, Password Benar, atau Coba Ganti Server VPN.")
            self.m = None
            return False

    def kirim_paket(self, file_path, caption):
        if not os.path.exists(file_path): return False
        
        # Auto-Login kalau belum login
        if not self.m:
            if not self.login_mega():
                self.kirim_notif_tele("⚠️ Gagal Upload: Bot tidak bisa login ke MEGA.")
                return False

        file_size = os.path.getsize(file_path) / (1024 * 1024)
        file_name = os.path.basename(file_path)
        
        console.print(f"   ☁️  [cyan]Uploading to MEGA:[/cyan] {file_name} ({file_size:.2f} MB)...")
        self.kirim_notif_tele(f"⏳ *Sedang Upload ke MEGA...*\n📂 `{file_name}` ({file_size:.2f} MB)")

        try:
            # PROSES UPLOAD
            # Kita gunakan dest=None biar masuk ke Root folder (Cloud Drive utama)
            uploaded_file = self.m.upload(file_path)
            
            # GENERATE LINK
            # Link yang dihasilkan langsung mengarah ke file
            link = self.m.get_upload_link(uploaded_file)
            
            console.print(f"   ✅ Upload Sukses! Link: {link}")
            
            # Kirim ke Telegram
            pesan_final = f"{caption}\n\n☁️ *MEGA CLOUD*\n🔗 {link}"
            self.kirim_notif_tele(pesan_final)
            
            return True

        except Exception as e:
            console.print(f"   ❌ Error Upload MEGA: {e}")
            # Kadang error karena session habis, coba login ulang sekali lagi
            console.print("      🔄 Mencoba relogin dan upload ulang...")
            if self.login_mega():
                try:
                    uploaded_file = self.m.upload(file_path)
                    link = self.m.get_upload_link(uploaded_file)
                    self.kirim_notif_tele(f"{caption}\n\n☁️ *MEGA CLOUD*\n🔗 {link}")
                    return True
                except:
                    pass
            
            self.kirim_notif_tele(f"⚠️ Gagal Upload MEGA: {file_name}")
            return False