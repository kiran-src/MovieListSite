from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, SelectField
from wtforms.fields.html5 import URLField
from wtforms.validators import DataRequired
import requests
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), unique=False, nullable=False)
    year = db.Column(db.Integer, unique=False, nullable=False)
    description = db.Column(db.String(1500), unique=True, nullable=False)
    rating = db.Column(db.Float, unique=False, nullable=True)
    review = db.Column(db.String(1500), unique=False, nullable=True)
    img_url = db.Column(db.String(150), unique=True, nullable=False)


db.create_all()


# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds "
#                 "himself trapped in a phone booth, pinned down by an extortionist's "
#                 "sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads "
#                 "to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
# db.session.add(new_movie)
# db.session.commit()


class EditForm(FlaskForm):
    rating = FloatField('Rating out of 10', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Submit')


class AddMovie(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField('Submit')

movies = []

@app.route("/")
def home():
    movies = []
    for count, i in enumerate(db.session.query(Movie).order_by(Movie.rating.desc())):
        movies.append({
            'id': count+1,
            'title': i.title,
            'year': i.year,
            'description': i.description,
            'rating': i.rating,
            'review': i.review,
            'img_url': i.img_url
        })
    return render_template("index.html", movies=movies)


@app.route("/edit/<title>", methods=['POST', 'GET'])
def edit(title):
    form = EditForm()
    if form.validate_on_submit():
        movie = Movie.query.filter_by(title=title).first()
        movie.rating = form.rating.data
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", title=title, form=form)


@app.route("/delete/<title>")
def delete(title):
    db.session.delete(Movie.query.filter_by(title=title).first())
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=['POST', 'GET'])
def add():
    form = AddMovie()
    if form.validate_on_submit():
        return redirect(url_for('select', title=form.title.data))
    return render_template('add.html', form=form)

@app.route('/select/t/<title>')
def select(title):
    url = "https://api.themoviedb.org/3//search/movie"
    params = {
        'api_key': os.environ.get('API_KEY'),
        'query': title
    }
    headers = {
        'Authorization': os.environ.get('API_TOKEN'),
        'Content-Type': 'application/json;charset=utf-8'
    }
    movie_db = requests.get(url=url, params=params, headers=headers)
    movie_db.raise_for_status()
    global movies
    movies = movie_db.json()['results']
    return render_template("select.html", data=movies)

@app.route('/select/i/<movie_id>')
def found(movie_id):
    title = ''
    for i in movies:
        print(i['id'])
        if int(i['id']) == int(movie_id):
            new_movie = Movie(
                title=i['original_title'],
                year=i['release_date'].split('-')[0],
                description=i['overview'],
                rating=i['vote_average'],
                review='',
                img_url='https://image.tmdb.org/t/p/original' + i['poster_path']
            )
            db.session.add(new_movie)
            db.session.commit()
            title = i['original_title']
            break
    return redirect(url_for('edit', title=title))

if __name__ == '__main__':
    app.run(debug=True)
