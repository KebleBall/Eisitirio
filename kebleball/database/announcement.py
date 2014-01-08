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

user_announce_link = db.Table(
    'user_announce_link',
    db.Model.metadata,
    db.Column('user_id',
        db.Integer,
        db.ForeignKey('user.id')
    ),
    db.Column('announcement_id',
        db.Integer,
        db.ForeignKey('announcement.id')
    )
)

email_announce_link = db.Table(
    'email_announce_link',
    db.Model.metadata,
    db.Column('user_id',
        db.Integer,
        db.ForeignKey('user.id')
    ),
    db.Column('announcement_id',
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
    time = db.Column(
        db.String(50),
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

    users = db.relationship(
        'User',
        secondary=user_announce_link,
        backref='announcements'
    )

    emails = db.relationship(
        'User',
        secondary=email_announce_link
    )

    def __init__(self,
                 subject,
                 content,
                 sender,
                 send_email,
                 college=None,
                 has_tickets=None,
                 affiliation=None,
                 is_waiting=None,
                 has_collected=None):
        self.time = datetime.now()
        self.subject = subject
        self.content = content
        self.has_tickets = has_tickets
        self.is_waiting = is_waiting
        self.has_collected = has_collected

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
            query = query.filter(User.college_id==self.college_id)

        if self.affiliation_id is not None:
            query = query.filter(User.affiliation_id==self.affiliation_id)

        for user in query.all():
            if (
                (
                    self.has_tickets is None or
                    user.hasTickets()==self.has_tickets
                ) and
                (
                    self.is_waiting is None or
                    user.isWaiting()==self.is_waiting
                ) and
                (
                    self.has_collected is None or
                    user.hasCollected()==self.has_collected
                )
            ):
                self.users.append(user)
                self.emails.append(user)

    def __repr__(self):
        return "<Announcement {0}: {1}>".format(self.id, self.subject)

    def sendEmails(self, count):
        try:
            msg = MIMEText(self.content)
            msg['Subject'] = self.subject
            msg['From'] = self.sender.email

            for user in self.emails:
                if count <= 0:
                    break
                msg['To'] = user.email
                app.email_manager.sendMsg(msg)
                self.emails.remove(user)

            self.email_sent = (len(self.emails) == 0)
        finally:
            db.session.commit()

        return count

    @staticmethod
    def get_by_id(id):
        return Announcement.query.filter(Announcement.id==id).first()