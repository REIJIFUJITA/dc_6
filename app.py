from flask import Flask, redirect, url_for, session, render_template, request
from models import db, User
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
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
    return render_template("index.html")

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

        return render_template("profile.html", name=name, email=email)
    except Exception as e:
        print("Error:", e)  # エラーメッセージを出力
        return "認証に失敗しました。"

# 初回実行時のデータベース作成
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
