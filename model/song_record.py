from repository.db_model import db


class SongRecord(db.Model):
    id = db.Column(db.uuid, primary_key=True)
    username = db.Column(db.String(80), unique=False, nullable=False)
    artist = db.Column(db.String(300), unique=False, nullable=False)
    song = db.Column(db.String(300), unique=False, nullable=False)