from flask import Flask, jsonify, request, redirect, url_for, session, render_template, flash, g
from models import db, User ,Routine,Task
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from datetime import datetime
import os

# Flask アプリの初期化
app = Flask(__name__)
app.secret_key = "your_secret_key"

# データベースの設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Google API の設定
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # HTTP を許可
CLIENT_SECRETS_FILE = "client_id.json"
SCOPES = ["https://www.googleapis.com/auth/userinfo.email", 
          "https://www.googleapis.com/auth/userinfo.profile", 
          "openid"]

@app.route("/")
def index():
    if g.current_user: #　ログイン済みのユーザーがいる場合
        return redirect(url_for('profile')) # プロフィール画面にリダイレクト
    return render_template("index.html") #　ログインしていない場合のトップページ

@app.route("/login")
def login():
    # Google 認証のフローを作成
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri="http://127.0.0.1:5000/callback"
    )
    auth_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(auth_url)

@app.route("/callback")
def callback():
    try:
        # Google 認証のフローを取得
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            state=session["state"],
            redirect_uri="http://127.0.0.1:5000/callback"
        )
        # 認証コードを交換してトークンを取得
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials

        # Google API を使用してユーザー情報を取得
        service = build("oauth2", "v2", credentials=credentials)
        userinfo = service.userinfo().get().execute()

        # ユーザー情報をデータベースに保存
        email = userinfo["email"]
        name = userinfo["name"]

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, name=name)
            db.session.add(user)
            db.session.commit()

        session["user_email"] = email #ユーザーをセッションに保存

        return redirect(url_for('profile'))
    except Exception as e:
        print("Error:", e)  # エラーメッセージを出力
        return "認証に失敗しました。"
    
#現在のユーザーを取得する関数
@app.before_request
def load_logged_in_user():
    user_email = session.get('user_email')
    if user_email is None:
        g.current_user = None
    else:
        g.current_user = User.query.filter_by(email=user_email).first()

# プロフィール画面
@app.route("/profile", methods=["GET"])
def profile():
    if g.current_user is None:
        flash('ログインが必要です', 'error')
        return redirect(url_for('login'))
    
    # 現在のユーザーのルーティーンを取得
    routines = Routine.query.filter_by(user_id=g.current_user.id).all()
    return render_template('profile.html', name=g.current_user.name, email=g.current_user.email, routines=routines)

    
# ルーティーン作成フォームの表示
@app.route('/routines/new',methods=['GET'])
def new_routine():
    users = User.query.all()
    return render_template('new_routine.html',users=users)

# ルーティーン作成処理
@app.route('/routines', methods=['POST'])
def create_routine_from_form():
    if g.current_user is None:
        flash('ログインが必要です', 'error')
        return redirect(url_for('login'))
    
    name = request.form.get('name')
    wake_up_time = request.form.get('wake_up_time')
    is_active = request.form.get('is_active') == 'on'
    user_id = g.current_user.id

    if not name or not wake_up_time:
        flash('すべてのフィールドを入力してください', 'error')
        return redirect(url_for('new_routine'))
    
    try:
        wake_up_time = datetime.strptime(wake_up_time, "%H:%M").time()
        routine = Routine(name=name, wake_up_time=wake_up_time, is_active=is_active, user_id=user_id)
        db.session.add(routine)
        db.session.commit()
        flash('ルーティーンが正常に作成されました', 'success')
        return redirect(url_for('profile'))
    except Exception as e:
        flash(f'エラーが発生しました: {e}', 'error')
        return redirect(url_for('new_routine'))


#　ルーティーンの一覧表示
@app.route('/routines/display_routines', methods=['GET'])
def display_routines():
    if g.current_user is None:
        flash('ログインが必要です', 'error')
        return redirect(url_for('login'))

    # 現在ログインしているユーザーのルーティーンのみを取得
    routines = Routine.query.filter_by(user_id=g.current_user.id).all()
    return render_template('display_routines.html', routines=routines)

