from flask import Blueprint

front = Blueprint('front', __name__)

@front.route('/home')
def home():
    # [todo] - Add homepage
    raise NotImplementedError('homepage')

@front.route('/login')
def login():
    # [todo] - Add login
    raise NotImplementedError('login')

@front.route('/register')
def register():
    # [todo] - Add register
    raise NotImplementedError('register')

@front.route('/terms')
def terms():
    # [todo] - Add terms
    raise NotImplementedError('terms')

@front.route('/passwordreset')
def passwordReset():
    # [todo] - Add passwordReset
    raise NotImplementedError('passwordReset')

@front.route('/confirmemail')
def confirmEmail():
    # [todo] - Add confirmEmail
    raise NotImplementedError('confirmEmail')

@front.route('/logout')
def logout():
    # [todo] - Add logout
    raise NotImplementedError('logout')