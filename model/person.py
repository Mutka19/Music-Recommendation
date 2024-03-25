import uuid
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import generate_password_hash, check_password_hash
from repository.db_model import db


class Person(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4())
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(32), unique=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
