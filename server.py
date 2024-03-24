import flask
from flask import request, jsonify
import requests, json, os
from dotenv import load_dotenv, find_dotenv
import spotifyAPI as sp
from repository.db_model import db
from model.person import Person
from model.song_record import SongRecord


app = flask.Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.secret_key = os.getenv("SECRET_KEY")
db.init_app(app)

# with app.app_context():
#     db.create_all()


@app.route("/music-selection", methods=["GET", "POST"])
def find_song():
    # Get JSON data
    data = flask.request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Get data from JSON and if none is present set equal to empty string
    artist_string = data.get("artist", "")
    genre_string = data.get("genres", "")
    track_string = data.get("tracks", "")

    # Separate artist string into list using comma delimiters
    artist_list = artist_string.split(",") if len(artist_string) > 0 else []

    # Separate genres string into list using comma delimiters
    genres_list = genre_string.split(",") if len(genre_string) > 0 else []

    # Separate track string into list using comma delimiters
    track_list = track_string.split(",") if len(track_string) > 0 else []

    # Return error if too many arguments are used
    if len(artist_list) + len(genres_list) + len(track_list) > 5:
        return jsonify({"error": "Too many arguments, maximum number of arguments is 5"}), 400

    # Get recommendations using spotify recommendation api
    try:
        song = sp.get_recommendations(
            sp.request_auth(),
            artists=artist_list,
            genres=genres_list,
            tracks=track_list,
        )["tracks"][0]
    except IndexError:
        return jsonify({"error": "No tracks found"}), 404

    # Extract song name from JSON response
    song_name = song["name"]
    song_artist = song["artists"][0]["name"]

    return jsonify({"song_name": song_name, "song_artist": song_artist}), 200


@app.route("/music-database", methods=["GET", "POST"])
def music_database():
    # Get JSON data
    data = flask.request.form
    song = data.get("song_name")
    artist = data.get("song_artist")
    user = data.get("user")

    # Create artist object using form data
    liked_song = SongRecord(username=user, artist=artist, song=song)

    # Stage song
    db.session.add(liked_song)

    # Commit song to database
    db.session.commit()

    return jsonify({"Result": "Success"}), 201


app.run(debug=True)
