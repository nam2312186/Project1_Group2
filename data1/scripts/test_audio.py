import requests

BASE_URL = "https://api.reccobeats.com/v1"

def get_audio_features(recco_id: str):
    """Lấy audio features bằng ReccoBeats ID"""
    url = f"{BASE_URL}/audio-features?ids={recco_id}"
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"❌ Error {resp.status_code} when fetching audio features for {recco_id}")
        return None


spotify_id =  "73Yi5M3WRdNEUjumZip3LI"


if spotify_id:
    print("✅ ReccoBeats ID:", spotify_id)
    features = get_audio_features(spotify_id)
    if features:
        print("🎵 Audio Features:", features)
else:
    print("❌ Không tìm thấy ReccoBeats ID")
