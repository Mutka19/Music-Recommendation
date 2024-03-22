import uuid
from sqlalchemy.dialects.postgresql import UUID
from repository.db_model import db


class Person(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4())
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(32), unique=True, nullable=False)
