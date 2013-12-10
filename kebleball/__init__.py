from flask import Flask, url_for, redirect

app = Flask(__name__)

from flask.ext.login import current_user
from os import getenv
from .views import *
from .helpers import *

app.config.from_pyfile('config/default.py')

if getenv('KEBLE_BALL_ENV', 'DEVELOPMENT') == 'PRODUCTION':
    app.config.from_pyfile('config/production.py')
else:
    app.config.from_pyfile('config/development.py')

app.register_blueprint(admin.admin)
app.register_blueprint(ajax.ajax)
app.register_blueprint(dashboard.dashboard)
app.register_blueprint(front.front)
app.register_blueprint(purchase.purchase)

login_manager.loginManager.init_app(app)

@app.route('/hello')
def hello_world():
    # [review] - Remove this!
    return ('Hello World! I am the Keble Ball Ticketing System, '
        'running in the {0} environment').format(getenv('KEBLE_BALL_ENV', 'DEVELOPMENT'))

@app.route('/')
def router():
    if current_user is not None:
        return redirect(url_for('dashboard.dashboardHome'))
    else:
        return redirect(url_for('front.home'))

@app.errorhandler(404)
def error404():
    # [todo] - Add error404
    raise NotImplementedError('error404')

@app.errorhandler(500)
def error500():
    # [todo] - Add error500
    raise NotImplementedError('error500')

@app.context_processor
def utility_processor():
    def get_all(query):
        return query.all()
    return dict(get_all=get_all)

if __name__ == '__main__':
    app.run()
