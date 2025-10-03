import requests
from bs4 import BeautifulSoup
import json
import html

url = "https://spinitron.com/KXCI/pl/21316602/Global-Rhythm-Radio?sp=426349426"

resp = requests.get(url)
soup = BeautifulSoup(resp.text, "html.parser")

tracks = []

for row in soup.select("tr.spin-item"):
    data_spin = row.get("data-spin")
    if data_spin:
        # unescape HTML entities (&quot; → ")
        data_spin = html.unescape(data_spin)
        try:
            info = json.loads(data_spin)
            artist = info.get("a")
            title = info.get("s")
            release = info.get("r")
            tracks.append({
                "artist": artist,
                "track": title,
                "release": release
            })
        except Exception as e:
            print("Error parsing row:", e)

print(f"Found {len(tracks)} tracks")
for t in tracks:
    print(f"{t['artist']} – {t['track']} ({t['release']})")
