"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import (Flask, render_template, redirect, request, flash,
                   session)
from flask_debugtoolbar import DebugToolbarExtension

from model import User, Rating, Movie, connect_to_db, db


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""
    return render_template("homepage.html")


@app.route("/users")
def show_users():

    users = User.query.all()

    return render_template("user_list.html", users=users)


@app.route("/user_info/<user_id>")
def show_user_info(user_id):
    user = User.query.filter_by(user_id=user_id).first()

    return render_template("user_info.html", user=user)


@app.route("/movies")
def show_movies():
    movies = Movie.query.order_by(Movie.title).all()

    return render_template("movies.html", movies=movies)


@app.route("/movie_info/<movie_id>")
def show_movie_info(movie_id):
    movie = Movie.query.filter_by(movie_id=movie_id).first()

    return render_template("movie_info.html", movie=movie)


@app.route("/new-user")
def show_form():
    return render_template("new_user.html")


@app.route("/add-movie", methods=["POST"])  # submit new user data
def add_movie():
    movie_id = request.form["movie_id"]
    rating = request.form["rating"]
    user_id = session["user_id"]

    rating_q = Rating.query.filter(Rating.movie_id == movie_id, Rating.user_id == user_id).first()

    if rating_q:
        rating_q.score = rating
        flash("Rating successfully updated")
    else:
        new_rating = Rating(movie_id=movie_id, score=rating, user_id=user_id)
        db.session.add(new_rating)
        flash("Rating successfully created")

    db.session.commit()
    return redirect("/movies")


@app.route("/add-user", methods=["POST"])  # submit new user data
def add_user():
    email = request.form["email"]
    password = request.form["password"]

    if not User.query.filter_by(email=email).first():
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash("New user successfully added.")
        return redirect("/login")
    else:
        flash("Email already exists!")
        return redirect("/new-user")


@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def actually_login():
    email = request.form["email"]
    password = request.form["password"]
    user = User.query.filter(User.email == email, User.password == password).first()

    if user:
        session["user_id"] = user.user_id
        flash("Logged In!")
        return redirect("/user_info/{}".format(user.user_id))
    else:
        flash("Incorrect email and/or password")
        return redirect("/login")


@app.route("/logout")
def logout():
    if session.get("user_id"):
        del session["user_id"]
        flash("Logged Out!")
    else:
        flash("You are not logged in")
    return redirect("/")





if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    # make sure templates, etc. are not cached in debug mode
    app.jinja_env.auto_reload = app.debug

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
