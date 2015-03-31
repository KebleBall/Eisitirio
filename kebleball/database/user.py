# coding: utf-8
"""
user.py

Contains User class
"""

from flask import flash
from flask import url_for
from flask.ext.bcrypt import Bcrypt

from kebleball import app
from kebleball import helpers
from kebleball.database import db
from kebleball.database import battels
from kebleball.database import affiliation

DB = db.DB
APP = app.APP

BCRYPT = Bcrypt(APP)

class User(DB.Model):
    """Database model for users."""
    object_id = DB.Column(
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

    def __init__(self, email, password, firstname,
                 surname, phone, college, affiliation):
        self.email = email
        self.set_password(password)
        self.firstname = firstname
        self.surname = surname
        self.phone = phone
        self.secretkey = helpers.generate_key(64)
        self.verified = False
        self.deleted = False
        self.role = 'User'
        self.affiliation_verified = None

        if hasattr(college, 'object_id'):
            self.college_id = college.object_id
        else:
            self.college_id = college

        if hasattr(affiliation, 'object_id'):
            self.affiliation_id = affiliation.object_id
        else:
            self.affiliation_id = affiliation

        self.battels = battels.Battels.query.filter(
            battels.Battels.email == email
        ).first()

    def __repr__(self):
        return "<User {0}: {1} {2}>".format(
            self.object_id, self.firstname, self.surname)

    def check_password(self, candidate):
        """Check if a password matches the hash stored for the user.

        Runs the Bcrypt checking routine to validate the password.

        Args:
            candidate: (str) the candidate password

        Returns:
            (bool) whether the candidate password matches the stored hash
        """
        return BCRYPT.check_password_hash(self.passhash, candidate)

    def set_password(self, password):
        """Set the password for the user.

        Hashes the password using bcrrypt and stores the resulting hash.

        Args:
            password: (str) new password for the user.
        """
        self.passhash = BCRYPT.generate_password_hash(password)

    def has_tickets(self):
        """Does the user have any tickets?"""
        return len([x for x in self.tickets
                    if not x.cancelled]) > 0

    def has_uncollected_tickets(self):
        """Does the user have any uncollected tickets?"""
        return len([x for x in self.tickets
                    if not x.cancelled and not x.collected]) > 0

    def has_collected_tickets(self):
        """Has the user collected any tickets?"""
        return len([x for x in self.tickets
                    if not x.cancelled and x.collected]) > 0

    def has_unresold_tickets(self):
        """Has the user got any tickets they can resell?"""
        return len([x for x in self.tickets
                    if not x.cancelled and x.resalekey is None]) > 0

    def is_reselling_tickets(self):
        """Is the user currently in the process of reslling tickets?"""
        return len([x for x in self.tickets
                    if x.resalekey is not None]) > 0

    def has_unpaid_tickets(self, method=None):
        """Does the user have any unpaid tickets?

        Checks if the user has tickets which they haven't yet paid for,
        potentially filtered by payment method.

        Args:
            method: (str) payment method to search for unpaid tickets by

        Returns:
            (bool) whether there are any tickets owned by the user (and with
            the given payment method set if given) which have not been paid for
        """
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
        """Does the user have any unpaid tickets?

        Checks if the user has tickets which they have paid for, potentially
        filtered by payment method.

        Args:
            method: (str) payment method to search for paid tickets by

        Returns:
            (bool) whether there are any tickets owned by the user (and with
            the given payment method set if given) which have been paid for
        """
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
        """Make the user an admin."""
        self.role = 'Admin'

    def demote(self):
        """Make the user an ordinary user (no admin privileges)"""
        self.role = 'User'

    def is_admin(self):
        """Check if the user is an admin"""
        return self.role == 'Admin'

    def is_waiting(self):
        """Is the user on the waiting list?"""
        return self.waiting.count() > 0

    def waiting_for(self):
        """How many tickets is the user waiting for?"""
        return sum([x.waitingfor for x in self.waiting])

    def can_pay_by_battels(self):
        """Is the user able to pay by battels?

        The requirement for this is that the user is a current Keble member, and
        that it is either Michaelmas or Hilary term. The logic determining
        whether the user is a current Keble member is carried out at
        registration (and based on whether their email matches one in our list
        of battelable emails). Alternately, this can be forced by an admin
        through the admin interface if the user is not automatically recognised.
        Given this, it suffices to only check if the user has a defined battels
        account on the system.
        """
        return (
            self.battels is not None and
            APP.config['CURRENT_TERM'] != 'TT'
        )

    def gets_discount(self):
        """Does the user get a discount?

        Discounts are given on the first ticket a current Keble student
        purchases during the limited release.
        """
        return (
            self.college.name == "Keble" and
            self.affiliation.name == "Student" and
            APP.config['KEBLE_DISCOUNT'] > 0 and
            not APP.config['TICKETS_ON_SALE'] and
            self.tickets.filter_by(cancelled=False).count() == 0
        )

    def is_verified(self):
        """Has the user's email address been verified?"""
        return self.verified

    def is_deleted(self):
        """Has the user been deleted?

        In order to maintain referential integrity, when a user is deleted we
        scrub their personal details, but maintain the user object referenced by
        log entries, tickets, transactions etc.
        """
        return self.deleted

    def is_active(self):
        """Is the user active?

        This method is specifically for the use of the Flask-Login extension,
        and refers to whether the user can log in.
        """
        return self.is_verified() and not self.is_deleted()

    def is_authenticated(self):
        """Is the user authenticated?

        This method is specifically for the use of the Flask-Login extension,
        and refers to whether the user is logged in. Because our login state has
        no concept of session expiry, so long as we have a user object in the
        session, that user is logged in, therefore we always return True.
        """
        return True

    def is_anonymous(self):
        """Is the user anonymous?

        This method is specifically for the use of the Flask-Login extension,
        and refers to whether the user is identified. Because this system has no
        use for anonymous users, we require that every user object be
        non-anonymous, and so we always return False.
        """
        return False

    def get_id(self):
        """What is this user's ID?

        This method is specifically for the use of the Flask-Login extension,
        and is a defined class method which returns a unique identifier for the
        user, in this case their database ID.
        """
        return unicode(self.object_id)

    @staticmethod
    def get_by_id(object_id):
        """Get a user object by its database ID."""
        user = User.query.filter(User.object_id == int(object_id)).first()

        if not user:
            return None

        return user

    @staticmethod
    def get_by_email(email):
        """Get a user object by the user's email address."""
        user = User.query.filter(User.email == email).first()

        if not user:
            return None

        return user

    def verify_affiliation(self):
        """Mark the users affiliation as verified.

        For limited release, we require that the user's affiliation is verified.
        For current members with known battels accounts, this is done
        automatically, but for graduands, fellows, staff members etc an admin
        must manually check and approve them. This method is called when the
        affiliation is approved, and updates a flag before sending an email to
        the user reminding them to buy tickets.
        """
        self.affiliation_verified = True

        APP.email_manager.sendTemplate(
            self.email,
            "Affiliation Verified - Buy Your Tickets Now!",
            "affiliation_verified.email",
            url=url_for('purchase.purchaseHome', _external=True)
        )

        DB.session.commit()

    def deny_affiliation(self):
        """Mark the users affiliation as invalid.

        For limited release, we require that the user's affiliation is verified.
        For current members with known battels accounts, this is done
        automatically, but for graduands, fellows, staff members etc an admin
        must manually check and approve them. This method is called when the
        affiliation is rejected, and updates a flag accordingly.
        """
        self.affiliation_verified = False

        DB.session.commit()

    def update_affiliation(self, new_affiliation):
        """Change the users affiliation.

        In order to maintain the verification of users' affiliations, when we
        update an affiliation we must re-submit it for verification as
        appropriate.
        """
        old_affiliation = self.affiliation

        if hasattr(affiliation, 'object_id'):
            self.affiliation_id = affiliation.object_id
        else:
            self.affiliation_id = new_affiliation
            new_affiliation = affiliation.Affiliation.get_by_id(new_affiliation)

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
        """Check if a user's affiliation can be verified

        Checks if a user's affiliation can be verified automatically, and
        otherwise sends an email to the ball ticketing officer to ask them to
        verify it manually
        """
        if (
                self.affiliation_verified is None and
                not APP.config['TICKETS_ON_SALE']
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
        """Manually add a battels account for the user

        If we don't have a battels account automatically matched to the user,
        the admin can manually create one for them.
        """
        self.battels = battels.Battels.query.filter(
            battels.Battels.email == self.email
        ).first()

        if not self.battels:
            self.battels = battels.Battels(None, self.email, None,
                                           self.firstname, self.surname, True)
            DB.session.add(self.battels)

        DB.session.commit()

    def get_base_ticket_price(self):
        """What is the basic price for tickets this user purchases?

        During limited release, current staff members and fellows get a
        discounted ticket price. We checkif the user is affiliated with Keble as
        a staff member/fellow or not, and return the appropriate ticket price
        from the config"""
        if (
                self.college.name == "Keble" and
                self.affiliation.name == "Staff/Fellow" and
                not app.config['TICKETS_ON_SALE']
        ):
            return APP.config["KEBLE_STAFF_TICKET_PRICE"]
        else:
            return APP.config["TICKET_PRICE"]
