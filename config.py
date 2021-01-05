import os

# Get path to current script
basedir = os.path.abspath(os.path.dirname(__file__))

# Set a secret key
SECRET_KEY = os.urandom(32)

# Enable debug mode
DEBUG = True

# Specify database connection details
dialect = 'postgres'
username = 'sangyoonpark'
password = '' # No password
host = 'localhost'
port = '5432'
db_name = "fyyur"
SQLALCHEMY_DATABASE_URI = f'{dialect}://{username}:{password}@{host}:{port}/{db_name}'
SQLALCHEMY_TRACK_MODIFICATIONS = False
