# coding: utf-8
"""
user.py

Contains User class
"""

import re

from flask import flash
from flask import url_for
from flask.ext.bcrypt import Bcrypt

from kebleball.app import app
from kebleball.database import db
from kebleball.database.affiliation import Affiliation
from kebleball.database.battels import Battels
from kebleball.database.college import College
from kebleball.helpers import generate_key
from kebleball.helpers import get_boolean_config

bcrypt = Bcrypt(app)

class User(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True,
        nullable=False
    )
    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )
    newemail = db.Column(
        db.String(120),
        unique=True,
        nullable=True
    )
    passhash = db.Column(
        db.BINARY(60),
        nullable=False
    )
    firstname = db.Column(
        db.String(120),
        nullable=False
    )
    surname = db.Column(
        db.String(120),
        nullable=False
    )
    fullname = db.column_property(firstname + " " + surname)
    phone = db.Column(
        db.String(20),
        nullable=False
    )
    secretkey = db.Column(
        db.String(64),
        nullable=True
    )
    secretkeyexpiry = db.Column(
        db.DateTime(),
        nullable=True
    )
    verified = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )
    deleted = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )
    note = db.Column(
        db.Text,
        nullable=True
    )
    role = db.Column(
        db.Enum(
            'User',
            'Admin'
        ),
        nullable=False
    )

    college_id = db.Column(
        db.Integer,
        db.ForeignKey('college.id'),
        nullable=False
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
        db.ForeignKey('affiliation.id'),
        nullable=False
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
            uselist=False
        )
    )

    affiliation_verified = db.Column(
        db.Boolean,
        default=None,
        nullable=True
    )

    def __init__(self, email, password, firstname, surname, phone, college, affiliation):
        self.email = email
        self.passhash = bcrypt.generate_password_hash(password)
        self.firstname = firstname
        self.surname = surname
        self.phone = phone
        self.secretkey = generate_key(64)
        self.verified = False
        self.deleted = False
        self.role = 'User'
        self.affiliation_verified = None

        if hasattr(college, 'id'):
            self.college_id = college.id
        else:
            self.college_id = college

        if hasattr(affiliation, 'id'):
            self.affiliation_id = affiliation.id
        else:
            self.affiliation_id = affiliation

        self.battels = Battels.query.filter(Battels.email==email).first()

    def __repr__(self):
        return "<User {0}: {1} {2}>".format(self.id, self.firstname, self.surname)

    def checkPassword(self, candidate):
        return bcrypt.check_password_hash(self.passhash, candidate)

    def setPassword(self, password):
        self.passhash = bcrypt.generate_password_hash(password)

    def hasTickets(self):
        return len([x for x in self.tickets if not x.cancelled]) > 0

    def hasUncollectedTickets(self):
        return len([x for x in self.tickets if not x.cancelled and not x.collected]) > 0

    def hasCollectedTickets(self):
        return len([x for x in self.tickets if not x.cancelled and x.collected]) > 0

    def hasUnresoldTickets(self):
        return len([x for x in self.tickets if not x.cancelled and x.resalekey is None]) > 0

    def isResellingTickets(self):
        return len([x for x in self.tickets if x.resalekey is not None]) > 0

    def hasUnpaidTickets(self, method=None):
        if method is None:
            return len(
                [
                    x for x in self.tickets if (
                        not x.paid and
                        not x.cancelled
                    )
                ]
            ) > 0
        else:
            return len(
                [
                    x for x in self.tickets if (
                        x.paymentmethod == method and
                        not x.paid and
                        not x.cancelled
                    )
                ]
            ) > 0

    def hasPaidTickets(self, method=None):
        if method is None:
            return len(
                [
                    x for x in self.tickets if (
                        x.paid and
                        not x.cancelled
                    )
                ]
            ) > 0
        else:
            return len(
                [
                    x for x in self.tickets if (
                        x.paymentmethod == method and
                        x.paid and
                        not x.cancelled
                    )
                ]
            ) > 0

    def promote(self):
        self.role = 'Admin'

    def demote(self):
        self.role = 'User'

    def isAdmin(self):
        return self.role=='Admin'

    def isWaiting(self):
        return self.waiting.count() > 0

    def waitingFor(self):
        return sum([x.waitingfor for x in self.waiting])

    def canPayByBattels(self):
        return (
            self.battels is not None and
            app.config['CURRENT_TERM'] != 'TT'
        )

    def getsDiscount(self):
        return (
            self.college.name == "Keble" and
            self.affiliation.name == "Student" and
            app.config['KEBLE_DISCOUNT'] > 0 and
            self.tickets.count() == 0
        )

    def is_verified(self):
        return self.verified

    def is_deleted(self):
        return self.deleted

    def is_active(self):
        return self.is_verified() and not self.is_deleted()

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

    def verify_affiliation(self):
        self.affiliation_verified = True

        app.email_manager.sendTemplate(
            self.email,
            "Affiliation Verified - Buy Your Tickets Now!",
            "affiliation_verified.email",
            url=url_for('purchase.purchaseHome', _external=True)
        )

        db.session.commit()

    def deny_affiliation(self):
        self.affiliation_verified = False

        db.session.commit()

    def update_affiliation(self, affiliation):
        old_affiliation = self.affiliation

        if hasattr(affiliation, 'id'):
            self.affiliation_id = affiliation.id
            new_affiliation = affiliation
        else:
            self.affiliation_id = affiliation
            new_affiliation = Affiliation.get_by_id(affiliation)

        if (
                old_affiliation != new_affiliation and
                self.college.name == "Keble" and
                new_affiliation.name not in [
                    "Other",
                    "None",
                    "Graduate/Alumnus"
                ]
        ):
            self.affiliation_verified = None

    def maybe_verify_affiliation(self):
        if (
                self.affiliation_verified is None and
                not get_boolean_config('TICKETS_ON_SALE')
        ):
            if (
                    self.college.name != "Keble" or
                    self.affiliation.name in [
                        "Other",
                        "None",
                        "Graduate/Alumnus"
                    ] or
                    (
                        self.affiliation.name == "Student" and
                        self.battels_id is not None
                    )
            ):
                self.affiliation_verified = True
                db.session.commit()
                return

            app.email_manager.sendTemplate(
                app.config['TICKETS_EMAIL'],
                "Verify Affiliation",
                "verify_affiliation.email",
                user=self,
                url=url_for('admin.verify_affiliations', _external=True)
            )
            flash(
                (
                    u'Your affiliation must be verified before you will be '
                    u'able to purchase tickets. You will receive an email when '
                    u'your status has been verified.'
                ),
                u'info'
            )

    def add_manual_battels(self):
        self.battels = Battels.query.filter(Battels.email==self.email).first()

        if not self.battels:
            self.battels = Battels(None, self.email, None, self.firstname,
                                   self.surname, True)
            db.session.add(self.battels)

        db.session.commit()

    def get_base_ticket_price(self):
        if (
                self.college.name == "Keble" and
                self.affiliation.name == "Staff/Fellow"
        ):
            return app.config["KEBLE_STAFF_TICKET_PRICE"]
        else:
            return app.config["TICKET_PRICE"]
