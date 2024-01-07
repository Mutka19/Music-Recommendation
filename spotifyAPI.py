import requests as rq
import json
import os
import base64
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")


def request_auth():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    params = {"grant_type": "client_credentials"}
    res = rq.post(url, headers=headers, data=params)
    json_res = json.loads(res.content)
    token = json_res["access_token"]
    return token


def get_header(token):
    return {"Authorization": "Bearer " + token}


def search_artist(token, name):
    url = "https://api.spotify.com/v1/search"
    headers = get_header(token)
    query = f"?q={name}&type=artist&limit=1"
    query_url = url + query

    res = rq.get(query_url, headers=headers)
    json_res = json.loads(res.content)["artists"]["items"]
    if len(json_res) == 0:
        return None
    else:
        return json_res[0]


def search_song(token, song_title):
    url = "https://api.spotify.com/v1/search"
    headers = get_header(token)
    query = f"?q={song_title}&type=track&limit=1"
    query_url = url + query

    res = rq.get(query_url, headers=headers)
    json_res = json.loads(res.content)["tracks"]["items"]
    if len(json_res) == 0:
        return None
    else:
        return json_res[0]


def search_album(token, album_title):
    url = "https://api.spotify.com/v1/search"
    headers = get_header(token)
    query = f"?q={album_title}&type=album&limit=1"
    query_url = url + query

    res = rq.get(query_url, headers=headers)
    json_res = json.loads(res.content)["albums"]["items"]
    if len(json_res) == 0:
        return None
    else:
        return json_res[0]


def getSongArt(token, song_title):
    song_json = search_song(token, song_title)
    return song_json["album"]["images"][0]["url"]


def get_recommendations(
    token, limit=1, artists=["None"], genres=["None"], tracks=["None"]
):
    genres_string = ",".join(genres)
    artists_string = ",".join([search_artist(token, i)["id"] for i in artists])
    tracks_string = ",".join([search_song(token, i)["id"] for i in tracks])

    url = "https://api.spotify.com/v1/recommendations"
    headers = get_header(token)
    query = f"?limit={limit}&market=ES&seed_artists={artists_string}&seed_genres={genres_string}&seed_tracks={tracks_string}"
    query_url = url + query

    res = rq.get(query_url, headers=headers)
    json_res = json.loads(res.content)
    if len(json_res) == 0:
        return None
    else:
        return json_res
