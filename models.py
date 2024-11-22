from flask_sqlalchemy import SQLAlchemy

# SQLAlchemyのインスタンス
db = SQLAlchemy()

# ユーザーモデル
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)

# ルーティンモデル
class Routine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    routine_name = db.Column(db.String(120), unique=True, nullable=False)
    wake_up_time = db.Column(db.Time, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationship with User
    user = db.relationship('User', backref=db.backref('routines', lazy=True))
    