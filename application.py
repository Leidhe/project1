import os

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    if not "user_id" in session:
        return render_template("login.html")
    else:
        return redirect(url_for('search'))


@app.route("/login", methods=['GET', 'POST'])
def login():
    if "user_id" in session:
        return redirect("/search")
    error = None
    if request.method == 'POST':
        username = request.form.get('inputUsername')
        password = request.form.get('inputPassword')

        if username == "":
            error = "Missing username"
        elif password == "":
            error = "Missing password"

        else:
            exist_user = db.execute("SELECT id FROM users WHERE username = :username AND password = :password", {
                                    "username": username, "password": password}).fetchone()

            if exist_user is None:
                error = "Wrong username or password. Please try again"
            else:
                session["user_id"] = int(exist_user[0])
            return redirect(url_for('search'))
        return render_template('login.html', error=error)

    return render_template('login.html')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if "user_id" in session:
        return redirect("/search")
    error = None
    if request.method == 'POST':

        username = request.form.get('inputUsername')
        password = request.form.get('inputPassword')
        password2 = request.form.get('inputPassword2')

        if username == "":
            error = "Missing username"
        elif password == "":
            error = "Missing password"
        elif password2 == "":
            error = "Missing password"
        elif password != password2:
                error = "Passwords don't matching"
        else:
            exist_username = db.execute("SELECT id FROM users WHERE username = :username", {
                "username": username}).fetchone()
            if exist_username:
                error = "The username exists. Please choose other."
            else:
                db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {
                        "username": username, "password": password})
                db.commit()
                return render_template('login.html', register=" Thank you for registering. Please sign in.")
        return render_template('register.html', error=error)
    return render_template('register.html')

@app.route("/logout")
def logout():
    session.pop('user_id')
    return redirect(url_for('index'))

@app.route("/search")
def search():
    return "AQUI VA SEARCH"


