import requests
import re
import os
import time

class VideyAggregator:
    def __init__(self):
        # Header Mobile biasanya lebih jarang kena blokir 403
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Accept': 'application/json',
            'Referer': 'https://www.google.com/'
        }
        self.folder = "videy_panen_raya"
        
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)

    def extract_id(self, url):
        patterns = [
            r'id=([a-zA-Z0-9]+)',
            r'videy\.co/v\?id=([a-zA-Z0-9]+)',
            r'cdn\.videy\.co/([a-zA-Z0-9]+)',
            r'videyk\.com/set/\?id=([a-zA-Z0-9]+)'
        ]
        for p in patterns:
            match = re.search(p, url)
            if match: return match.group(1)
        return None

    def scan_reddit_global_pro(self, limit=100):
        print(f"📡 Mencari Video Terbaru (Taktik Siluman)...")
        # Menggunakan old.reddit seringkali lebih ampuh tembus 403
        url = "https://old.reddit.com/search.json"
        params = {
            'q': "site:videy.co OR site:videyk.com",
            'sort': 'new',
            'limit': limit,
            't': 'day' 
        }

        try:
            session = requests.Session()
            res = session.get(url, headers=self.headers, params=params, timeout=15)
            
            if res.status_code != 200:
                print(f"⚠️ Gagal akses. Code: {res.status_code}")
                return []

            data = res.json()
            posts = data.get('data', {}).get('children', [])
            tasks = []

            for post in posts:
                p_data = post['data']
                text_to_scan = f"{p_data.get('url', '')} {p_data.get('selftext', '')} {p_data.get('title', '')}"
                
                links = re.findall(r'https?://(?:www\.)?(?:videy\.co|videyk\.com)[^\s<>"]+', text_to_scan)
                for link in links:
                    v_id = self.extract_id(link)
                    if v_id:
                        tasks.append((v_id, f"https://cdn.videy.co/{v_id}.mp4"))
            
            return list(set(tasks))
        except Exception as e:
            print(f"❌ Error saat scan: {e}")
            return []

    def download(self, tasks):
        if not tasks:
            print("😭 Zonk! Tidak ditemukan video baru.")
            return

        print(f"\n📥 Memulai Sedotan Dewa: {len(tasks)} target...")
        total_berhasil = 0
        
        for i, (v_id, url) in enumerate(tasks):
            filename = os.path.join(self.folder, f"{v_id}.mp4")
            
            if os.path.exists(filename):
                continue 
            
            print(f"⬇️  [{total_berhasil+1}] Sedot: {v_id}")
            
            try:
                dl_headers = {
                    'User-Agent': self.headers['User-Agent'],
                    'Referer': 'https://videy.co/'
                }
                with requests.get(url, stream=True, headers=dl_headers, timeout=15) as r:
                    if r.status_code == 200:
                        with open(filename, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=1024*1024):
                                f.write(chunk)
                        total_berhasil += 1
                    else:
                        print(f"   ❌ File {v_id} mati (404).")
            except Exception:
                print(f"   ⚠️ Koneksi putus: {v_id}")

        print(f"\n✨ Selesai! Berhasil ambil {total_berhasil} video baru.")

if __name__ == "__main__":
    bot = VideyAggregator()
    links = bot.scan_reddit_global_pro(limit=100)
    bot.download(links)