# coding: utf-8
"""Views related to administering announcements."""

from __future__ import unicode_literals

import flask_login as login
# from flask.ext import login
import flask

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.helpers import login_manager

APP = app.APP
DB = db.DB

ADMIN_ANNOUNCEMENTS = flask.Blueprint('admin_announcements', __name__)

@ADMIN_ANNOUNCEMENTS.route('/admin/announcements', methods=['GET', 'POST'])
@ADMIN_ANNOUNCEMENTS.route('/admin/announcements/page/<int:page>',
                           methods=['GET', 'POST'])
@login.login_required
@login_manager.admin_required
def announcements(page=1):
    """Manage announcements.

    Allows the creation of announcements, viewing and deleting existing
    announcements, and cancelling email sending for existing announcements.
    """
    form = {}

    if flask.request.method == 'POST':
        form = flask.request.form

        success = True

        if 'subject' not in form or form['subject'] == '':
            flask.flash(
                'Subject must not be blank',
                'warning'
            )
            success = False

        if 'message' not in form or form['message'] == '':
            flask.flash(
                'Message must not be blank',
                'warning'
            )
            success = False

        if 'owned_tickets' in form and form['owned_tickets'] == 'no':
            if 'collected' in form and form['collected'] == 'yes':
                flask.flash(
                    (
                        'A person cannot own no tickets and have collected '
                        'tickets'
                    ),
                    'warning'
                )
                success = False
            if 'uncollected' in form and form['uncollected'] == 'yes':
                flask.flash(
                    (
                        'A person cannot own no tickets and have uncollected '
                        'tickets'
                    ),
                    'warning'
                )
                success = False

        if success:
            college = None
            if 'college' in form and form['college'] != 'any':
                college = models.College.get_by_id(form['college'])

            affiliation = None
            if 'affiliation' in form and form['affiliation'] != 'any':
                affiliation = models.Affiliation.get_by_id(form['affiliation'])

            has_tickets = None
            if 'owned_tickets' in form:
                if form['owned_tickets'] == 'yes':
                    has_tickets = True
                elif form['owned_tickets'] == 'no':
                    has_tickets = False

            holds_ticket = None
            if 'held_ticket' in form:
                if form['held_ticket'] == 'yes':
                    holds_ticket = True
                elif form['held_ticket'] == 'no':
                    holds_ticket = False

            is_waiting = None
            if 'waiting' in form:
                if form['waiting'] == 'yes':
                    is_waiting = True
                elif form['waiting'] == 'no':
                    is_waiting = False

            has_collected = None
            if 'collected' in form:
                if form['collected'] == 'yes':
                    has_collected = True
                elif form['collected'] == 'no':
                    has_collected = False

            has_uncollected = None
            if 'uncollected' in form:
                if form['uncollected'] == 'yes':
                    has_uncollected = True
                elif form['uncollected'] == 'no':
                    has_uncollected = False

            send_email = 'send_emails' in form and form['send_emails'] == 'yes'
            use_noreply = 'use_noreply' in form and form['use_noreply'] == 'yes'

            announcement = models.Announcement(
                form['subject'],
                form['message'],
                login.current_user,
                send_email,
                college,
                affiliation,
                has_tickets,
                holds_ticket,
                is_waiting,
                has_collected,
                has_uncollected,
                use_noreply
            )

            DB.session.add(announcement)
            DB.session.commit()

            flask.flash(
                'Announcement created successfully',
                'success'
            )

            form = {}

    return flask.render_template(
        'admin_announcements/announcements.html',
        colleges=models.College.query.all(),
        affiliations=models.Affiliation.query.all(),
        announcements=models.Announcement.query.paginate(page, 10, False),
        form=form
    )

@ADMIN_ANNOUNCEMENTS.route('/admin/announcement/<int:announcement_id>/delete')
@login.login_required
@login_manager.admin_required
def delete_announcement(announcement_id):
    """Delete an announcement.

    Removes an announcement from the database, but cannot recall any emails
    which have already been sent
    """
    announcement = models.Announcement.get_by_id(announcement_id)

    if announcement:
        DB.session.delete(announcement)
        DB.session.commit()

        flask.flash(
            'Announcement deleted successfully',
            'success'
        )
    else:
        flask.flash(
            'Could not find announcement, could not delete',
            'warning'
        )

    return flask.redirect(flask.request.referrer or
                          flask.url_for('admin_announcements.announcements'))

@ADMIN_ANNOUNCEMENTS.route('/admin/announcement/<int:announcement_id>/cancel')
@login.login_required
@login_manager.admin_required
def cancel_announcement_emails(announcement_id):
    """Cancel sending emails for an announcement.

    Remove from the sending queue any pending emails for an announcement. Does
    not recall previously sent emails.
    """
    announcement = models.Announcement.get_by_id(announcement_id)

    if announcement:
        announcement.emails = []
        announcement.send_email = False
        DB.session.commit()

        flask.flash(
            'Announcement emails cancelled successfully',
            'success'
        )
    else:
        flask.flash(
            'Could not find announcement, could not cancel emails',
            'warning'
        )

    return flask.redirect(flask.request.referrer or
                          flask.url_for('admin_announcements.announcements'))
