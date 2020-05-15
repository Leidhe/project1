import os

from flask import Flask, session, request, render_template, flash
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
    session["logged"] = False  # Cambiar

    if not session.get('logged'):
        return render_template('login.html')
    else:
        return "Hello :)"  # Cambiar más adelante


@app.route("/login", methods=['POST'])
def login():
    if request.form['username'] == 'username' and request.form['password'] == 'password':
        session["logged"] = True
        return "logged :)"

    else:
        flash('Invalid Credentials. Try again.')
        return index()

