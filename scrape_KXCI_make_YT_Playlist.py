import requests
from bs4 import BeautifulSoup
import json
import html
import time
import tqdm
from ytmusicapi import YTMusic

# =====================
# CONFIG
# =====================
SPINITRON_URL = "https://spinitron.com/KXCI/pl/21316602/Global-Rhythm-Radio?sp=426349426"
MAX_RETRIES = 4
DELAY = 10  # seconds

# Initialize YouTube Music with your auth headers (already generated)
yt = YTMusic("browser.json")

# Fetch existing playlists once
existing_playlists = {pl['title']: pl['playlistId'] for pl in yt.get_library_playlists()}
print(f"Existing playlists: {existing_playlists}")
delay = DELAY

# =====================
# FUNCTIONS
# =====================

def scrape_spinitron(url):
    """Scrape tracklist from a Spinitron playlist page."""
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    tracks = []
    for row in soup.select("tr.spin-item"):
        data_spin = row.get("data-spin")
        if data_spin:
            data_spin = html.unescape(data_spin)
            try:
                info = json.loads(data_spin)
                artist = info.get("a")
                title = info.get("s")
                release = info.get("r")
                if artist and title:
                    tracks.append({"artist": artist, "track": title, "release": release})
            except Exception as e:
                print("Error parsing row:", e)
    return tracks

def get_or_create_playlist(name):
    if name in existing_playlists:
        return existing_playlists[name]
    playlist_id = yt.create_playlist(name, name + " description")
    existing_playlists[name] = playlist_id
    return playlist_id

def add_tracks_to_youtube(playlist_id, tracks):
    global delay
    for entry in tqdm.tqdm(tracks):
        time.sleep(1)  # avoid hammering the API
        track = entry["track"]
        artist = entry["artist"]
        search_query = f"{track} {artist}"
        search_results = yt.search(search_query)

        retries = 0
        success = False

        while retries < MAX_RETRIES and not success:
            try:
                if search_results:
                    song_id = None
                    for result in search_results:
                        if "videoId" in result:
                            song_id = result["videoId"]
                            break

                    if song_id:
                        print(f"Adding '{track}' by {artist}...")
                        yt.add_playlist_items(playlist_id, [song_id])
                        success = True
                    else:
                        print(f"No valid videoId found for '{track}' by {artist}.")
                        success = True
                else:
                    print(f"Couldn't find '{track}' by {artist} in the search results.")
                    success = True

            except Exception as e:
                if "HTTP 400" in str(e) or "HTTP 429" in str(e):
                    print(f"Rate limit error for '{track}' by {artist}. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay *= 2
                    retries += 1
                else:
                    print(f"Error adding '{track}' by {artist}: {e}")
                    retries = MAX_RETRIES

        delay = DELAY  # reset delay

# =====================
# MAIN
# =====================

if __name__ == "__main__":
    # Step 1: Scrape playlist
    tracks = scrape_spinitron(SPINITRON_URL)
    print(f"Scraped {len(tracks)} tracks from Spinitron")

    # Step 2: Create or reuse YT Music playlist
    playlist_name = f"Global Rhythm Radio {time.strftime('%Y-%m-%d')}"
    playlist_id = get_or_create_playlist(playlist_name)

    # Step 3: Add tracks to YT Music
    add_tracks_to_youtube(playlist_id, tracks)

    print("Done!")