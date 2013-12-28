"""
user.py

Contains User class
"""

from kebleball.database import db
from kebleball.database.battels import Battels
from kebleball.database.college import College
from kebleball.database.affiliation import Affiliation
from kebleball.app import app
from flask.ext.bcrypt import Bcrypt
from kebleball.helpers import generate_key

from datetime import datetime
import re

bcrypt = Bcrypt(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    passhash = db.Column(db.BINARY(60), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    secretkey = db.Column(db.String(64), nullable=True)
    secretkeyexpiry = db.Column(db.DateTime(), nullable=True)
    verified = db.Column(db.Boolean, nullable=False)
    deleted = db.Column(db.Boolean, nullable=False)
    note = db.Column(db.Text, nullable=True)
    role = db.Column(db.Enum('User', 'Admin'), nullable=False)

    college_id = db.Column(
        db.Integer,
        db.ForeignKey('college.id'),
        nullable=True
    )
    college = db.relationship(
        'College',
        backref=db.backref(
            'users',
            lazy='dynamic'
        )
    )

    affiliation_id = db.Column(
        db.Integer,
        db.ForeignKey('affiliation.id')
    )
    affiliation = db.relationship(
        'Affiliation',
        backref=db.backref(
            'users',
            lazy='dynamic'
        )
    )

    battels_id = db.Column(
        db.Integer,
        db.ForeignKey('battels.id'),
        nullable=True
    )
    battels = db.relationship(
        'Battels',
        backref=db.backref(
            'user',
            lazy='dynamic'
        )
    )

    def __init__(self, email, password, name, phone, college, affiliation):
        self.email = email
        self.passhash = bcrypt.generate_password_hash(password)
        self.name = name
        self.phone = phone
        self.secretkey = generate_key(64)
        self.verified = False
        self.deleted = False
        self.role = 'User'

        if isinstance(college, College):
            self.college = college
        else:
            self.college_id = college

        if isinstance(affiliation, Affiliation):
            self.affiliation = affiliation
        else:
            self.affiliation_id = affiliation

        battels = Battels.query.filter(Battels.email==email).first()

        if battels is not None:
            self.battels = battels
        elif re.match('(.*?)@keble\.ox\.ac\.uk$',email) is not None:
            self.battels = Battels(None, None, True)
            db.session.add(self.battels)
        else:
            self.battels = None

    def __repr__(self):
        return "<User {id}: {name}>".format_map(vars(self))

    def checkPassword(self, candidate):
        return bcrypt.check_password_hash(self.passhash, candidate)

    def setPassword(self, password):
        self.passhash = bcrypt.generate_password_hash(password)

    def hasTickets(self):
        return len(self.tickets) > 0

    def hasUncollectedTickets(self):
        return len([x for x in self.tickets if x.collected]) > 0

    def promote(self):
        self.role = 'Admin'

    def demote(self):
        self.role = 'User'

    def isAdmin(self):
        return self.role=='Admin'

    def isWaiting(self):
        return len(self.waiting) > 0

    def waitingFor(self):
        return sum([x.num for x in self.waiting])

    def canPayByBattels(self):
        return self.battels is not None

    def is_verified(self):
        return self.verified

    def is_deleted(self):
        return self.deleted

    def is_active(self):
        return is_verified() and not is_deleted()

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    @staticmethod
    def get_by_id(id):
        user = User.query.filter(User.id==int(id)).first()

        if not user:
            return None

        return user

    @staticmethod
    def get_by_email(email):
        user = User.query.filter(User.email==email).first()

        if not user:
            return None

        return user

    def delete(self):
        # [todo] - Implement user.delete

        raise NotImplementedError