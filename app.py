#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from operator import ge
from threading import Timer
from types import FunctionType
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask.globals import session
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from logging import Formatter, FileHandler
from flask_wtf import Form
from jinja2.filters import do_default
from forms import *
from sqlalchemy.orm import backref, relationship
import sys
from datetime import datetime
import re

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.secret_key = 'some_secret'
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO-DONE: connect to a local postgresql database

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
  __tablename__ = 'shows'

  venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), primary_key=True)
  start_time = db.Column(db.DateTime, nullable=False)

db.create_all()

#----------------------------------------------------------------------------#
# Helpers.
#----------------------------------------------------------------------------#
def get_upcoming_shows_list_artist(artist_input):
  upcoming_shows_list = []
  upcoming_shows = Show.query.filter_by(venue_id=artist_input.id).filter(datetime.utcnow() <= Show.start_time)
  for show in upcoming_shows:
    venue_hosting_show = Artist.query.filter_by(id=show.artist_id).first()
    show_dict = {
      "artist_id" : show.artist_id,
      "venue_name" : venue_hosting_show.name,
      "venue_image_link" : venue_hosting_show.image_link,
      "start_time" : format_datetime(str(show.start_time))
    }
    upcoming_shows_list.append(show_dict)
  return upcoming_shows_list

def get_past_shows_list_artist(artist_input):
  past_shows_list = []
  past_shows = Show.query.filter_by(venue_id=artist_input.id).filter(datetime.utcnow() > Show.start_time)
  for show in past_shows:
    artist_at_show = Artist.query.filter_by(id=show.artist_id).first()
    show_dict = {
      "artist_id" : show.artist_id,
      "venue_name" : artist_at_show.name,
      "venue_image_link" : artist_at_show.image_link,
      "start_time" : format_datetime(str(show.start_time))
    }
    past_shows_list.append(show_dict)
  return past_shows_list

def get_upcoming_shows_list_venue(venue_input):
  upcoming_shows_list = []
  upcoming_shows = Show.query.filter_by(venue_id=venue_input.id).filter(datetime.utcnow() <= Show.start_time)
  for show in upcoming_shows:
    artist_at_show = Artist.query.filter_by(id=show.artist_id).first()
    show_dict = {
      "artist_id" : show.artist_id,
      "artist_name" : artist_at_show.name,
      "artist_image_link" : artist_at_show.image_link,
      "start_time" : format_datetime(str(show.start_time))
    }
    upcoming_shows_list.append(show_dict)
  return upcoming_shows_list

def get_past_shows_list_venue(venue_input):
  past_shows_list = []
  past_shows = Show.query.filter_by(venue_id=venue_input.id).filter(datetime.utcnow() > Show.start_time)
  for show in past_shows:
    artist_at_show = Artist.query.filter_by(id=show.artist_id).first()
    show_dict = {
      "artist_id" : show.artist_id,
      "artist_name" : artist_at_show.name,
      "artist_image_link" : artist_at_show.image_link,
      "start_time" : format_datetime(str(show.start_time))
    }
    past_shows_list.append(show_dict)
  return past_shows_list

def get_num_upcoming_shows(input):
  if type(input) is Venue:
    numShows = Show.query.filter_by(venue_id=input.id).filter(datetime.utcnow() <= Show.start_time).count()
  else:
    numShows = Show.query.filter_by(artist_id=input.id).filter(datetime.utcnow() <= Show.start_time).count()
  return numShows

def get_num_past_shows(input):
  if type(input) is Venue:
    numShows = Show.query.filter_by(venue_id=(input.id)).filter(datetime.utcnow() > Show.start_time).count()
  else:
    numShows = Show.query.filter_by(artist_id=input.id).filter(datetime.utcnow() > Show.start_time).count()
  return numShows

def get_venue_dict(targetCity, targetCityState):
  venuesInCity = []
  cityVenues = Venue.query.filter_by(city=targetCity)
  for venue in cityVenues:
    venueDict = {
      "id"  : venue.id,
      "name" : venue.name,
      "num_upcoming_shows" : get_num_upcoming_shows(venue)
    }
    venuesInCity.append(venueDict.copy())
  mainDict = {
    "city"  : targetCity,
    "state" : targetCityState,
    "venues": venuesInCity
  }
  return mainDict

def get_venue(id):
  venue = Venue.query.filter_by(id=id).first()
  return venue

