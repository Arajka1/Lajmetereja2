from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class VisitorStats(db.Model):
    __tablename__ = "visitor_stats"

    id = db.Column(db.Integer, primary_key=True)
    device = db.Column(db.String(200), nullable=True)
    browser = db.Column(db.String(200), nullable=True)
    timezone = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(200), nullable=True)
