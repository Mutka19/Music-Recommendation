import flask
from flask import jsonify
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

# with app.app_context():
#     db.create_all()


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
        token = create_access_token(identity=username)
        return flask.jsonify({"token": token}), 200
    else:
        return flask.jsonify({"message": "Invalid username or password"}), 401


@app.route("/signup", methods=["POST"])
def signup():
    # Get data as JSON
    data = flask.request.get_json()

    # Extract username and password from JSON
    username = data.get("username")
    password = data.get("password")

    # Query for persons with matching username
    person = Person.query.filter_by(username=username).first()

    # Check if username is in use and password is not null
    if not person and len(password) > 8:
        # Create person object
        person = Person(username=username)

        # Use set_password
        person.set_password(password=password)

        # Stage person object in db and commit
        db.session.add(person)
        db.session.commit()

        return flask.jsonify({"message": "Signup Successful"}), 200
    else:
        return (
            flask.jsonify({"message": "Username is taken or password is too short"}),
            401,
        )


@app.route("/music-selection", methods=["GET", "POST"])
def find_song():
    # Get JSON data
    data = flask.request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

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
            jsonify({"error": "Too many arguments, maximum number of arguments is 5"}),
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
        return jsonify({"error": "No tracks found"}), 404

    # Extract song name from JSON response
    song_name = song["name"]
    song_artist = song["artists"][0]["name"]
    album_name = song["album"]["name"]
    release_date = song["album"]["release_date"][:4]

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


@app.route("/music-database", methods=["POST"])
@jwt_required()
def music_database():
    # Get JSON data
    data = flask.request.get_json()
    song = data.get("song_name")
    artist = data.get("song_artist")
    username = get_jwt_identity()

    # Create artist object using form data
    liked_song = SongRecord(username=username, artist=artist, song=song)

    # Stage song
    db.session.add(liked_song)

    # Commit song to database
    db.session.commit()

    return jsonify({"Result": "Success"}), 201


@app.route("/get-library", methods=["GET"])
@jwt_required()
def get_library():
    # Get user identity
    username = get_jwt_identity()

    # Query for all songs that user has saved
    songs = SongRecord.query.filter_by(username=username).all()

    # If songs are found then return all songs
    if songs:
        return jsonify({"songs": songs}), 200
    else:
        return jsonify({"error": "No songs found"})


app.run(debug=True)
