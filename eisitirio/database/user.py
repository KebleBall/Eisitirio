# coding: utf-8
"""Database model for users."""

from __future__ import unicode_literals

from flask.ext import bcrypt

from eisitirio import app
from eisitirio.database import battels
from eisitirio.database import db
from eisitirio.database import photo as photo_model # pylint: disable=unused-import
from eisitirio.helpers import util

DB = db.DB
APP = app.APP

BCRYPT = bcrypt.Bcrypt(APP)

class User(DB.Model):
    """Model for users."""
    __tablename__ = 'user'

    # Class level properties for Flask-Login
    #
    # Sessions don't expire, and no users are anonymous, so these can be hard
    # coded
    is_authenticated = True
    is_anonymous = False

    email = DB.Column(
        DB.Unicode(120),
        unique=True,
        nullable=False
    )
    new_email = DB.Column(
        DB.Unicode(120),
        unique=True,
        nullable=True
    )
    password_hash = DB.Column(
        DB.BINARY(60),
        nullable=False
    )
    forenames = DB.Column(
        DB.Unicode(120),
        nullable=False
    )
    surname = DB.Column(
        DB.Unicode(120),
        nullable=False
    )
    full_name = DB.column_property(forenames + ' ' + surname)
    phone = DB.Column(
        DB.Unicode(20),
        nullable=False
    )
    secret_key = DB.Column(
        DB.Unicode(64),
        nullable=True
    )
    secret_key_expiry = DB.Column(
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
        DB.UnicodeText,
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
        DB.ForeignKey('college.object_id'),
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
        DB.ForeignKey('affiliation.object_id'),
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
        DB.ForeignKey('battels.object_id'),
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

    photo_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('photo.object_id'),
        nullable=True
    )
    photo = DB.relationship(
        'Photo',
        backref=DB.backref(
            'user',
            uselist=False
        )
    )

    def __init__(self, email, password, forenames, surname, phone, college,
                 affiliation, photo):
        self.email = email
        self.forenames = forenames
        self.surname = surname
        self.phone = phone
        self.college = college
        self.affiliation = affiliation
        self.photo = photo

        self.set_password(password)

        self.secret_key = util.generate_key(64)
        self.verified = False
        self.deleted = False
        self.role = 'User'
        self.affiliation_verified = None

        self.battels = battels.Battels.query.filter(
            battels.Battels.email == email
        ).first()

    def __repr__(self):
        return '<User {0}: {1} {2}>'.format(
            self.object_id, self.forenames, self.surname)

    def check_password(self, candidate):
        """Check if a password matches the hash stored for the user.

        Runs the bcrypt.Bcrypt checking routine to validate the password.

        Args:
            candidate: (str) the candidate password

        Returns:
            (bool) whether the candidate password matches the stored hash
        """
        return BCRYPT.check_password_hash(self.password_hash, candidate)

    def set_password(self, password):
        """Set the password for the user.

        Hashes the password using bcrypt and stores the resulting hash.

        Args:
            password: (str) new password for the user.
        """
        self.password_hash = BCRYPT.generate_password_hash(password)

    def promote(self):
        """Make the user an admin."""
        self.role = 'Admin'

    def demote(self):
        """Make the user an ordinary user (no admin privileges)"""
        self.role = 'User'

    @property
    def is_admin(self):
        """Check if the user is an admin"""
        return self.role == 'Admin'

    @property
    def is_waiting(self):
        """Is the user on the waiting list?"""
        return self.waiting.count() > 0

    def waiting_for(self):
        """How many tickets is the user waiting for?"""
        return sum([x.waiting_for for x in self.waiting])

    @property
    def is_verified(self):
        """Has the user's email address been verified?"""
        return self.verified

    @property
    def is_deleted(self):
        """Has the user been deleted?

        In order to maintain referential integrity, when a user is deleted we
        scrub their personal details, but maintain the user object referenced by
        log entries, tickets, transactions etc.
        """
        return self.deleted

    @property
    def is_active(self):
        """Is the user active?

        This method is specifically for the use of the Flask-Login extension,
        and refers to whether the user can log in.
        """
        return self.is_verified and not self.is_deleted

    def get_id(self):
        """What is this user's ID?

        This method is specifically for the use of the Flask-Login extension,
        and is a defined class method which returns a unique identifier for the
        user, in this case their database ID.
        """
        return unicode(self.object_id)

    @staticmethod
    def get_by_email(email):
        """Get a user object by the user's email address."""
        user = User.query.filter(User.email == email).first()

        if not user:
            return None

        return user

    def add_manual_battels(self):
        """Manually add a battels account for the user

        If we don't have a battels account automatically matched to the user,
        the admin can manually create one for them.
        """
        self.battels = battels.Battels.query.filter(
            battels.Battels.email == self.email
        ).first()

        if not self.battels:
            self.battels = battels.Battels(None, self.email, None,
                                           self.forenames, self.surname, True)
            DB.session.add(self.battels)

        DB.session.commit()

    @staticmethod
    def write_csv_header(csv_writer):
        csv_writer.writerow([
            'User ID',
            'Email',
            'Forenames',
            'Surname',
            'Phone Number',
            'Notes',
            'Role',
            'College',
            'Affiliation',
            'Battels ID',
        ])

    def write_csv_row(self, csv_writer):
        csv_writer.writerow([
            self.object_id,
            self.email,
            self.forenames,
            self.surname,
            self.phone,
            self.note,
            self.role,
            self.college.name,
            self.affiliation.name,
            self.battels.battels_id if self.battels is not None else 'N/A',
        ])
