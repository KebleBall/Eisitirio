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
import smtplib
from email.mime.text import MIMEText

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

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.String(50))
    content = db.Column(db.Text(65536))
    subject = db.Column(db.Text(256))
    send_email = db.Column(db.Boolean)

    # UserID of last person email sent to
    sent_to_last = db.Column(db.Integer)

    # Has email been sent to all relevant users?
    email_sent = db.Column(db.Boolean)

    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    sender = db.relationship('User',
        backref=db.backref('announcements-sent',
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

    is_waiting = db.Column(db.Boolean, nullable=True)
    has_tickets = db.Column(db.Boolean, nullable=True)
    has_collected = db.Column(db.Boolean, nullable=True)

    users = db.relationship(
        'User',
        secondary=user_announce_link,
        backref='announcements'
    )


    def __init__(self,
                 subject,
                 content,
                 send_email,
                 college=None,
                 has_tickets=None,
                 affiliation=None,
                 is_waiting=None,
                 has_collected=None):
        self.time = datetime.datetime.now()
        self.subject = subject
        self.content = content
        self.has_tickets = has_tickets
        self.is_waiting = is_waiting
        self.has_collected = has_collected
        self.users = []

        if isinstance(college, (College, type(None))):
            self.college = college
        else:
            self.college_id = college

        if isinstance(affiliation, (Affiliation, type(None))):
            self.affiliation = affiliation
        else:
            self.affiliation_id = affiliation

        query = User.filter_by(User.id>self.sent_to_last)

        if self.college is not None:
            query.filter_by(User.college==self.college)

        if self.affiliation is not None:
            query.filter_by(User.affiliation==self.affiliation)

        for user in query:
            if ((self.has_tickets is None or
                user.hasTickets()==self.has_tickets) and
               (self.is_waiting is None or
                user.isWaiting()==self.is_waiting) and
               (self.has_collected is None or
                user.hasCollected()==self.has_collected)):
                self.users.append(user)

    def __repr__(self):
        return "<Announcement {id}: {subject}".format_map(vars(self))

    def sendEmails(self):
        try:
            msg = MIMEText(self.content)
            msg['Subject'] = subject
            msg['From'] = self.sender.email

            for user in self.users:
                msg['To'] = user.email
                app.email_manager.sendMsg(msg)
                self.sent_to_last = user.id
            self.email_sent = True
        finally:
            db.session.commit()

