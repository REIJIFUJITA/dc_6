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
    name = db.Column(db.String(120), unique=False, nullable=False)
    wake_up_time = db.Column(db.Time, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('routines', lazy=True))
    tasks = db.relationship('Task', backref='routine', lazy=True, cascade='all, delete-orphan' )

# タスクモデル
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(120), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    song_speed = db.Column(db.String(50), nullable=True)
    song_mood = db.Column(db.String(50), nullable=True)
    routine_id = db.Column(db.Integer, db.ForeignKey('routine.id'), nullable=False)
    track_name = db.Column(db.String(120), nullable=True)  # 楽曲名
    track_url = db.Column(db.String(200), nullable=True)   # Spotify URL