from flask import Flask
import os
import json

app = Flask(__name__)
app.config.from_object('config.default')

if os.getenv('KEBLE_BALL_ENV', 'DEVELOPMENT') == 'PRODUCTION':
    app.config.from_object('config.production')
else:
    app.config.from_object('config.development')

@app.route('/hello')
def hello_world():
    return ('Hello World! I am the Keble Ball Ticketing System, '
        'running in the {0} environment').format(getenv('KEBLE_BALL_ENV', 'DEVELOPMENT'))

@app.route('/')
def index():
    raise NotImplementedError

@app.route('/environ')
def dump_environ():
    x = os.environ
    return str(x)

if __name__ == '__main__':
    app.run()
