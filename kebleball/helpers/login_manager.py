from flask.ext.login import LoginManager
from kebleball.database import User

loginManager = LoginManager()

@loginManager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

loginManager.login_view = "front.login"

loginManager.session_protection = "strong"