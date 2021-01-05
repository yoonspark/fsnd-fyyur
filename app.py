import sys
import logging
from logging import Formatter, FileHandler
import dateutil.parser
import babel
from datetime import datetime
import pytz
from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    abort,
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from forms import VenueForm, ArtistForm, ShowForm
from models import db, Venue, Artist, Show, Genre

#----------------------------------------------------------------------------#
# App Config
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.app = app
db.init_app(app)
migrate = Migrate(app, db, compare_type=True)

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
    if not v:
        abort(404)

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
        seeking_talent = True if request.form.get('seeking_talent') else False,
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
    v.seeking_talent = True if request.form.get('seeking_talent') else False
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


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    v = Venue.query.get(venue_id)
    if not v:
        abort(404)
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

    return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------

@app.route('/artists')
def artists():
    # Get artist info
    artists = db.session.query(
        Artist.id.label('id'),
        Artist.name.label('name'),
    ).order_by(
        Artist.name,
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
    if not a:
        abort(404)

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


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist():
    a = Artist(
        name = request.form.get('name'),
        city = request.form.get('city'),
        state = request.form.get('state'),
        phone = request.form.get('phone'),
        image_link = request.form.get('image_link'),
        facebook_link = request.form.get('facebook_link'),
        website = request.form.get('website'),
        seeking_venue = True if request.form.get('seeking_venue') else False,
        seeking_description = request.form.get('seeking_description'),
    )
    a.genres = [get_genre(name=g) for g in request.form.getlist('genres')]

    error = False
    try:
        db.session.add(a)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Artist \"' + request.form.get('name') + '\" could not be listed.')
        abort(400)
    else:
        flash('Artist \"' + request.form.get('name') + '\" was successfully listed!')

    return render_template('pages/home.html')


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist_form(artist_id):
    a = Artist.query.get(artist_id)
    if not a:
        abort(404)
    artist = a.to_dict()

    # Populate form with existing values
    form = ArtistForm()
    form.name.data = artist['name']
    form.city.data = artist['city']
    form.state.data = artist['state']
    form.phone.data = artist['phone']
    form.image_link.data = artist['image_link']
    form.facebook_link.data = artist['facebook_link']
    form.website.data = artist['website']
    form.seeking_venue.data = artist['seeking_venue']
    form.seeking_description.data = artist['seeking_description']
    form.genres.data = artist['genres']

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist(artist_id):
    a = Artist.query.get(artist_id)
    if not a:
        abort(404)
    aid = a.id

    # Update artist info
    a.name = request.form.get('name')
    a.city = request.form.get('city')
    a.state = request.form.get('state')
    a.phone = request.form.get('phone')
    a.image_link = request.form.get('image_link')
    a.facebook_link = request.form.get('facebook_link')
    a.website = request.form.get('website')
    a.seeking_venue = True if request.form.get('seeking_venue') else False
    a.seeking_description = request.form.get('seeking_description')
    a.genres = [get_genre(name=g) for g in request.form.getlist('genres')]

    # Save into database
    error = False
    try:
        db.session.add(a)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Artist <ID: ' + str(aid) + '> could not be updated.')
        abort(400)
    else:
        flash('Artist <ID: ' + str(aid) + '> was successfully updated!')

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
    a = Artist.query.get(artist_id)
    if not a:
        abort(404)
    artist_name = a.name
    error = False

    try:
        for s in a.shows:
            db.session.delete(s)
        db.session.delete(a)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Artist \"' + artist_name + '\" could not be deleted.')
        abort(400)
    else:
        flash('Artist \"' + artist_name + '\" was successfully deleted!')

    return redirect(url_for('index'))

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # Query all shows
    s_query = db.session.query(
        Show.start_time.label('start_time'),
        Artist.id.label('artist_id'),
        Artist.name.label('artist_name'),
        Artist.image_link.label('artist_image_link'),
        Venue.id.label('venue_id'),
        Venue.name.label('venue_name'),
    ).outerjoin(
        Artist,
        Show.artist_id == Artist.id,
    ).outerjoin(
        Venue,
        Show.venue_id == Venue.id,
    ).order_by(
        Show.start_time,
        Artist.name,
        Venue.name,
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

    # Package data for rendering
    data = {
        'past_shows': old_shows,
        'past_shows_count': len(old_shows),
        'upcoming_shows': new_shows,
        'upcoming_shows_count': len(new_shows),
    }

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_show_form():
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show():
    if not Artist.query.get(request.form['artist_id']):
        flash('Error: Artist does not exist.')
        abort(400)
    if not Venue.query.get(request.form['venue_id']):
        flash('Error: Venue does not exist.')
        abort(400)

    s = Show(
        start_time = request.form.get('start_time'),
        artist_id = request.form.get('artist_id'),
        venue_id = request.form.get('venue_id'),
    )

    error = False
    try:
        db.session.add(s)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Show could not be listed.')
        abort(400)
    else:
        flash('Show was successfully listed!')

    return render_template('pages/home.html')

#----------------------------------------------------------------------------#
# Error Handlers
#----------------------------------------------------------------------------#

@app.errorhandler(400)
def bad_request_error(error):
    return render_template('errors/400.html'), 400


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
# Launch
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
