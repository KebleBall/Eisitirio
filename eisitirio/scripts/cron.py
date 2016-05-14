# coding: utf-8
"""Worker to run repeated tasks on a schedule."""

from __future__ import unicode_literals

import contextlib
import datetime
import os
import sys

from flask.ext import script

from eisitirio import app
from eisitirio import system # pylint: disable=unused-import
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.database import static
from eisitirio.helpers import email_manager
from eisitirio.helpers import statistic_plots
from eisitirio.helpers import statistics
from eisitirio.logic import purchase_logic

APP = app.APP
DB = db.DB

@contextlib.contextmanager
def file_lock(lock_file):
    """Use a lock file to prevent multiple instances of the worker running."""
    if os.path.exists(lock_file):
        print (
            'Only one script can run at once. '
            'Script is locked with {}'
        ).format(lock_file)
        sys.exit(-1)
    else:
        open(lock_file, 'w').write('1')
        try:
            yield
        finally:
            os.remove(lock_file)

def get_last_run_time(timestamp_file):
    """Get the time at which the set of tasks was last run.

    Args:
        timestamp_file: (str) absolute path to file containing the timestamp

    Returns:
        (datetime.datetime) The datetime.datetime object representing the time
            in the timestamp
    """
    try:
        with open(timestamp_file, 'r') as file_handle:
            timestamp = int(file_handle.read().strip())
    except IOError:
        print 'Timestamp not found'
        timestamp = 0

    return datetime.datetime.fromtimestamp(timestamp)

def set_timestamp(timestamp_file, now):
    """Write the time of the current run to the timestamp file.

    Args:
        timestamp_file: (str) absolute path to file containing the timestamp
        now: (datetime.datetime) time at which the script was started
    """
    with open(timestamp_file, 'w') as file_handle:
        file_handle.write(now.strftime('%s'))

def send_announcements():
    """Send emails for any pending announcements."""
    emails_count = APP.config['EMAILS_BATCH']

    announcements = models.Announcement.query.filter(
        models.Announcement.send_email == True # pylint: disable=singleton-comparison
    ).filter(
        models.Announcement.email_sent == False # pylint: disable=singleton-comparison
    ).all()

    for announcement in announcements:
        if emails_count <= 0:
            break

        emails_count = announcement.send_emails(emails_count)

def allocate_waiting():
    """Allocate available tickets to people on the waiting list."""
    if not APP.config['TICKETS_ON_SALE']:
        return

    tickets_available = purchase_logic.guest_tickets_available()

    ticket_type = APP.config['DEFAULT_TICKET_TYPE']

    for wait in models.Waiting.query.order_by(
            models.Waiting.waiting_since
    ).all():
        if wait.waiting_for > tickets_available:
            break

        tickets = [
            models.Ticket(
                wait.user,
                ticket_type.slug,
                ticket_type.price
            )
            for _ in xrange(wait.waiting_for)
        ]

        DB.session.add_all(tickets)
        DB.session.delete(wait)

        APP.email_manager.send_template(
            wait.user.email,
            'You have been allocated tickets',
            'waiting_allocation.email',
            user=wait.user,
            num_tickets=wait.waiting_for,
            expiry=tickets[0].expires
        )

        DB.session.commit()

        tickets_available -= wait.waiting_for

def cancel_expired_tickets(now):
    """Cancel all tickets which have not been paid for in the given time."""
    expired = models.Ticket.query.filter(
        models.Ticket.expires != None
    ).filter(
        models.Ticket.expires < now
    ).filter(
        models.Ticket.cancelled == False # pylint: disable=singleton-comparison
    ).filter(
        models.Ticket.paid == False # pylint: disable=singleton-comparison
    ).all()

    for ticket in expired:
        ticket.add_note('Cancelled due to non-payment within time limit')
        ticket.cancelled = True
        ticket.expires = None

    DB.session.commit()

def remove_expired_secret_keys(now):
    """Remove expired secret keys for password resets."""
    expired = models.User.query.filter(
        models.User.secret_key_expiry != None
    ).filter(
        models.User.secret_key_expiry < now
    ).all()

    for user in expired:
        user.secret_key_expiry = None
        user.secret_key = None

    DB.session.commit()

def delete_old_statistics(now):
    """Delete statistics which are older than the limit."""
    statistic_limit = now - APP.config['STATISTICS_KEEP']

    models.Statistic.query.filter(
        models.Statistic.timestamp < statistic_limit
    ).delete()

    DB.session.commit()

def generate_statistics():
    """Generate statistics for all groups."""
    for group in static.STATISTIC_GROUPS:
        DB.session.add_all(
            models.Statistic(
                group,
                name,
                value
            ) for name, value in statistics.get(group).iteritems()
        )

        DB.session.commit()

def draw_graphs():
    """Generate graphs for all statistics groups."""
    if not os.path.exists(APP.config['GRAPH_STORAGE_FOLDER']):
        os.makedirs(APP.config['GRAPH_STORAGE_FOLDER'])

    for group in static.STATISTIC_GROUPS:
        statistic_plots.create_plot(group)

def run_5_minutely(now):
    """Run tasks which need to be run every 5 minutes.

    Args:
        now: (datetime.datetime) time at which the script was started
    """
    timestamp_file = os.path.abspath(
        './{}_cron_timestamp_5min.txt'.format(APP.config['ENVIRONMENT'])
    )

    if now - get_last_run_time(timestamp_file) < datetime.timedelta(minutes=5):
        return

    set_timestamp(timestamp_file, now)

    send_announcements()

    allocate_waiting()

    cancel_expired_tickets(now)

    remove_expired_secret_keys(now)

def run_20_minutely(now):
    """Run tasks which need to be run every 20 minutes.

    Args:
        now: (datetime.datetime) time at which the script was started
    """
    timestamp_file = os.path.abspath(
        './{}_cron_timestamp_20min.txt'.format(APP.config['ENVIRONMENT'])
    )

    difference = now - get_last_run_time(timestamp_file)

    if difference < datetime.timedelta(minutes=20):
        return

    set_timestamp(timestamp_file, now)

    delete_old_statistics(now)

    generate_statistics()

    draw_graphs()

class CronCommand(script.Command):
    """Flask Script command for running Cron jobs."""

    help = 'Run cron jobs'

    @staticmethod
    def run():
        """Check the lock, do some setup and run the tasks."""
        lockfile = os.path.abspath(
            './{}.cron.lock'.format(APP.config['ENVIRONMENT'])
        )

        with file_lock(lockfile):
            email_manager.EmailManager(APP)

            now = datetime.datetime.utcnow()

            run_5_minutely(now)

            run_20_minutely(now)
