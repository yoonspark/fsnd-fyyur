from datetime import datetime
from flask_wtf import Form
from wtforms import StringField, SelectField, SelectMultipleField, DateTimeField, BooleanField
from wtforms.validators import DataRequired, AnyOf, URL

genre_list = [
    'Alternative',
    'Blues',
    'Classical',
    'Country',
    'Electronic',
    'Folk',
    'Funk',
    'Heavy Metal',
    'Hip-Hop',
    'Instrumental',
    'Jazz',
    'Musical Theatre',
    'Other',
    'Pop',
    'Punk',
    'R&B',
    'Reggae',
    'Rock n Roll',
    'Soul',
]

state_timezone_dict = {
    'AK': 'US/Eastern',
    'AL': 'US/Eastern',
    'AR': 'US/Eastern',
    'AZ': 'US/Eastern',
    'CA': 'US/Eastern',
    'CO': 'US/Eastern',
    'CT': 'US/Eastern',
    'DC': 'US/Eastern',
    'DE': 'US/Eastern',
    'FL': 'US/Eastern',
    'GA': 'US/Eastern',
    'HI': 'US/Eastern',
    'IA': 'US/Eastern',
    'ID': 'US/Eastern',
    'IL': 'US/Eastern',
    'IN': 'US/Eastern',
    'KS': 'US/Eastern',
    'KY': 'US/Eastern',
    'LA': 'US/Eastern',
    'MA': 'US/Eastern',
    'MD': 'US/Eastern',
    'ME': 'US/Eastern',
    'MI': 'US/Eastern',
    'MN': 'US/Eastern',
    'MO': 'US/Eastern',
    'MS': 'US/Eastern',
    'MT': 'US/Eastern',
    'NC': 'US/Eastern',
    'ND': 'US/Eastern',
    'NE': 'US/Eastern',
    'NH': 'US/Eastern',
    'NJ': 'US/Eastern',
    'NM': 'US/Eastern',
    'NV': 'US/Eastern',
    'NY': 'US/Eastern',
    'OH': 'US/Eastern',
    'OK': 'US/Eastern',
    'OR': 'US/Eastern',
    'PA': 'US/Eastern',
    'RI': 'US/Eastern',
    'SC': 'US/Eastern',
    'SD': 'US/Eastern',
    'TN': 'US/Eastern',
    'TX': 'US/Eastern',
    'UT': 'US/Eastern',
    'VA': 'US/Eastern',
    'VT': 'US/Eastern',
    'WA': 'US/Eastern',
    'WI': 'US/Eastern',
    'WV': 'US/Eastern',
    'WY': 'US/Eastern',
}

genre_choices = [(g,g) for g in sorted(genre_list)]
state_choices = [(s,s) for s in sorted(state_timezone_dict.keys())]

class ShowForm(Form):
    artist_id = StringField(
        'artist_id',
    )
    venue_id = StringField(
        'venue_id',
    )
    start_time = DateTimeField(
        'start_time',
        validators=[DataRequired()],
        default=datetime.today(),
    )

class VenueForm(Form):
    name = StringField(
        'name',
        validators=[DataRequired()],
    )
    city = StringField(
        'city',
        validators=[DataRequired()],
    )
    state = SelectField(
        'state',
        validators=[DataRequired()],
        choices=state_choices,
    )
    address = StringField(
        'address',
        validators=[DataRequired()],
    )
    phone = StringField(
        'phone',
    )
    image_link = StringField(
        'image_link',
    )
    genres = SelectMultipleField(
        'genres',
        validators=[DataRequired()],
        choices=genre_choices,
    )
    facebook_link = StringField(
        'facebook_link',
        validators=[URL()],
    )
    website = StringField(
        'website',
        validators=[URL()],
    )
    seeking_talent = BooleanField(
        'seeking_talent',
    )
    seeking_description = StringField(
        'seeking_description',
    )

class ArtistForm(Form):
    name = StringField(
        'name',
        validators=[DataRequired()],
    )
    city = StringField(
        'city',
        validators=[DataRequired()],
    )
    state = SelectField(
        'state',
        validators=[DataRequired()],
        choices=state_choices,
    )
    phone = StringField(
        'phone',
    )
    image_link = StringField(
        'image_link',
    )
    genres = SelectMultipleField(
        'genres',
        validators=[DataRequired()],
        choices=genre_choices,
    )
    facebook_link = StringField(
        'facebook_link',
        validators=[URL()],
    )
    website = StringField(
        'website',
        validators=[URL()],
    )
    seeking_venue = BooleanField(
        'seeking_venue',
    )
    seeking_description = StringField(
        'seeking_description',
    )
