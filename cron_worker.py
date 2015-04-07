#!/usr/bin/env python2
# coding: utf-8
"""Worker to run repeated tasks on a schedule."""

from __future__ import unicode_literals

import os
import sys
from datetime import datetime
from datetime import timedelta
from contextlib import contextmanager

from sqlalchemy import func
from sqlalchemy import distinct

from kebleball import app
from kebleball.database import db
from kebleball.helpers import email_manager

APP = app.APP
DB = db.DB

@contextmanager
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
        (datetime) The datetime object representing the time in the timestamp
    """
    try:
        with open(timestamp_file, 'r') as file_handle:
            timestamp = int(file_handle.read().strip())
    except IOError:
        print 'Timestamp not found'
        timestamp = 0

    return datetime.fromtimestamp(timestamp)

def set_timestamp(timestamp_file, now):
    """Write the time of the current run to the timestamp file.

    Args:
        timestamp_file: (str) absolute path to file containing the timestamp
        now: (datetime) time at which the script was started
    """
    with open(timestamp_file, 'w') as file_handle:
        file_handle.write(now.strftime('%s'))

def send_announcements():
    """Send emails for any pending announcements."""
    emails_count = APP.config['EMAILS_BATCH']

    announcements = DB.Announcement.query \
        .filter(DB.Announcement.send_email == True) \
        .filter(DB.Announcement.email_sent == False) \
        .all()

    for announcement in announcements:
        if emails_count <= 0:
            break

        emails_count = announcement.send_emails(emails_count)

def allocate_waiting():
    """Allocate available tickets to people on the waiting list."""
    tickets_available = APP.config['TICKETS_AVAILABLE'] - DB.Ticket.count()

    for wait in DB.Waiting.query.order_by(DB.Waiting.waitingsince).all():
        if wait.waiting_for > tickets_available:
            break

        tickets = []

        if wait.user.gets_discount():
            tickets.append(
                DB.Ticket(
                    wait.user,
                    None,
                    (
                        wait.user.get_base_ticket_price() -
                        APP.config['KEBLE_DISCOUNT']
                    )
                )
            )
            start = 1
        else:
            start = 0

        for _ in xrange(start, wait.waiting_for):
            tickets.append(
                DB.Ticket(
                    wait.user,
                    None,
                    wait.user.get_base_ticket_price()
                )
            )

        if wait.referrer is not None:
            for ticket in tickets:
                ticket.set_referrer(wait.referrer)

        DB.session.add_all(tickets)
        DB.session.delete(wait)

        APP.email_manager.send_template(
            wait.user.email,
            'You have been allocated tickets',
            'waiting_allocation.email',
            user=wait.user,
            num_tickets=wait.waitingfor,
            expiry=tickets[0].expires
        )

        DB.session.commit()

        tickets_available -= wait.waiting_for

def cancel_expired_tickets(now):
    """Cancel all tickets which have not been paid for in the given time."""
    expired = DB.Ticket.query \
        .filter(DB.Ticket.expires != None) \
        .filter(DB.Ticket.expires < now) \
        .filter(DB.Ticket.cancelled == False) \
        .filter(DB.Ticket.paid == False) \
        .all()

    for ticket in expired:
        ticket.add_note('Cancelled due to non-payment within time limit')
        ticket.cancelled = True
        ticket.expires = None

    DB.session.commit()

def remove_expired_secret_keys(now):
    """Remove expired secret keys for password resets."""
    expired = DB.User.query \
        .filter(DB.User.secret_key_expiry != None) \
        .filter(DB.User.secret_key_expiry < now) \
        .all()

    for user in expired:
        user.secret_key_expiry = None
        user.secret_key = None

    DB.session.commit()

def delete_old_statistics(now):
    """Delete statistics which are older than the limit."""
    statistic_limit = now - APP.config['STATISTICS_KEEP']

    DB.Statistic.query.filter(DB.Statistic.timestamp < statistic_limit).delete()

    DB.session.commit()

def generate_sales_statistics():
    """Generate statistics for number of tickets available, sold etc."""
    def maybe_int(value):
        """Convert the result of an sqlalchemy scalar to an int."""
        if value is None:
            return 0
        else:
            return int(value)

    statistics = {
        'Available':
            APP.config['TICKETS_AVAILABLE'],
        'Ordered':
            DB.Ticket.count(),
        'Paid':
            DB.Ticket.query \
                .filter(DB.Ticket.paid == True) \
                .filter(DB.Ticket.cancelled == False) \
                .count(),
        'Cancelled':
            DB.Ticket.query.filter(DB.Ticket.cancelled == True).count(),
        'Collected':
            DB.Ticket.query.filter(DB.Ticket.collected == True).count(),
        'DB.Waiting':
            maybe_int(
                DB.session.query(
                    func.sum(
                        DB.Waiting.waiting_for
                    )
                ).scalar()
            ),
    }

    DB.session.add_all(
        DB.Statistic(
            'Sales',
            name,
            value
        ) for name, value in statistics.iteritems()
    )

    DB.session.commit()

def generate_payment_statistics():
    """Generate statistics for number of tickets paid for by each method."""
    DB.session.add_all(
        DB.Statistic(
            'Payments',
            str(method[0]),
            DB.Ticket.query \
                .filter(DB.Ticket.payment_method == method[0]) \
                .filter(DB.Ticket.paid == True) \
                .count()
        ) for method in DB.session.query(
            distinct(
                DB.Ticket.payment_method
            )
        ).all()
    )

    DB.session.commit()

def generate_college_statistics():
    """Generate statistics for number of users from each college."""
    DB.session.add_all(
        DB.Statistic(
            'Colleges',
            college.name,
            DB.User.query.filter(DB.User.college_id == college.id).count()
        ) for college in DB.College.query.all()
    )

    DB.session.commit()

def send_3_day_warnings(now, difference):
    """Send warnings for tickets expiring in 3 days.

    Args:
        now: (datetime) time at which the script was started
        difference: (timedelta) how long since the script last ran
    """
    start = now + timedelta(days=3)
    end = now + timedelta(days=3) + difference

    tickets = DB.Ticket.query \
        .filter(DB.Ticket.expires != None) \
        .filter(DB.Ticket.expires > start) \
        .filter(DB.Ticket.expires <= end) \
        .filter(DB.Ticket.cancelled == False) \
        .filter(DB.Ticket.paid == False) \
        .group_by(DB.Ticket.owner_id) \
        .all()

    for ticket in tickets:
        APP.email_manager.send_template(
            ticket.owner.email,
            'Tickets Expiring',
            'tickets_expiring_3_days.email',
            ticket=ticket
        )

def send_1_day_warnings(now, difference):
    """Send warnings for tickets expiring in 1 day.

    Args:
        now: (datetime) time at which the script was started
        difference: (timedelta) how long since the script last ran
    """
    start = now + timedelta(days=1)
    end = now + timedelta(days=1) + difference

    tickets = DB.Ticket.query \
        .filter(DB.Ticket.expires != None) \
        .filter(DB.Ticket.expires > start) \
        .filter(DB.Ticket.expires <= end) \
        .filter(DB.Ticket.cancelled == False) \
        .filter(DB.Ticket.paid == False) \
        .group_by(DB.Ticket.owner_id) \
        .all()

    for ticket in tickets:
        APP.email_manager.send_template(
            ticket.owner.email,
            'Final Warning: Tickets Expiring',
            'tickets_expiring_1_day.email',
            ticket=ticket
        )

def run_5_minutely(now):
    """Run tasks which need to be run every 5 minutes.

    Args:
        now: (datetime) time at which the script was started
    """
    timestamp_file = os.path.abspath(
        './{}_cron_timestamp_5min.txt'.format(APP.config['ENVIRONMENT'])
    )

    if now - get_last_run_time(timestamp_file) < timedelta(minutes=5):
        return

    set_timestamp(timestamp_file, now)

    send_announcements()

    allocate_waiting()

    cancel_expired_tickets(now)

    remove_expired_secret_keys(now)

def run_20_minutely(now):
    """Run tasks which need to be run every 20 minutes.

    Args:
        now: (datetime) time at which the script was started
    """
    timestamp_file = os.path.abspath(
        './{}_cron_timestamp_20min.txt'.format(APP.config['ENVIRONMENT'])
    )

    difference = now - get_last_run_time(timestamp_file)

    if difference < timedelta(minutes=20):
        return

    set_timestamp(timestamp_file, now)

    delete_old_statistics(now)

    generate_sales_statistics()

    generate_payment_statistics()

    generate_college_statistics()

    send_3_day_warnings(now, difference)

    send_1_day_warnings(now, difference)

def main():
    """Check the lock, do some setup and run the tasks."""
    if 'KEBLE_BALL_ENV' in os.environ:
        if os.environ['KEBLE_BALL_ENV'] == 'PRODUCTION':
            APP.config.from_pyfile('config/production.py')
        elif os.environ['KEBLE_BALL_ENV'] == 'STAGING':
            APP.config.from_pyfile('config/staging.py')
        elif os.environ['KEBLE_BALL_ENV'] == 'DEVELOPMENT':
            APP.config.from_pyfile('config/development.py')

    lockfile = os.path.abspath(
        './{}.cron.lock'.format(APP.config['ENVIRONMENT'])
    )

    with file_lock(lockfile):
        email_manager.EmailManager(APP)

        now = datetime.utcnow()

        run_5_minutely(now)

        run_20_minutely(now)

if __name__ == '__main__':
    main()
