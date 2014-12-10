# coding: utf-8
"""
announcement.py

Contains Announcement class
Used to store announcements displayed on site and emailed
"""

from kebleball.app import app
from kebleball.database import db
from kebleball.database.user import User
from kebleball.database.college import College
from kebleball.database.affiliation import Affiliation
from email.mime.text import MIMEText
from datetime import datetime

USER_ANNOUNCE_LINK = db.Table(
    'user_announce_link',
    db.Model.metadata,
    db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('user.id')
    ),
    db.Column(
        'announcement_id',
        db.Integer,
        db.ForeignKey('announcement.id')
    )
)

EMAIL_ANNOUNCE_LINK = db.Table(
    'email_announce_link',
    db.Model.metadata,
    db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('user.id')
    ),
    db.Column(
        'announcement_id',
        db.Integer,
        db.ForeignKey('announcement.id')
    )
)

class Announcement(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True,
        nullable=False
    )
    timestamp = db.Column(
        db.DateTime(),
        nullable=False
    )
    content = db.Column(
        db.Text(65536),
        nullable=False
    )
    subject = db.Column(
        db.Text(256),
        nullable=False
    )
    send_email = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )
    email_sent = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    sender_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )
    sender = db.relationship(
        'User',
        backref=db.backref(
            'announcements-sent',
            lazy='dynamic'
        )
    )

    college_id = db.Column(
        db.Integer,
        db.ForeignKey('college.id'),
        nullable=True
    )
    college = db.relationship(
        'College',
        backref=db.backref(
            'announcements',
            lazy='dynamic'
        )
    )

    affiliation_id = db.Column(
        db.Integer,
        db.ForeignKey('affiliation.id'),
        nullable=True
    )
    affiliation = db.relationship(
        'Affiliation',
        backref=db.backref(
            'announcements-received',
            lazy='dynamic'
        )
    )

    is_waiting = db.Column(
        db.Boolean,
        nullable=True
    )
    has_tickets = db.Column(
        db.Boolean,
        nullable=True
    )
    has_collected = db.Column(
        db.Boolean,
        nullable=True
    )
    has_uncollected = db.Column(
        db.Boolean,
        nullable=True
    )

    users = db.relationship(
        'User',
        secondary=USER_ANNOUNCE_LINK,
        backref='announcements'
    )

    emails = db.relationship(
        'User',
        secondary=EMAIL_ANNOUNCE_LINK,
        lazy='dynamic'
    )

    def __init__(self,
                 subject,
                 content,
                 sender,
                 send_email,
                 college=None,
                 affiliation=None,
                 has_tickets=None,
                 is_waiting=None,
                 has_collected=None,
                 has_uncollected=None):
        self.timestamp = datetime.utcnow()
        self.subject = subject
        self.content = content
        self.send_email = send_email
        self.has_tickets = has_tickets
        self.is_waiting = is_waiting
        self.has_collected = has_collected
        self.has_uncollected = has_uncollected

        if hasattr(sender, 'id'):
            self.sender_id = sender.id
        else:
            self.sender_id = sender

        if hasattr(college, 'id'):
            self.college_id = college.id
        else:
            self.college_id = college

        if hasattr(affiliation, 'id'):
            self.affiliation_id = affiliation.id
        else:
            self.affiliation_id = affiliation

        query = User.query

        if self.college_id is not None:
            query = query.filter(User.college_id == self.college_id)

        if self.affiliation_id is not None:
            query = query.filter(User.affiliation_id == self.affiliation_id)

        for user in query.all():
            if (
                    (
                        self.has_tickets is None or
                        user.has_tickets() == self.has_tickets
                    ) and
                    (
                        self.is_waiting is None or
                        user.is_waiting() == self.is_waiting
                    ) and
                    (
                        self.has_collected is None or
                        user.has_collected_tickets() == self.has_collected
                    ) and
                    (
                        self.has_uncollected is None or
                        user.has_uncollected_tickets() == self.has_uncollected
                    )
            ):
                self.users.append(user)
                if send_email:
                    self.emails.append(user)

    def __repr__(self):
        return "<Announcement {0}: {1}>".format(self.id, self.subject)

    def send_emails(self, count):
        try:
            msg = MIMEText(self.content)
            msg['Subject'] = self.subject
            msg['From'] = self.sender.email

            for user in self.emails:
                if count <= 0:
                    break
                try:
                    msg.replace_header('To', user.email)
                except KeyError:
                    msg['To'] = user.email
                app.email_manager.sendMsg(msg)
                self.emails.remove(user)
                count = count - 1
        finally:
            db.session.commit()
            self.email_sent = (self.emails.count() == 0)
            db.session.commit()

        return count

    @staticmethod
    def get_by_id(id):
        announcement = Announcement.query.filter(
            Announcement.id == int(id)).first()

        if not announcement:
            return None

        return announcement
