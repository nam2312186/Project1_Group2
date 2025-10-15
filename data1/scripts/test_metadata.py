from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json
import pandas as pd
load_dotenv()

client_id = os.getenv("SPOTIPY_CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")


def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials"  # Removed scope parameter
    }
    result = post(url, headers=headers, data=data)
    
    # Check response status
    if result.status_code != 200:
        print(f"Error getting token: {result.status_code}")
        print(f"Response: {result.text}")
        return None
        
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token



def search_track(token, artist_name, song_name):
    # URL để search track
    url = "https://api.spotify.com/v1/search"
    
    # Headers với access token
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Tham số tìm kiếm
    query = f"track:{song_name} artist:{artist_name}"
    query_params = {
        "q": query,
        "type": "track",
        "limit": 1  # Giới hạn 1 kết quả
    }
    
    # Gửi GET request
    result = get(url, headers=headers, params=query_params)
    json_result = result.json()
    
    # Kiểm tra có kết quả không
    if len(json_result["tracks"]["items"]) == 0:
        return None
        
    # Lấy track ID từ kết quả đầu tiên
    track_id = json_result["tracks"]["items"][0]["id"]
    return track_id




def get_track_metadata(token, track_id):
    """
    Lấy metadata của một track từ Spotify API
    """
    url = f"https://api.spotify.com/v1/tracks/{track_id}"
    
    # Chuẩn hóa token (loại bỏ “Bearer ” nếu có)
    token = token.replace("Bearer ", "")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    try:
        print(f"\nĐang lấy metadata cho track ID: {track_id}")
        response = get(url, headers=headers)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            json_result = response.json()
            
            # Tránh lỗi nếu mảng artists trống hoặc album là None
            artist_name = None
            if json_result.get("artists"):
                # Nếu có nhiều nghệ sĩ, bạn có thể nối tên hoặc chọn index 0
                artist_name = json_result["artists"][0].get("name")
            
            album_info = json_result.get("album") or {}
            
            metadata = {
                "id": json_result.get("id"),
                "album_id": album_info.get("id"),
                "release_date_precision": album_info.get("release_date_precision"),
                "preview_url": json_result.get("preview_url"),
                "external_url": json_result.get("external_urls", {}).get("spotify"),
                "is_playable": json_result.get("is_playable"),
                "available_markets": json_result.get("available_markets"),
                "disc_number": json_result.get("disc_number"),
                "track_number": json_result.get("track_number"),
                "href": json_result.get("href"),
                "uri": json_result.get("uri"),
                "external_ids": json_result.get("external_ids"),  # contains isrc, etc.
                "linked_from": json_result.get("linked_from"),
                "restrictions": json_result.get("restrictions"),
            }
            
            return metadata
        else:
            # nếu không thành công, in lỗi để debug
            print(f"Lỗi: Status code {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except Exception as e:
        print(f"Lỗi khi lấy metadata: {str(e)}")
        return None
# Sửa phần gọi hàm chính để lấy token mới mỗi lần chạy
# ...existing code...



def main():
    # Lấy token mới
    token = get_token()
    if not token:
        print("Không thể lấy token. Kiểm tra client_id và client_secret")
        return
        
    print(f"Token: {token[:50]}...")

    # Thông tin bài hát cần tìm
    artist = "Olivia Rodrigo"
    song = "Can’t Catch Me Now - from The Hunger Games: The Ballad of Songbirds & Snakes"
    
    # Tìm track ID
    print(f"\nTìm kiếm bài hát: {song} - {artist}")
    track_id = search_track(token, artist, song)
    
    if track_id:
        print(f"Đã tìm thấy Track ID: {track_id}")
        
        # Lấy token mới cho audio features request
        token = get_token()
        if not token:
            print("Không thể lấy token mới cho audio features")
            return
            
        # Lấy metadata
        features = get_track_metadata(token, track_id)
        if features:
            print("\nMeta data:")
            for feature, value in features.items():
                print(f"{feature}: {value}")

            # ✅ Lưu kết quả ra file CSV
            df = pd.DataFrame([features])   # đưa dict vào DataFrame
            out_path = r"data\data-top50\track_metadata.csv"
            df.to_csv(out_path, index=False, encoding="utf-8-sig")
            print(f"\n✅ Đã lưu metadata ra file: {out_path}")

        else:
            print("Không thể lấy được metadata")
    else:
        print("Không tìm thấy bài hát")




if __name__ == "__main__":
    main()

