# Fyyur: Artist-Venue Matching Site

## Getting Started
The current project repo uses [`poetry`](https://python-poetry.org/docs/) to manage
dependencies among different Python packages, which is essential to reproducibility.
Following are steps for setting up and getting started:

First, ensure you are using the right version of Python (`^3.8`). You may want to
use [`pyenv`](https://github.com/pyenv/pyenv) to effectively manage multiple versions
of Python installation. You can then install `poetry`:
```
$ pip install poetry
```

Once you clone the current repo into your local machine, you can go inside the repo and run:
```
$ poetry install
```
to install the right versions of packages for running scripts in the project repo.

To use the new Python configuration that has been installed, you need to run:
```
$ poetry shell
```
which will activate the virtual environment for the project repo.

You can simply type:
```
$ exit
```
to exit from the virtual environment and return to the global (or system) Python installation.

Once the virtual environment is activated, create a new PostgreSQL database to connect and use, e.g.:
```
$ createdb fyyur
```
and set up the configuration in `config.py`, e.g.:
```
dialect = 'postgres'
username = 'sangyoonpark'
password = '' # No password
host = 'localhost'
port = '5432'
db_name = "fyyur"
```

You can then run the following command to populate the database with appropriate tables:
```
$ flask db upgrade
```

Finally, you can launch the application:
```
$ python app.py
```

For successful launch, make sure that the virtual environment has been activated.
