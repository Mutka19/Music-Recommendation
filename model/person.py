from repository.db_model import db


class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(32), unique=True, nullable=False)

    def __repr__(self):
        return "<User %r>" % self.username

    def validate(self, password):
        return self.password == password
