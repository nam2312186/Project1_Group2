
import os
import base64
import pandas as pd
import requests
from dotenv import load_dotenv
import time

# Load client_id và client_secret từ file .env
load_dotenv()
CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

def get_token():
	auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
	auth_bytes = auth_string.encode("utf-8")
	auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

	url = "https://accounts.spotify.com/api/token"
	headers = {"Authorization": "Basic " + auth_base64,
			   "Content-Type": "application/x-www-form-urlencoded"}
	data = {"grant_type": "client_credentials"}

	result = requests.post(url, headers=headers, data=data)
	if result.status_code != 200:
		print("❌ Error getting token:", result.status_code, result.text)
		return None
	return result.json()["access_token"]

# Example function to get track info by track_id
def get_track_metadata(token, track_id):
	url = f"https://api.spotify.com/v1/tracks/{track_id}"
	headers = {"Authorization": f"Bearer {token}"}
	resp = requests.get(url, headers=headers)
	if resp.status_code != 200:
		print(f"❌ Metadata lỗi {track_id}: {resp.status_code}")
		return None
	return resp.json()

# Example main logic (update as needed for your batch process)
def update_artist_names(input_csv, output_csv):
	df = pd.read_csv(input_csv, encoding="utf-8-sig")
	token = get_token()
	if not token:
		print("❌ Không lấy được token Spotify")
		return
	for idx, row in df.iterrows():
		track_id = row.get("track_id")
		if not track_id or pd.isna(track_id):
			print(f"{idx+1}. ⚠️ Không có track_id")
			continue
		meta = get_track_metadata(token, track_id)
		if meta:
			df.at[idx, "song"] = meta.get("name")
			df.at[idx, "artist"] = ", ".join([a["name"] for a in meta.get("artists", [])])
			print(f"{idx+1}. ✅ {track_id} → {df.at[idx, 'song']} / {df.at[idx, 'artist']}")
		else:
			print(f"{idx+1}. ❌ Không lấy được metadata cho {track_id}")
		time.sleep(0.1)  # avoid rate limit
	df.to_csv(output_csv, index=False, encoding="utf-8-sig")
	print(f"\n✅ Đã lưu kết quả cập nhật vào {output_csv}")

if __name__ == '__main__':
    # Danh sách các nước
    countries = [
        'argentina', 'france', 'italy', 'japan', 'mexico',
        'south-korea', 'spain', 'uk', 'usa', 'world'
    ]
    base_dir = 'data/data-top50'
    for country in countries:
        input_path = os.path.abspath(os.path.join(base_dir, country,f'encoded_song_or_artist_rows_{country}.csv'))
        output_path = os.path.abspath(os.path.join(base_dir, country,f'spotify_streaming_top_50_fixed_{country}.csv'))
        print(f"Checking: {input_path}")
        if os.path.isfile(input_path):
            update_artist_names(input_csv=input_path, output_csv=output_path)
        else:
            print(f'File not found: {input_path}')
