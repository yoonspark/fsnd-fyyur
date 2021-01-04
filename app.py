from datetime import datetime
import pytz
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate

#----------------------------------------------------------------------------#
# App Config
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db, compare_type=True)

#----------------------------------------------------------------------------#
# Data Models
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String())

    def __repr__(self):
        return f'<Venue ID: {self.id}, name: {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'city': self.city,
            'state': self.state,
            'address': self.address,
            'phone': self.phone,
            'image_link': self.image_link,
            'facebook_link': self.facebook_link,
            'website': self.website,
            'seeking_talent': self.seeking_talent,
            'seeking_description': self.seeking_description,
            'genres': [g.name for g in self.genres],
        }

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String())

    def __repr__(self):
        return f'<Artist ID: {self.id}, name: {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'city': self.city,
            'state': self.state,
            'phone': self.phone,
            'image_link': self.image_link,
            'facebook_link': self.facebook_link,
            'website': self.website,
            'seeking_venue': self.seeking_venue,
            'seeking_description': self.seeking_description,
            'genres': [g.name for g in self.genres],
        }

class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime(timezone=True))

    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)

    venue = db.relationship('Venue', backref='shows', lazy=True)
    artist = db.relationship('Artist', backref='shows', lazy=True)

    def __repr__(self):
        return f'<Show ID: {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'start_time': self.start_time,
            'venue_id': self.venue_id,
            'artist_id': self.artist_id,
        }

# Create association tables for genre
venue_genre = db.Table('venue_genre',
    db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True)
)
artist_genre = db.Table('artist_genre',
    db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True)
)

class Genre(db.Model):
    __tablename__ = 'Genre'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    db.UniqueConstraint(name)

    venues = db.relationship('Venue', secondary=venue_genre, backref='genres', lazy=True)
    artists = db.relationship('Artist', secondary=artist_genre, backref='genres', lazy=True)

    def __repr__(self):
        return f'<Genre ID: {self.id}, name: {self.name}>'

#----------------------------------------------------------------------------#
# Filters
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE, MMMM d, y 'at' h:mma"
  elif format == 'medium':
      format="EE, MM/dd/y, h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Helpers
#----------------------------------------------------------------------------#

def time_now():
    return (datetime
        .utcnow()
        .astimezone(pytz.timezone("UTC"))
    )

def get_genre(name):
    g = Genre.query.filter(Genre.name == name).first()
    if not g:
        g = Genre(name=name)

    return g

#----------------------------------------------------------------------------#
# Controllers
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # Identify upcoming shows
    new_shows = db.session.query(
        Show.id.label('id'),
        Show.venue_id.label('venue_id'),
    ).filter(
        Show.start_time > time_now(),
    ).subquery()

    # Get desired venue-level information
    venue_list = db.session.query(
        Venue.id.label('id'),
        Venue.name.label('name'),
        Venue.city.label('city'),
        Venue.state.label('state'),
        db.func.count(Show.id).label('n_new_show'),
    ).outerjoin(
        new_shows,
        Venue.id == new_shows.c.venue_id,
    ).group_by(
        Venue.id,
    ).order_by(
        Venue.city,
        Venue.name,
    ).all()

    # Package data to render
    data = {}
    for v in venue_list:
        # Initialize location entry if not existing
        if (v.city, v.state) not in data:
            data[(v.city, v.state)] = {
                'city': v.city,
                'state': v.state,
                'venues': [],
            }

        # Append each venue to the corresponding location
        data[(v.city, v.state)]['venues'].append({
            'id': v.id,
            'name': v.name,
            'num_upcoming_shows': v.n_new_show,
        })

    # Sort and format data
    data = [data[k] for k in sorted(data.keys())]

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # Get search terms
    search_term = request.form.get('search_term', '')

    # Identify upcoming shows
    new_shows = db.session.query(
        Show.id.label('id'),
        Show.venue_id.label('venue_id'),
    ).filter(
        Show.start_time > time_now(),
    ).subquery()

    # Search venues
    venue_list = db.session.query(
        Venue.id.label('id'),
        Venue.name.label('name'),
        db.func.count(new_shows.c.id).label('n_new_show'),
    ).filter(
        Venue.name.ilike("%{}%".format(search_term)),
    ).outerjoin(
        new_shows,
        Venue.id == new_shows.c.venue_id,
    ).group_by(
        Venue.id,
    ).order_by(
        Venue.name,
    ).all()

    # Package response data
    response = {'count': 0, 'data': []}
    for v in venue_list:
        response['count'] = response['count'] + 1
        response['data'].append({
            'id': v.id,
            'name': v.name,
            'num_upcoming_shows': v.n_new_show,
        })

    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # Get venue info
    v = Venue.query.get(venue_id)

    # Query all shows at the venue
    s_query = db.session.query(
        Show.start_time.label('start_time'),
        Artist.id.label('artist_id'),
        Artist.name.label('artist_name'),
        Artist.image_link.label('artist_image_link'),
    ).filter(
        Show.venue_id == venue_id,
    ).outerjoin(
        Artist,
        Show.artist_id == Artist.id,
    ).order_by(
        Show.start_time,
    )

    # Identify past shows
    old_shows = s_query.filter(Show.start_time < time_now()).all()
    old_shows = [s._asdict() for s in old_shows]
    old_shows.reverse() # For past shows, display latest one first
    for s in old_shows:
        s['start_time'] = s['start_time'].isoformat()

    # Identify upcoming shows
    new_shows = s_query.filter(Show.start_time > time_now()).all()
    new_shows = [s._asdict() for s in new_shows]
    for s in new_shows:
        s['start_time'] = s['start_time'].isoformat()

    # Package data to render
    data = v.to_dict()
    data['past_shows'] = old_shows
    data['past_shows_count'] = len(old_shows)
    data['upcoming_shows'] = new_shows
    data['upcoming_shows_count'] = len(new_shows)

    return render_template('pages/show_venue.html', venue=data)


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue():
    v = Venue(
        name = request.form.get('name'),
        city = request.form.get('city'),
        state = request.form.get('state'),
        address = request.form.get('address'),
        phone = request.form.get('phone'),
        image_link = request.form.get('image_link'),
        facebook_link = request.form.get('facebook_link'),
        website = request.form.get('website'),
        seeking_talent = request.form.get('seeking_talent', False),
        seeking_description = request.form.get('seeking_description'),
    )
    v.genres = [get_genre(name=g) for g in request.form.getlist('genres')]

    error = False
    try:
        db.session.add(v)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Venue \"' + request.form.get('name') + '\" could not be listed.')
        abort(400)
    else:
        flash('Venue \"' + request.form.get('name') + '\" was successfully listed!')

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    v = Venue.query.get(venue_id)
    venue_name = v.name
    error = False

    try:
        for s in v.shows:
            db.session.delete(s)
        db.session.delete(v)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue \"' + venue_name + '\" could not be deleted.')
        abort(400)
    else:
        flash('Venue \"' + venue_name + '\" was successfully deleted!')

    return None


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue_form(venue_id):
    v = Venue.query.get(venue_id)
    if not v:
        abort(404)
    venue = v.to_dict()

    # Populate form with existing values
    form = VenueForm()
    form.name.data = venue['name']
    form.city.data = venue['city']
    form.state.data = venue['state']
    form.address.data = venue['address']
    form.phone.data = venue['phone']
    form.image_link.data = venue['image_link']
    form.facebook_link.data = venue['facebook_link']
    form.website.data = venue['website']
    form.seeking_talent.data = venue['seeking_talent']
    form.seeking_description.data = venue['seeking_description']
    form.genres.data = venue['genres']

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue(venue_id):
    v = Venue.query.get(venue_id)
    if not v:
        abort(404)
    vid = v.id

    # Update venue info
    v.name = request.form.get('name')
    v.city = request.form.get('city')
    v.state = request.form.get('state')
    v.address = request.form.get('address')
    v.phone = request.form.get('phone')
    v.image_link = request.form.get('image_link')
    v.facebook_link = request.form.get('facebook_link')
    v.website = request.form.get('website')
    v.seeking_talent = request.form.get('seeking_talent')
    v.seeking_description = request.form.get('seeking_description')
    v.genres = [get_genre(name=g) for g in request.form.getlist('genres')]

    # Save into database
    error = False
    try:
        db.session.add(v)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Venue <ID: ' + str(vid) + '> could not be updated.')
        abort(400)
    else:
        flash('Venue <ID: ' + str(vid) + '> was successfully updated!')

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Artists
#  ----------------------------------------------------------------

