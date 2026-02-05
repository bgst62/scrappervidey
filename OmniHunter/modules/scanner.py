import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from rich.console import Console

console = Console()

class OmniScanner:
    def __init__(self):
        opts = Options()
        opts.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

    def scan_page(self, keyword, scroll_count=3):
        all_links = set()
        
        # Jika keyword kosong, asumsi user sudah di halaman yang tepat (misal Home/Bookmarks)
        if keyword.strip():
            console.print(f"[bold cyan]🔍 Membuka Search: {keyword}[/bold cyan]")
            self.driver.get(f"https://x.com/search?q={keyword}&f=live")
            time.sleep(5)
        else:
            console.print(f"[bold cyan]🔍 Scanning Halaman Saat Ini...[/bold cyan]")

        with console.status("[bold yellow]Mode Brutal: Menyedot Semua Link...[/bold yellow]") as status:
            for i in range(scroll_count):
                # STRATEGI BARU: Ambil properti 'href' dari semua tag <a>
                # Ini jauh lebih ampuh daripada baca teks tweet
                elements = self.driver.find_elements(By.TAG_NAME, "a")
                
                found_in_loop = 0
                for el in elements:
                    try:
                        href = el.get_attribute("href")
                        if href:
                            # Filter: Kita cuma mau link eksternal (t.co) atau link video langsung
                            # Kita abaikan link ke profil user (x.com/username) atau hashtag
                            if "t.co/" in href or "videy.co" in href or "youtube.com" in href or "tiktok.com" in href:
                                if href not in all_links:
                                    all_links.add(href)
                                    found_in_loop += 1
                    except:
                        # Kadang elemen hilang pas discroll (StaleElement), abaikan aja
                        continue
                
                console.print(f"   └── 🔄 Putaran {i+1}: Menyedot {found_in_loop} link mentah.")
                
                # Scroll ke bawah
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(4)
            
        return list(all_links)