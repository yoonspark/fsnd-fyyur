from datetime import datetime
from flask_wtf import Form
from wtforms import (
    IntegerField,
    StringField,
    SelectField,
    SelectMultipleField,
    DateTimeField,
    BooleanField,
)
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

state_list = {
    'AK',
    'AL',
    'AR',
    'AZ',
    'CA',
    'CO',
    'CT',
    'DC',
    'DE',
    'FL',
    'GA',
    'HI',
    'IA',
    'ID',
    'IL',
    'IN',
    'KS',
    'KY',
    'LA',
    'MA',
    'MD',
    'ME',
    'MI',
    'MN',
    'MO',
    'MS',
    'MT',
    'NC',
    'ND',
    'NE',
    'NH',
    'NJ',
    'NM',
    'NV',
    'NY',
    'OH',
    'OK',
    'OR',
    'PA',
    'RI',
    'SC',
    'SD',
    'TN',
    'TX',
    'UT',
    'VA',
    'VT',
    'WA',
    'WI',
    'WV',
    'WY',
}

genre_choices = [(g,g) for g in sorted(genre_list)]
state_choices = [(s,s) for s in sorted(state_list)]

class ShowForm(Form):
    artist_id = IntegerField(
        'artist_id',
        validators=[DataRequired()],
    )
    venue_id = IntegerField(
        'venue_id',
        validators=[DataRequired()],
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
