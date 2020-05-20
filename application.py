import json
import os

import requests
from flask import (Flask, abort, flash, jsonify, redirect, render_template,
                   request, session, url_for)
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
        return redirect(url_for('login'))
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
            print(exist_user)
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
    session.clear()
    return redirect(url_for('index'))


@app.route("/search", methods=['GET', 'POST'])
def search():
    if not "user_id" in session:
        return redirect("/login")
    text = None
    if request.method == 'POST':
        search = request.form.get('search')
        text = "Your results for " + search + ":"
        search = search.capitalize()
        books = db.execute("SELECT id, isbn, title, author, year FROM books WHERE \
                            books.isbn LIKE :search OR \
                            books.title LIKE :search OR \
                            books.author LIKE :search",
                           {"search": search + '%'}).fetchall()

        if books == []:
            text = "No book has been found. Try again"
            return render_template('search.html', text=text)
        print(books)
        return render_template('search.html', books=books, text=text)

    return render_template('search.html')


@app.route("/books/<int:book_id>", methods=['GET', 'POST'])
def book(book_id):
    if not "user_id" in session:
        return redirect("/login")

    user_id = session.get("user_id")

    error = None

    # Make sure book exists.
    book = db.execute("SELECT * FROM books WHERE id = :id",
                      {"id": book_id}).fetchone()
    if book is None:
            abort(404)
    # Get the book.
    book = db.execute("SELECT title, author, year, isbn FROM books WHERE id = :id",
                      {"id": book_id}).fetchone()
    title = book.title
    author = book.author
    year = book.year
    isbn = book.isbn
    print("hola ")
    
    #Get all reviews of the book
    reviews = db.execute("SELECT users.username, reviews.rating, reviews.review \
                        FROM books JOIN reviews ON books.id = reviews.book_id \
                        JOIN users ON reviews.user_id = users.id \
                        WHERE books.id = :id",
                         {"id": book_id}).fetchall()

    # Make request to Goodreads API
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": "lcYiJCdL01tLTLRaMrlCg", "isbns": isbn})

    number_ratings = None
    average_score = None

    if res.status_code == 200:
        data = res.json()
        number_ratings = data["books"][0]["work_ratings_count"]
        average_score = data["books"][0]["average_rating"]

    #Put a review
    if request.method == 'POST':

        rating = request.form.get('rating')
        review = request.form.get('review')

        exist_review = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_id = :book_id", {"user_id": user_id, "book_id": book_id}).fetchone()

        if review == "":
            error = "Error = Please write a review"
        #Check if the current user has put a comment in the book
        elif exist_review:
            error = "Error = You've already written a review before."
        else:    
            db.execute("INSERT INTO reviews (rating, review, user_id, book_id) VALUES (:rating, :review, :user_id, :book_id)", {
            "rating": rating, "review": review, "user_id": user_id, "book_id": book_id})
            db.commit()
            #Update all reviews of the book
            reviews = db.execute("SELECT reviews.user_id, reviews.rating, reviews.review FROM books JOIN reviews ON books.id = reviews.book_id WHERE books.id = :id",
                         {"id": book_id}).fetchall()


    return render_template("book.html", error = error, reviews = reviews, id = book_id, title=title, author=author, year=year, isbn=isbn, average_score=average_score, number_ratings=number_ratings)


@app.route("/api/<isbn>", methods=['GET'])
def api(isbn):
    # Make sure book exists.
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                      {"isbn": isbn}).fetchone()
    if book is None:
        abort(404)
    # Get the book.
    book = db.execute("SELECT title, author, year, isbn, AVG(rating) as average_score, COUNT(review) as review_count FROM books LEFT JOIN reviews ON books.id = reviews.book_id WHERE isbn = :isbn GROUP BY title, author, year, isbn",
                      {"isbn": isbn}).fetchone()

    return jsonify(title=book.title,
                   author=book.author,
                   year=book.year,
                   isbn=book.isbn,
                   review_count=book.review_count,
                   average_score=book.average_score)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('error_404.html'), 404
