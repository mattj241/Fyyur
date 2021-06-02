from flask import Flask
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.secret_key = 'some_secret'
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
db.create_all()

# @ Udacity mentor, what resources do you recommend to architect a better flask app that reflects MVC? 
# I was having trouble setting up a "controllers.py" in this dir that could somehow re-direct routes declared in app.py to controllers.py

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
  __tablename__ = 'venue'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String, nullable = False)
  city = db.Column(db.String(120), nullable = False)
  state = db.Column(db.String(120), nullable = False)
  address = db.Column(db.String(120), nullable = False)
  phone = db.Column(db.String(120), nullable = False)
  genres = db.Column(db.String, nullable = False)
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  website_link = db.Column(db.String(120))
  seeking_talent = db.Column(db.Boolean)
  seeking_description = db.Column(db.String)
  v_shows = db.relationship('Show', backref='venue')


class Artist(db.Model):
  __tablename__ = 'artist'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String, nullable = False)
  city = db.Column(db.String(120), nullable = False)
  state = db.Column(db.String(120), nullable = False)
  phone = db.Column(db.String(120), nullable = False)
  genres = db.Column(db.String(120), nullable = False)
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  website_link = db.Column(db.String(120))
  seeking_venue = db.Column(db.Boolean)
  seeking_description = db.Column(db.String)
  a_shows = db.relationship('Show', backref='artist')

class Show(db.Model):
  __tablename__ = 'show'

  id = db.Column(db.Integer, primary_key=True)
  venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'))
  artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'))
  start_time = db.Column(db.DateTime, nullable=False)