# coding: utf-8
from flask.ext.login import LoginManager
from kebleball.database.user import User

loginManager = LoginManager()

@loginManager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

loginManager.login_view = "front.home"

loginManager.session_protection = "strong"