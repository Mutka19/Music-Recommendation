import flask
from flask import jsonify
from datetime import datetime, timedelta
import os
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
import spotify_api_handler as sp
from repository.db_model import db
from model.person import Person
from model.song_record import SongRecord


app = flask.Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.secret_key = os.getenv("SECRET_KEY")
app.config["JWT_SECRET_KEY"] = os.getenv("SECRET_KEY")
db.init_app(app)
jwt = JWTManager(app)


@app.route("/login", methods=["POST"])
def login():
    # Get data as JSON
    data = flask.request.get_json()

    # Extract username and password from JSON
    username = data.get("username")
    password = data.get("password")

    # Query for persons with matching username
    person = Person.query.filter_by(username=username).first()
    # Check if username and password match
    if person and person.check_password(password):
        expires_in = timedelta(minutes=30)
        token = create_access_token(identity=person.id, expires_delta=expires_in)
        return flask.jsonify({"token": token, "expiration": int(expires_in.total_seconds())}), 200
    else:
        return flask.jsonify({"message": "Invalid username or password"}), 401


@app.route("/signup", methods=["POST"])
def signup():
    # Get data as JSON
    data = flask.request.get_json()

    # Extract username and password from JSON
    username = data.get("username")
    password = data.get("password")

    if len(username) < 1:
        return jsonify({"message": "Username is required"}), 400

    # Query for persons with matching username
    person = Person.query.filter(Person.username == username).first()

    # Check if username is in use and password is not null
    if not person and len(password) > 8:
        # Create person object
        person = Person(username=username)

        # Use set_password
        person.set_password(password=password)

        # Stage person object in db and commit
        db.session.add(person)
        db.session.commit()

        return jsonify({"message": "Signup Successful"}), 200
    elif person:
        return jsonify({"message": "Username already taken"}), 400
    else:
        return jsonify({"message": "Password is too short"}), 400


@app.route("/change-password", methods=["PUT"])
@jwt_required()
def change_password():
    # Get user identity
    person_id = get_jwt_identity()

    # Get JSON data
    data = flask.request.get_json()

    try:
        # Query for user
        person = Person.query.filter(Person.id == person_id).first()
    except Exception:
        return jsonify({"message": "Could not find user in database"}), 404

    # Extract password and new password from data
    old_password = data.get("oldPassword")
    new_password = data.get("newPassword")

    # Check if entered password matches old password
    if person.check_password(old_password) and len(new_password) > 8:
        person.set_password(new_password)
        db.session.commit()
        return jsonify({"message": "Password updated successfully"}), 201
    elif len(new_password) < 8:
        return jsonify({"message": "New password length too short"}), 400
    else:
        return jsonify({"message": "Old password is incorrect"}), 401


@app.route("/verify", methods=["GET"])
@jwt_required()
def verify():
    # Get user identity
    person_id = get_jwt_identity()

    # Query for person in database
    person = Person.query.filter(Person.id == person_id).first()

    if not person:
        return jsonify({"message": "Could not verify user"}), 404
    else:
        return jsonify({"message": "Verified"}), 200


@app.route("/music-selection", methods=["GET", "POST"])
def find_song():
    # Get JSON data
    data = flask.request.get_json()

    if not data:
        return jsonify({"message": "No data provided"}), 400

    # Get data from JSON and if none is present set equal to empty string
    artist_string = data.get("artists", "")
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
        return (
            jsonify({"message": "Too many arguments, maximum number of arguments is 5"}),
            400,
        )

    # Get recommendations using spotify recommendation api
    try:
        song = sp.get_recommendations(
            sp.request_auth(),
            artists=artist_list,
            genres=genres_list,
            tracks=track_list,
        )["tracks"][0]
    except IndexError:
        return jsonify({"message": "No tracks found"}), 404

    # Extract song name from JSON response
    song_name = song["name"]
    song_artist = song["artists"][0]["name"]
    album_name = song["album"]["name"]
    release_date = song["album"]["release_date"]

    return (
        jsonify(
            {
                "songName": song_name,
                "songArtist": song_artist,
                "albumName": album_name,
                "releaseDate": release_date,
            }
        ),
        200,
    )


@app.route("/save-music", methods=["POST"])
@jwt_required()
def music_database():
    # Get JSON data
    data = flask.request.get_json()
    song = data.get("songName")
    artist = data.get("songArtist")
    album = data.get("albumName")
    release_date = data.get("releaseDate")

    # Get username from JWT
    person_id = get_jwt_identity()

    # Query for person in database
    person = Person.query.filter(Person.id == person_id).first()

    if not person:
        return jsonify({"result", "User not found"})

    time_stamp = datetime.strptime(release_date[:4], "%Y").date()

    # Create artist object using form data
    liked_song = SongRecord(artist=artist, song=song, album=album, release_date=time_stamp, person_id=person.id)

    # Stage song
    db.session.add(liked_song)

    # Commit song to database
    db.session.commit()

    return jsonify({"message": "Music saved to database"}), 201


@app.route("/delete-song", methods=["DELETE"])
@jwt_required()
def delete_song():
    # Get data from request
    data = flask.request.get_json()
    song_id = data.get("songId")

    # Query for song in database
    try:
        song_record = SongRecord.query.filter(SongRecord.id == song_id).first()
    except Exception:
        return jsonify({"Error": "Song not found"}), 404

    # Delete song from database
    db.session.delete(song_record)
    db.session.commit()

    return jsonify({"message": "Song deleted from library"}), 204


@app.route("/get-library", methods=["POST"])
@jwt_required()
def get_library():
    # Get user identity
    person_id = get_jwt_identity()

    # Get page being requested by front end
    data = flask.request.get_json()
    page = data.get("page")

    # Query for all songs that user has saved
    pagination = SongRecord.query.filter_by(person_id=person_id).paginate(page=page, per_page=5, error_out=False)
    songs = pagination.items

    songs_json = [song.to_library_json() for song in songs]

    # If songs are found then return all songs
    if songs:
        return jsonify({"songs": songs_json, "pages": pagination.pages}), 200
    else:
        return jsonify({"message": "No songs found"}), 404


app.run(host="0.0.0.0", port=5000, debug=True)