def get_artist(id):
  artist = Artist.query.filter_by(id=id).first()
  return artist
#----------------------------------------------------------------------------#
# Formatters.
#----------------------------------------------------------------------------#

def format_genres(genres):
  regex = re.findall("\w+", genres)
  return regex

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = []
  distinctCities = Venue.query.distinct('city').all()
  for city in distinctCities:
    data.append(get_venue_dict(city.city, city.state).copy())
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  user_query=request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike(r"%{}%".format(user_query)))
  data = []
  for venue in venues:
    temp = {
      "id" : venue.id,
      "name" : venue.name,
      "num_upcoming_shows" : get_num_upcoming_shows(venue)
    }
    data.append(temp)
  response = {
    "count" : venues.count(),
    "data" : data
  }
  return render_template('pages/search_venues.html', results=response, search_term=user_query)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.filter_by(id=venue_id).first()
  data = {
    "id" : venue.id,
    "name" : venue.name,
    "address" : venue.address,
    "city" : venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "genres": format_genres(venue.genres),
    "facebook_link" : venue.facebook_link,
    "image_link" : venue.image_link,
    "website_link" : venue.website_link,
    "seeking_talent" : venue.seeking_talent,
    "seeking_description" : venue.seeking_description,
    "past_shows": get_past_shows_list_venue(venue),
    "upcoming_shows" : get_upcoming_shows_list_venue(venue),
    "past_shows_count" : get_num_past_shows(venue),
    "upcoming_shows_count" : get_num_upcoming_shows(venue)
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  try:
    form = VenueForm(request.form)
    name = form.name.data
    city = form.city.data
    state = form.state.data
    address = form.address.data
    phone = form.phone.data
    genres = form.genres.data
    facebook_link = form.facebook_link.data
    image_link = form.image_link.data
    website_link = form.website_link.data
    seeking_talent = form.seeking_talent.data
    seeking_description = form.seeking_description.data
    newVenue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres,
                    facebook_link=facebook_link, image_link=image_link, website_link=website_link,
                    seeking_talent=seeking_talent, seeking_description=seeking_description)
    db.session.add(newVenue)
    db.session.commit()
    flash('Venue ' + name + ' was successfully listed!')
  except:
    error = True
    flash('An error occurred. Venue ' + name + ' could not be listed.')
    db.session.rollback()
    print (sys.exc_info())
  finally:
    db.session.close()
  if error:
    abort(400)
  else:
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    deletion = Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
    flash('You deleted ' + ' from the Venue records')
  except:
    db.session.rollback()
    flash('Deletion unsuccessful')
  finally:
    db.session.close()
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = []
  artists = Artist.query.group_by('id').all()
  for artist in artists:
    artist_dict = {
      "id" : artist.id,
      "name" : artist.name
    }
    data.append(artist_dict.copy())
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  user_query=request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike(r"%{}%".format(user_query)))
  data = []
  for artist in artists:
    temp = {
      "id" : artist.id,
      "name" : artist.name,
      "num_upcoming_shows" : get_num_upcoming_shows(artist)
    }
    data.append(temp)
  response = {
    "count" : artists.count(),
    "data" : data
  }
  return render_template('pages/search_artists.html', results=response, search_term=user_query)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  artist = get_artist(artist_id)
  data = {
    "id" : artist.id,
    "name" : artist.name,
    "city" : artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "genres": format_genres(artist.genres),
    "facebook_link" : artist.facebook_link,
    "image_link" : artist.image_link,
    "website" : artist.website_link,
    "seeking_venue" : artist.seeking_venue,
    "seeking_description" : artist.seeking_description,
    "past_shows": get_past_shows_list_artist(artist),
    "upcoming_shows" : get_upcoming_shows_list_artist(artist),
    "past_shows_count" : get_num_past_shows(artist),
    "upcoming_shows_count" : get_num_upcoming_shows(artist)
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = get_artist(artist_id)
  edittable_artist={
    "id" : artist.id,
    "name" : artist.name,
    "city" : artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "genres": format_genres(artist.genres),
    "facebook_link" : artist.facebook_link,
    "image_link" : artist.image_link,
    "website" : artist.website_link,
    "seeking_venue" : artist.seeking_venue,
    "seeking_description" : artist.seeking_description,
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=edittable_artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    form = ArtistForm(request.form)
    edit_artist = Artist.query.filter_by(id=artist_id).first()
    edit_artist.name = form.name.data
    edit_artist.city = form.city.data
    edit_artist.state = form.state.data
    edit_artist.phone = form.phone.data
    edit_artist.genres = form.genres.data,
    edit_artist.facebook_link = form.facebook_link.data
    edit_artist.image_link = form.image_link.data
    edit_artist.website_link = form.website_link.data
    edit_artist.seeking_venue = form.seeking_venue.data
    edit_artist.seeking_description = form.seeking_description.data
    db.session.commit()
    flash(edit_artist.name +' was editted sucessfully!')
  except:
    db.session.rollback()
    flash('Edtting '+ edit_artist.name +'\'s values caused something to go wrong...')
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = get_venue(venue_id)
  edittable_venue={
    "id": venue.id,
    "name": venue.name,
    "genres": format_genres(venue.genres),
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link
  }
  return render_template('forms/edit_venue.html', form=form, venue=edittable_venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    form = VenueForm(request.form)
    edit_venue = Venue.query.filter_by(id=venue_id).first()
    edit_venue.name = form.name.data
    edit_venue.city = form.city.data
    edit_venue.state = form.state.data
    edit_venue.address = form.address.data
    edit_venue.genres = form.genres.data,
    edit_venue.facebook_link = form.facebook_link.data
    edit_venue.image_link = form.image_link.data
    edit_venue.website_link = form.website_link.data
    edit_venue.seeking_talent = form.seeking_talent.data
    edit_venue.seeking_description = form.seeking_description.data
    db.session.commit()
    flash(edit_venue.name +' was editted sucessfully!')
  except:
    db.session.rollback()
    flash('Edtting '+ edit_venue.name +'\'s values caused something to go wrong...')
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  try:
    form = ArtistForm(request.form)
    name = form.name.data
    city = form.city.data
    state = form.state.data
    phone = form.phone.data
    genres = form.genres.data
    facebook_link = form.facebook_link.data
    image_link = form.image_link.data
    website_link = form.website_link.data
    seeking_venue = form.seeking_venue.data
    seeking_description = form.seeking_description.data
    newArtist = Artist(name=name, city=city, state=state, phone=phone, image_link=image_link,
                    genres=genres, facebook_link=facebook_link, website_link=website_link,
                    seeking_venue=seeking_venue, seeking_description=seeking_description)
    db.session.add(newArtist)
    db.session.commit()
    flash('Artist ' + name + ' was successfully listed!')
  except:
    error = True
    flash('An error occurred. Artist ' + name + ' could not be listed.')
    db.session.rollback()
    print (sys.exc_info())
  finally:
    db.session.close()
  if error:
    abort(400)
  else:
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  shows = Show.query.all()
  data = []
  for show in shows:
    target_venue = Venue.query.filter_by(id=show.venue_id).first()
    target_artist = Artist.query.filter_by(id=show.artist_id).first()
    temp_show = {
      "venue_id" : target_venue.id,
      "venue_name" : target_venue.name,
      "artist_name" : target_artist.name,
      "artist_image_link" : target_artist.image_link,
      "start_time" : format_datetime(str(show.start_time))
    }
    data.append(temp_show.copy())

  # data=[{
  #   "venue_id": 1,
  #   "venue_name": "The Musical Hop",
  #   "artist_id": 4,
  #   "artist_name": "Guns N Petals",
  #   "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
  #   "start_time": "2019-05-21T21:30:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 5,
  #   "artist_name": "Matt Quevedo",
  #   "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
  #   "start_time": "2019-06-15T23:00:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 6,
  #   "artist_name": "The Wild Sax Band",
  #   "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #   "start_time": "2035-04-01T20:00:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 6,
  #   "artist_name": "The Wild Sax Band",
  #   "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #   "start_time": "2035-04-08T20:00:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 6,
  #   "artist_name": "The Wild Sax Band",
  #   "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #   "start_time": "2035-04-15T20:00:00.000Z"
  # }]
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try:
    form = ShowForm(request.form)
    artist_id = form.artist_id.data
    venue_id = form.venue_id.data
    start_time = form.start_time.data
    newShow = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(newShow)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    error = True
    flash('Show could not be listed.')
    db.session.rollback()
    print (sys.exc_info())
  finally:
    db.session.close()
  if error:
    abort(400)
  else:
    return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
  app.debug = True
  app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
