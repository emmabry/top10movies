from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)


# CREATE DB
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///topmovies.db'
db.init_app(app)


# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(unique=True)
    year: Mapped[int] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column()
    rating: Mapped[float] = mapped_column(nullable=True)
    ranking: Mapped[int] = mapped_column(nullable=True)
    review: Mapped[str] = mapped_column(nullable=True)
    img_url: Mapped[str] = mapped_column()

with app.app_context():
    db.create_all()
class EditMovieForm(FlaskForm):
    movie_rating = StringField('Rating', validators=[DataRequired()])
    movie_review = StringField('Review', validators=[DataRequired()])
    submit = SubmitField('Submit')


class AddMovieForm(FlaskForm):
    movie_title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating.desc()))
    all_movies = result.scalars().all()
    length = len(all_movies)
    ranking = length - (length - 1)
    for movie in all_movies:
        movie.ranking = ranking
        ranking += 1
    return render_template("index.html", all_movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = EditMovieForm()
    movie_id = request.args.get("id")
    movie_to_edit = db.get_or_404(Movie, movie_id)
    if request.method == "POST":
        movie_to_edit.rating = form.movie_rating.data
        movie_to_edit.review = form.movie_review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", movie=movie_to_edit, form=form)


@app.route('/delete')
def delete():
    movie_id = request.args.get("id")
    movie_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJlYTkwMzNlZTlkMDJhZWY2N2QzMjdiZTkxZTdhMzEyYSIsIm5iZiI6MTcyODY3MTIyNy41NjcxOTYsInN1YiI6IjY3MDk2Y2E1ZTFkYjllYzQ4NjJlODhmNiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.AYHYjwvNX45OMUheh4Fu87ui5YXQ29cxinYQz4MRY28"
}
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

@app.route('/add', methods=["GET", "POST"])
def add():
    add_form = AddMovieForm()
    movie_title = add_form.movie_title.data
    if add_form.validate_on_submit():
        response = requests.get("https://api.themoviedb.org/3/search/movie", headers=headers, params={"query": movie_title})
        print(response)
        results = response.json()['results'][0]
        year = results["release_date"]
        print(f"results are {results}")
        movie_to_add = Movie(
            title=results['title'],
            year=year[:4],
            description=results['overview'],
            img_url=f"{MOVIE_DB_IMAGE_URL}{results['poster_path']}"
            )
        with app.app_context():
            db.session.add(movie_to_add)
            db.session.commit()
            added_movie_id = movie_to_add.id
            return redirect(url_for("edit", id=added_movie_id))
    return render_template("add.html", form=add_form)


if __name__ == '__main__':
    app.run(debug=True)
