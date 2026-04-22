import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_dance.contrib.google import make_google_blueprint, google
import pymysql, random, datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

# DATABASE MYSQL WORKBENCH

def get_connection():
    return pymysql.connect(
        host="127.0.0.1",
        user="root",
        password="Puru@132002",
        database="quiz_app",
        cursorclass=pymysql.cursors.DictCursor
    )

# GOOGLE LOGIN

google_bp = make_google_blueprint(
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_to="dashboard",
    scope=["https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"]
)
app.register_blueprint(google_bp, url_prefix="/login")

# ROUTES
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login")
def login():
    if not google.authorized:
        return redirect(url_for("google.login"))
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    resp = google.get("/oauth2/v2/userinfo")
    user = resp.json()
    session['user'] = user
    return render_template("dashboard.html", user=user)

@app.route("/quiz")
def quiz():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM questions")
    questions = cur.fetchall()
    random.shuffle(questions)
    return render_template("quiz.html", questions=questions)

@app.route("/submit_quiz", methods=["POST"])
def submit_quiz():
    answers = request.json
    conn = get_connection()
    cur = conn.cursor()
    score = 0

    for qid, ans in answers.items():
        cur.execute("SELECT answer FROM questions WHERE id=%s", (qid,))
        if ans == cur.fetchone()['answer']:
            score += 1

    user = session.get('user')
    if user:
        cur.execute("INSERT INTO scores(name,email,score,date) VALUES(%s,%s,%s,%s)",
                    (user['name'], user['email'], score, datetime.datetime.now()))
        conn.commit()

    return jsonify({"score": score})

@app.route("/leaderboard")
def leaderboard():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name,score FROM scores ORDER BY score DESC LIMIT 10")
    return render_template("leaderboard.html", data=cur.fetchall())

@app.route("/admin")
def admin():
    return render_template("admin.html")

@app.route("/add_question", methods=["POST"])
def add_question():
    d = request.form
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO questions(question,option1,option2,option3,option4,answer) VALUES(%s,%s,%s,%s,%s,%s)",
                (d['question'],d['o1'],d['o2'],d['o3'],d['o4'],d['ans']))
    conn.commit()
    return redirect('/admin')

if __name__ == "__main__":
    app.run(debug=True)