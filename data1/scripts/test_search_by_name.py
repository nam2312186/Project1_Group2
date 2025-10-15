import os
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

# Load biến môi trường
load_dotenv()

client_id = os.getenv("SPOTIPY_CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

# Setup client
sp = Spotify(auth_manager=SpotifyClientCredentials(
    client_id=client_id,
    client_secret=client_secret
))

def test_search(song_name):
    results = sp.search(q=f"track:{song_name}", type="track", limit=1)
    items = results["tracks"]["items"]
    if not items:
        print("❌ Không tìm thấy bài hát")
        return

    track = items[0]
    print("✅ Tìm thấy track:")
    print("Track ID:", track["id"])
    print("Name:", track["name"])
    print("Artist:", ", ".join([a["name"] for a in track["artists"]]))
    print("Album:", track["album"]["name"])
    print("Release date:", track["album"]["release_date"])
    print("External URL:", track["external_urls"]["spotify"])

if __name__ == "__main__":
    # Test với 1 bài hát
    test_search("Seven (feat. Latto) (Explicit Ver.)")
