from flask import Flask
from os import getenv

app = Flask(__name__)
app.config.from_object('config.default')

if getenv('KEBLE_BALL_ENV', 'DEVELOPMENT') == 'PRODUCTION':
    app.config.from_object('config.production')
else:
    app.config.from_object('config.development')

@app.route('/hello')
def hello_world():
    return ('Hello World! I am the Keble Ball Ticketing System, '
        'running in the {0} environment').format(app.config['ENVIRONMENT'])

@app.route('/')
def index():
    raise NotImplementedError

if __name__ == '__main__':
    app.run()
