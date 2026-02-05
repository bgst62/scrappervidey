import os
import shutil
import subprocess
import time
import requests
from rich.console import Console

console = Console()

def ensure_chrome_ready(session_name):
    """Membuka Chrome dengan profil sesi spesifik"""
    try:
        requests.get("http://127.0.0.1:9222/json", timeout=2)
        return True
    except:
        console.print(f"[bold yellow]🚀 Membuka Chrome untuk Sesi: {session_name}...[/bold yellow]")
        
        # Deteksi Chrome di Linux/Windows
        chrome_bin = shutil.which("google-chrome") or shutil.which("google-chrome-stable") or shutil.which("chromium")
        if not chrome_bin:
            # Fallback untuk Windows default path
            chrome_bin = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            
        # Folder profil unik berdasarkan nama sesi
        profile_dir = os.path.join(os.path.expanduser("~"), ".config", "omni_hunter_sessions", session_name)
        
        cmd = [
            chrome_bin,
            "--remote-debugging-port=9222",
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "https://x.com/home"  # Langsung buka X
        ]
        
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        with console.status("[bold green]Menunggu Chrome Siap...[/bold green]"):
            time.sleep(8)
        return True