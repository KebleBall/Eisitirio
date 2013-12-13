from flask import Flask
from os import getenv

app = Flask(__name__)

app.config.from_pyfile('config/default.py')

if getenv('KEBLE_BALL_ENV', 'DEVELOPMENT') == 'PRODUCTION':
    app.config.from_pyfile('config/production.py')
else:
    app.config.from_pyfile('config/development.py')