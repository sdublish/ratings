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

BERATEMENT = [
    "I suppose you don't have such bad taste after all.",
    "I regret every decision that I've ever made that has brought me to listen to your opinion.",
    "Words fail me, as your taste in movies has clearly failed you.",
    "That movie is great. For a clown to watch. Idiot.",
    "Words cannot express the awfulness of your taste."
]


@app.route('/')
def index():
    """Homepage."""
    return render_template("homepage.html")


@app.route("/users")
def show_users():
    """ Shows a list of all users on site"""
    users = User.query.all()

    return render_template("user_list.html", users=users)


@app.route("/user_info/<user_id>")
def show_user_info(user_id):
    """ Shows information on specific user"""
    user = User.query.filter_by(user_id=user_id).first()

    return render_template("user_info.html", user=user)


@app.route("/update-user", methods=["POST"])
def update_user():
    """ Lets user update information if they are logged in"""
    user_id = session.get("user_id")
    age = request.form.get("age")
    zipcode = request.form.get("zipcode")

    user = User.query.filter_by(user_id=user_id).first()

    user.age = age
    user.zipcode = zipcode

    db.session.commit()
    flash("User information successfully updated")
    return redirect("/user_info/{}".format(user_id))


@app.route("/movies")
def show_movies():
    """ Shows all movies in database, in alphabetical order"""
    movies = Movie.query.order_by(Movie.title).all()

    return render_template("movies.html", movies=movies)


@app.route("/movie_info/<movie_id>")
def show_movie_info(movie_id):
    """ Shows information about a specific movie"""
    movie = Movie.query.filter_by(movie_id=movie_id).first()
    user_id = session.get("user_id")

    if user_id:
        user_rating = Rating.query.filter_by(movie_id=movie_id, user_id=user_id).first()

    else:
        user_rating = None

    rating_scores = [r.score for r in movie.ratings]
    avg_rating = float(sum(rating_scores) / len(rating_scores))
    prediction = None

    if (not user_rating) and user_id:
        user = User.query.get(user_id)
        if user:
            prediction = user.predict_rating(movie)

    if prediction:
        effective_rating = prediction
    elif user_rating:
        effective_rating = user_rating.score
    else:
        effective_rating = None

    the_eye = User.query.filter_by(email="the-eye@of-judgement.com").first()
    print(the_eye)
    eye_rating = Rating.query.filter_by(user_id=the_eye.user_id, movie_id=movie.movie_id).first()

    if eye_rating is None:
        eye_rating = the_eye.predict_rating(movie)
    else:
        eye_rating = eye_rating.score

    if eye_rating and effective_rating:
        difference = abs(eye_rating-effective_rating)
    else:
        difference = None

    if difference:
        beratement = BERATEMENT[int(difference)]
    else:
        beratement = None

    return render_template("movie_info.html", movie=movie,
                           user_rating=user_rating,
                           average=avg_rating,
                           prediction=prediction,
                           beratement=beratement)


@app.route("/add-rating", methods=["POST"])
def add_movie():
    """ Adds or updates rating associated for user in database"""
    movie_id = request.form.get("movie_id")
    rating = request.form.get("rating")
    user_id = session.get("user_id")

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


@app.route("/new-user")
def show_form():
    """Shows registration form for new user """
    return render_template("new_user.html")


@app.route("/add-user", methods=["POST"])
def add_user():
    """ Adds new user to database if email is not already present"""
    email = request.form.get("email")
    password = request.form.get("password")

    if User.query.filter_by(email=email).first():
        flash("Email already exists!")
        return redirect("/new-user")

    else:
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash("New user successfully added.")
        return redirect("/login")


@app.route("/login", methods=["GET"])
def show_login():
    """ Shows login form"""
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    """ Logs in user if email and password submitted matches what is in database"""
    email = request.form.get("email")
    password = request.form.get("password")

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
    """ Logs out user """
    if session.get("user_id"):
        del session["user_id"]
        # lets us do 'if key in session' checks instead of checking
        # to see if the key value is None
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