# ルーティーンの編集処理
@app.route('/routines/edit/<int:routine_id>', methods=['GET', 'POST'])
def edit_routine(routine_id):
    routine = Routine.query.get_or_404(routine_id)
    if routine.user_id != g.current_user.id:
        flash('権限がありません', 'error')
        return redirect(url_for('profile'))

    if request.method == 'POST':
        routine.name = request.form.get('name')
        wake_up_time = request.form.get('wake_up_time')
        routine.is_active = request.form.get('is_active') == 'on'

        if not routine.name or not wake_up_time:
            flash('すべてのフィールドを入力してください', 'error')
            return redirect(url_for('edit_routine', routine_id=routine.id))

        try:
            routine.wake_up_time = datetime.strptime(wake_up_time, "%H:%M").time()
            db.session.commit()
            flash('ルーティーンが正常に更新されました', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            flash(f'エラーが発生しました: {e}', 'error')
            return redirect(url_for('edit_routine', routine_id=routine.id))
    
    return render_template('edit_routine.html', routine=routine)


#　ルーティーンの削除処理
@app.route('/routines/delete/<int:routine_id>', methods=['POST'])
def delete_routine(routine_id):
    routine = Routine.query.get_or_404(routine_id)
    if routine.user_id != g.current_user.id:
        flash('権限がありません', 'error')
        return redirect(url_for('display_routines'))

    try:
        db.session.delete(routine)
        db.session.commit()
        flash('ルーティーンが正常に削除されました', 'success')
        return redirect(url_for('display_routines'))
    except Exception as e:
        flash(f'エラーが発生しました: {e}', 'error')
        return redirect(url_for('display_routines'))

@app.route('/tasks/new/<int:routine_id>', methods=['GET'])
def new_task(routine_id):
    routine = Routine.query.get_or_404(routine_id)
    return render_template('new_task.html', routine=routine)

@app.route('/tasks', methods=['POST'])
def create_task():
    if g.current_user is None:
        flash('ログインが必要です', 'error')
        return redirect(url_for('login'))

    task_name = request.form.get('task_name')
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')
    song_speed = request.form.get('song_speed')
    song_mood = request.form.get('song_mood')
    routine_id = request.form.get('routine_id')

    if not task_name or not start_time or not end_time:
        flash('すべてのフィールドを入力してください', 'error')
        return redirect(url_for('new_task', routine_id=routine_id))

    try:
        start_time = datetime.strptime(start_time, "%H:%M").time()
        end_time = datetime.strptime(end_time, "%H:%M").time()

        task = Task(
            task_name=task_name,
            start_time=start_time,
            end_time=end_time,
            song_speed=song_speed,
            song_mood=song_mood,
            routine_id=routine_id
        )
        db.session.add(task)
        db.session.commit()
        flash('タスクが正常に作成されました', 'success')
        return redirect(url_for('display_tasks', routine_id=routine_id))
    except Exception as e:
        flash(f'エラーが発生しました: {e}', 'error')
        return redirect(url_for('new_task', routine_id=routine_id))

@app.route('/tasks/<int:routine_id>', methods=['GET'])
def display_tasks(routine_id):
    routine = Routine.query.get_or_404(routine_id)
    if routine.user_id != g.current_user.id:
        flash('権限がありません', 'error')
        return redirect(url_for('display_routines'))

    tasks = Task.query.filter_by(routine_id=routine_id).all()
    return render_template('display_tasks.html', routine=routine, tasks=tasks)

@app.route('/tasks/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    routine = Routine.query.get_or_404(task.routine_id)
    if routine.user_id != g.current_user.id:
        flash('権限がありません', 'error')
        return redirect(url_for('display_tasks', routine_id=task.routine_id))

    if request.method == 'POST':
        task.task_name = request.form.get('task_name')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        task.song_speed = request.form.get('song_speed')
        task.song_mood = request.form.get('song_mood')

        if not task.task_name or not start_time or not end_time:
            flash('すべてのフィールドを入力してください', 'error')
            return redirect(url_for('edit_task', task_id=task.id))

        try:
            task.start_time = datetime.strptime(start_time, "%H:%M").time()
            task.end_time = datetime.strptime(end_time, "%H:%M").time()
            db.session.commit()
            flash('タスクが正常に更新されました', 'success')
            return redirect(url_for('display_tasks', routine_id=task.routine_id))
        except Exception as e:
            flash(f'エラーが発生しました: {e}', 'error')
            return redirect(url_for('edit_task', task_id=task.id))

    return render_template('edit_task.html', task=task)

@app.route('/tasks/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    routine = Routine.query.get_or_404(task.routine_id)
    if routine.user_id != g.current_user.id:
        flash('権限がありません', 'error')
        return redirect(url_for('display_tasks', routine_id=task.routine_id))

    try:
        db.session.delete(task)
        db.session.commit()
        flash('タスクが正常に削除されました', 'success')
        return redirect(url_for('display_tasks', routine_id=task.routine_id))
    except Exception as e:
        flash(f'エラーが発生しました: {e}', 'error')
        return redirect(url_for('display_tasks', routine_id=task.routine_id))


# 初回実行時のデータベース作成
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
