import os

# Get path to current script
basedir = os.path.abspath(os.path.dirname(__file__))

# Set a secret key
SECRET_KEY = os.urandom(32)

# Enable debug mode
DEBUG = True

# Specify database connection details
SQLALCHEMY_DATABASE_URI = 'postgresql://sangyoonpark@localhost:5432/fyyur'
SQLALCHEMY_TRACK_MODIFICATIONS = False