@app.route('/artists')
def artists():
    # Get artist info
    artists = db.session.query(
        Artist.id.label('id'),
        Artist.name.label('name'),
    ).all()

    # Package data for rendering
    data = [a._asdict() for a in artists]

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # Get search terms
    search_term = request.form.get('search_term', '')

    # Identify upcoming shows
    new_shows = db.session.query(
        Show.id.label('id'),
        Show.artist_id.label('artist_id'),
    ).filter(
        Show.start_time > time_now(),
    ).subquery()

    # Search artists
    artist_list = db.session.query(
        Artist.id.label('id'),
        Artist.name.label('name'),
        db.func.count(new_shows.c.id).label('n_new_show'),
    ).filter(
        Artist.name.ilike("%{}%".format(search_term)),
    ).outerjoin(
        new_shows,
        Artist.id == new_shows.c.artist_id,
    ).group_by(
        Artist.id,
    ).order_by(
        Artist.name,
    ).all()

    # Package response data
    response = {'count': 0, 'data': []}
    for a in artist_list:
        response['count'] = response['count'] + 1
        response['data'].append({
            'id': a.id,
            'name': a.name,
            'num_upcoming_shows': a.n_new_show,
        })

    return render_template('pages/search_artists.html', results=response, search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # Get artist info
    a = Artist.query.get(artist_id)

    # Query all shows by the artist
    s_query = db.session.query(
        Show.start_time.label('start_time'),
        Venue.id.label('venue_id'),
        Venue.name.label('venue_name'),
        Venue.image_link.label('venue_image_link'),
    ).filter(
        Show.artist_id == artist_id,
    ).outerjoin(
        Venue,
        Show.venue_id == Venue.id,
    ).order_by(
        Show.start_time,
    )

    # Identify past shows
    old_shows = s_query.filter(Show.start_time < time_now()).all()
    old_shows = [s._asdict() for s in old_shows]
    old_shows.reverse() # For past shows, display latest one first
    for s in old_shows:
        s['start_time'] = s['start_time'].isoformat()

    # Identify upcoming shows
    new_shows = s_query.filter(Show.start_time > time_now()).all()
    new_shows = [s._asdict() for s in new_shows]
    for s in new_shows:
        s['start_time'] = s['start_time'].isoformat()

    # Package data to render
    data = a.to_dict()
    data['past_shows'] = old_shows
    data['past_shows_count'] = len(old_shows)
    data['upcoming_shows'] = new_shows
    data['upcoming_shows_count'] = len(new_shows)

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data=[{
    "venue_id": 1,
    "venue_name": "The Musical Hop",
    "artist_id": 4,
    "artist_name": "Guns N Petals",
    "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    "start_time": "2019-05-21T21:30:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 5,
    "artist_name": "Matt Quevedo",
    "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    "start_time": "2019-06-15T23:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-01T20:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-08T20:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-15T20:00:00.000Z"
  }]
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  # on successful db insert, flash success
  flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
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
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
