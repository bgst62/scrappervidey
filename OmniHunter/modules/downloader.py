import os
import requests
import yt_dlp
import re
import time
import random
from rich.console import Console
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

console = Console()

class OmniButcher:
    def __init__(self, download_folder="OMNI_HARVEST"):
        self.folder = download_folder
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)

    def get_headers(self, target_url=""):
        """Header Pintar: Menyesuaikan Referer sesuai Target"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': '*/*',
            'Connection': 'keep-alive',
        }

        # LOGIKA KHUSUS VIDEY
        # Kalau mau ambil dari Videy, bilang kita dari Videy.
        if "videy.co" in target_url:
            headers['Referer'] = 'https://videy.co/'
            headers['Origin'] = 'https://videy.co'
        else:
            headers['Referer'] = 'https://x.com/'
        
        return headers

    def unwrap_link(self, url):
        try:
            # Unwrap pakai header umum dulu
            r = requests.head(url, allow_redirects=True, timeout=5, verify=False)
            return r.url
        except: return url

    def download_manual(self, url, depth=0):
        if depth > 2: return None, None

        try:
            clean_url = url.split("?")[0]
            filename_raw = clean_url.split("/")[-1]
            if not filename_raw.endswith(".mp4"):
                filename_raw = f"extracted_{int(time.time())}.mp4"
            else:
                filename_raw = re.sub(r'[^\w\-_\.]', '', filename_raw)

            save_path = os.path.join(self.folder, filename_raw)
            
            # SESSION BARU
            session = requests.Session()
            # PENTING: Generate header sesuai URL target saat ini
            session.headers.update(self.get_headers(url))
            
            try:
                r = session.get(url, stream=True, timeout=20, verify=False)
                
                # Cek khusus 404
                if r.status_code == 404:
                    console.print(f"      ❌ File Ghaib (404): Link ada, tapi file sudah dihapus server.")
                    return None, None
                
                r.raise_for_status()
            except Exception as e:
                console.print(f"      ❌ Gagal Akses: {e}")
                return None, None

            content_type = r.headers.get('content-type', '').lower()
            
            # SKENARIO 1: VIDEO
            if 'video' in content_type or 'octet-stream' in content_type or 'mp2t' in content_type:
                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        f.write(chunk)
                return save_path, "Direct Video (Manual)"

            # SKENARIO 2: HTML
            elif 'text/html' in content_type:
                console.print("      🔍 Link adalah Halaman Web. Mencari MP4...")
                
                html_content = ""
                for chunk in r.iter_content(chunk_size=1024*1024):
                    html_content += chunk.decode('utf-8', errors='ignore')
                    if len(html_content) > 500000: break 

                mp4_matches = re.findall(r'(https?://[^\s"\']+\.mp4)', html_content)
                
                if mp4_matches:
                    hidden_video_url = mp4_matches[0]
                    if hidden_video_url == url: return None, None
                    
                    console.print(f"      🎉 KETEMU Link Baru: [cyan]{hidden_video_url}[/cyan]")
                    return self.download_manual(hidden_video_url, depth=depth+1)
            
            return None, None
            
        except Exception as e:
            return None, None

    def download_video(self, url):
        target_url = self.unwrap_link(url)
        
        # Opsi YT-DLP
        ydl_opts = {
            'outtmpl': os.path.join(self.folder, '%(id)s.%(ext)s'),
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'cookiesfrombrowser': ('chrome',), 
            'quiet': True, 'no_warnings': True, 'ignoreerrors': True,
            'http_headers': self.get_headers(target_url), # Header dinamis
            'check_formats': False, 
            'nocheckcertificate': True 
        }

        console.print(f"   ⬇️  [cyan]Mencoba Sedot (Engine A):[/cyan] {target_url}")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(target_url, download=True)
                if info:
                    filename = ydl.prepare_filename(info)
                    return filename, info.get('title', target_url)
        except: pass
            
        console.print("   ⚠️  [bold yellow]Engine A Gagal. Mengaktifkan Deep Scan...[/bold yellow]")
        
        if "videy.co/v?id=" in target_url:
            v_id = target_url.split("id=")[1]
            target_url = f"https://cdn.videy.co/{v_id}.mp4"
            
        return self.download_manual(target_url)