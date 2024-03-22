import uuid
from sqlalchemy.dialects.postgresql import UUID
from repository.db_model import db


class SongRecord(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4())
    username = db.Column(db.String(80), unique=False, nullable=False)
    artist = db.Column(db.String(300), unique=False, nullable=False)
    song = db.Column(db.String(300), unique=False, nullable=False)
