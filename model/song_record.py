import uuid
from sqlalchemy.dialects.postgresql import UUID
from repository.db_model import db


class SongRecord(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artist = db.Column(db.String(300), unique=False, nullable=False)
    song = db.Column(db.String(300), unique=False, nullable=False)
    album = db.Column(db.String(300), unique=False)
    release_date = db.Column(db.DateTime, unique=False)
    person_id = db.Column(UUID(as_uuid=True), db.ForeignKey("person.id"), nullable=False)

    def to_library_json(self):
        return {
            "id": self.id,
            "songName": self.song,
            "artist": self.artist,
            "album": self.album,
            "releaseDate": self.release_date
        }
