# coding: utf-8
"""
user.py

Contains User class
"""

import re

from flask import flash
from flask import url_for
from flask.ext.bcrypt import Bcrypt

from kebleball import app
from kebleball import helpers
from kebleball.database import DB
from kebleball.database import *

APP = app.APP

BCRYPT = Bcrypt(APP)

class User(DB.Model):
    id = DB.Column(
        DB.Integer,
        primary_key=True,
        nullable=False
    )
    email = DB.Column(
        DB.String(120),
        unique=True,
        nullable=False
    )
    newemail = DB.Column(
        DB.String(120),
        unique=True,
        nullable=True
    )
    passhash = DB.Column(
        DB.BINARY(60),
        nullable=False
    )
    firstname = DB.Column(
        DB.String(120),
        nullable=False
    )
    surname = DB.Column(
        DB.String(120),
        nullable=False
    )
    fullname = DB.column_property(firstname + " " + surname)
    phone = DB.Column(
        DB.String(20),
        nullable=False
    )
    secretkey = DB.Column(
        DB.String(64),
        nullable=True
    )
    secretkeyexpiry = DB.Column(
        DB.DateTime(),
        nullable=True
    )
    verified = DB.Column(
        DB.Boolean,
        default=False,
        nullable=False
    )
    deleted = DB.Column(
        DB.Boolean,
        default=False,
        nullable=False
    )
    note = DB.Column(
        DB.Text,
        nullable=True
    )
    role = DB.Column(
        DB.Enum(
            'User',
            'Admin'
        ),
        nullable=False
    )

    college_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('college.id'),
        nullable=False
    )
    college = DB.relationship(
        'College',
        backref=DB.backref(
            'users',
            lazy='dynamic'
        )
    )

    affiliation_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('affiliation.id'),
        nullable=False
    )
    affiliation = DB.relationship(
        'Affiliation',
        backref=DB.backref(
            'users',
            lazy='dynamic'
        )
    )

    battels_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('battels.id'),
        nullable=True
    )
    battels = DB.relationship(
        'Battels',
        backref=DB.backref(
            'user',
            uselist=False
        )
    )

    affiliation_verified = DB.Column(
        DB.Boolean,
        default=None,
        nullable=True
    )

    def __init__(self, email, password, firstname,
                 surname, phone, college, affiliation):
        self.email = email
        self.passhash = BCRYPT.generate_password_hash(password)
        self.firstname = firstname
        self.surname = surname
        self.phone = phone
        self.secretkey = helpers.generate_key(64)
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

        self.battels = Battels.query.filter(Battels.email == email).first()

    def __repr__(self):
        return "<User {0}: {1} {2}>".format(
            self.id, self.firstname, self.surname)

    def check_password(self, candidate):
        return bcrypt.check_password_hash(self.passhash, candidate)

    def set_password(self, password):
        self.passhash = BCRYPT.generate_password_hash(password)

    def has_tickets(self):
        return len([x for x in self.tickets
                    if not x.cancelled]) > 0

    def has_uncollected_tickets(self):
        return len([x for x in self.tickets
                    if not x.cancelled and not x.collected]) > 0

    def has_collected_tickets(self):
        return len([x for x in self.tickets
                    if not x.cancelled and x.collected]) > 0

    def has_unresold_tickets(self):
        return len([x for x in self.tickets
                    if not x.cancelled and x.resalekey is None]) > 0

    def is_reselling_tickets(self):
        return len([x for x in self.tickets
                    if x.resalekey is not None]) > 0

    def has_unpaid_tickets(self, method=None):
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

    def has_paid_tickets(self, method=None):
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

    def is_admin(self):
        return self.role == 'Admin'

    def is_waiting(self):
        return self.waiting.count() > 0

    def waiting_for(self):
        return sum([x.waitingfor for x in self.waiting])

    def can_pay_by_battels(self):
        return (
            self.battels is not None and
            APP.config['CURRENT_TERM'] != 'TT'
        )

    def gets_discount(self):
        return (
            self.college.name == "Keble" and
            self.affiliation.name == "Student" and
            APP.config['KEBLE_DISCOUNT'] > 0 and
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
        user = User.query.filter(User.id == int(id)).first()

        if not user:
            return None

        return user

    @staticmethod
    def get_by_email(email):
        user = User.query.filter(User.email == email).first()

        if not user:
            return None

        return user

    def verify_affiliation(self):
        self.affiliation_verified = True

        APP.email_manager.sendTemplate(
            self.email,
            "Affiliation Verified - Buy Your Tickets Now!",
            "affiliation_verified.email",
            url=url_for('purchase.purchaseHome', _external=True)
        )

        DB.session.commit()

    def deny_affiliation(self):
        self.affiliation_verified = False

        DB.session.commit()

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
                not helpers.get_boolean_config('TICKETS_ON_SALE')
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
                DB.session.commit()
                return

            APP.email_manager.sendTemplate(
                APP.config['TICKETS_EMAIL'],
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
            DB.session.add(self.battels)

        DB.session.commit()

    def get_base_ticket_price(self):
        if (
                self.college.name == "Keble" and
                self.affiliation.name == "Staff/Fellow"
        ):
            return APP.config["KEBLE_STAFF_TICKET_PRICE"]
        else:
            return APP.config["TICKET_PRICE"]
