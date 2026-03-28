import sys
import json
import re
import os
import requests
from dotenv import load_dotenv

def get_playlist_id(url):
    match = re.search(r'[?&]list=([a-zA-Z0-9_-]+)', url)
    if not match:
        print("Xato: URL dan playlist ID topilmadi", file=sys.stderr)
        sys.exit(1)
    return match.group(1)

def fetch_playlist(api_key, playlist_id):
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "snippet",
        "playlistId": playlist_id,
        "maxResults": 150,
        "key": api_key,
    }

    items = []
    while True:
        r = requests.get(url, params=params)
        data = r.json()

        if "error" in data:
            print(f"YouTube API xatosi: {data['error']['message']}", file=sys.stderr)
            sys.exit(1)

        items.extend(data.get("items", []))

        if "nextPageToken" not in data:
            break
        params["pageToken"] = data["nextPageToken"]

    return [
        {
            "title": item["snippet"]["title"],
            "video_id": item["snippet"]["resourceId"]["videoId"],
            "position": item["snippet"]["position"],
        }
        for item in items
    ]

def main():
    if len(sys.argv) != 2:
        print("Ishlatish: python fetcher.py <playlist_url>", file=sys.stderr)
        sys.exit(1)

    # fetcher.py -> playlist-fetcher/ -> main-site/ -> project root
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base_dir, ".env")
    load_dotenv(env_path)

    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        print(f"Xato: YOUTUBE_API_KEY topilmadi ({env_path})", file=sys.stderr)
        sys.exit(1)

    playlist_url = sys.argv[1]
    playlist_id = get_playlist_id(playlist_url)
    results = fetch_playlist(api_key, playlist_id)
    # print(json.dumps(results, ensure_ascii=False, indent=2))
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved: {output_path}", file=sys.stderr)

if __name__ == "__main__":
    main()