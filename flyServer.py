import flask
from flask import request
import requests, json, os
from dotenv import load_dotenv, find_dotenv
from random import randrange
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exists
import spotifyAPI as sp
from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    login_required,
    logout_user,
)


app = flask.Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.secret_key = os.getenv("SECRET_KEY")
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class Person(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(32), unique=True, nullable=False)

    def __repr__(self):
        return "<User %r>" % self.username

    def validate(self, password):
        return self.password == password


class Artist(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=False, nullable=False)
    artist = db.Column(db.String(300), unique=False, nullable=False)
    song = db.Column(db.String(300), unique=False, nullable=False)

# with app.app_context():
#     db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return Person.query.get(int(user_id))
@app.route("/")
def main():
    if "username" in flask.session and flask.session["username"] is None:
        return flask.redirect("/signup")
    else:
        return flask.redirect("/main")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if flask.request.method == "POST":
        username = flask.request.form["username"]
        password = flask.request.form["password"]

        if Person.query.filter_by(username=username).first():
            error_message = (
                "This username already exists, please choose a different username!"
            )
            return flask.render_template("signup.html", error_message=error_message)

        new_user = Person(username=username, password=password)

        db.session.add(new_user)
        db.session.commit()
        return flask.redirect("/login")
    else:
        return flask.render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if flask.request.method == "POST":
        username = flask.request.form["username"]
        password = flask.request.form["password"]
        print(username, password)

        user = Person.query.filter_by(username=username).first()
        if user is not None and user.validate(password):
            flask.session["user_id"] = user.id
            flask.session["username"] = username
            login_user(user)
            return flask.redirect(flask.url_for("send_to_main"))
        else:
            error_message = "Invalid username or password"
            return flask.render_template("login.html", error_message=error_message)

    # Render login page
    return flask.render_template("login.html")

@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    flask.session.pop("user_id", None)
    flask.session.pop("username", None)
    flask.flash("Signed out")
    return flask.redirect(flask.url_for("login"))


@app.route("/main", methods=["GET"])
@login_required
def send_to_main():
    a = Artist.query.all()

    song_name = request.args.get("song_name")

    song_artist = request.args.get("song_artist")

    return flask.render_template(
        "main.html", user=flask.session["username"], song_lists=a, song=song_name, artist=song_artist
    )


@app.route("/music-selection", methods=["GET", "POST"])
def find_song():
    form_data = flask.request.form
    artist = form_data["artist"]
    artist_list = [artist]
    genres = form_data["genres"]
    genres_list = [genres]
    track = form_data["track"]
    track_list = [track]
    user = form_data["user"]

    song = sp.get_recommendations(
        sp.request_auth(), artists=artist_list, genres=genres_list, tracks=track_list
    )["tracks"][0]

    song_name = song["name"]
    song_artist = song["artists"][0]["name"]

    return flask.redirect(
        flask.url_for(
            "send_to_main", user=user, song_name=song_name, song_artist=song_artist
        )
    )  # sent to login to test


@app.route("/music-database", methods=["GET", "POST"])
def music_database():
    form_data = flask.request.form
    song = form_data["song_name"]
    artist = form_data["song_artist"]
    user = form_data["user"]
    artist_found = Artist(username=user, artist=artist, song=song)

    db.session.add(artist_found)

    db.session.commit()
    return flask.redirect(flask.url_for("send_to_main", user=user))

app.run(debug=True)
