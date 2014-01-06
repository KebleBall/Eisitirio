from flask import Flask
from os import environ

app = Flask(__name__)

app.config.from_pyfile('config/default.py')

if 'KEBLE_BALL_ENV' in environ and environ['KEBLE_BALL_ENV'] == 'PRODUCTION':
    app.config.from_pyfile('config/production.py')
else:
    app.config.from_pyfile('config/development.py')