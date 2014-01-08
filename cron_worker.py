#!/usr/bin/env python2
# coding: utf-8

from datetime import datetime, timedelta
import os, sys
from contextlib import contextmanager
from kebleball.app import app

if (
    'KEBLE_BALL_ENV' in os.environ and
    os.environ['KEBLE_BALL_ENV'] in [
        'PRODUCTION',
        'STAGING'
    ]
):
    app.config.from_pyfile('config/production.py')

from kebleball.database import *
from kebleball.helpers.email_manager import EmailManager
from sqlalchemy import func

@contextmanager
def file_lock(lock_file):
    if os.path.exists(lock_file):
        print 'Only one script can run at once. '\
              'Script is locked with %s' % lock_file
        sys.exit(-1)
    else:
        open(lock_file, 'w').write("1")
        try:
            yield
        finally:
            os.remove(lock_file)

with file_lock('/tmp/kebleball_cron.lock'):
    email_manager = EmailManager(app)
    app.email_manager = email_manager

    try:
        with open('cron_timestamp.txt', 'r') as f:
            timestamp = int(f.read().strip())
    except IOError:
        print 'cron_timestamp.txt not found'
        timestamp = 0

    last_run = datetime.fromtimestamp(timestamp)
    now = datetime.utcnow()

    with open('cron_timestamp.txt', 'w') as f:
        f.write(now.strftime('%s'))

    difference = now - last_run

    if difference > timedelta(minutes=5):
        emails_count = app.config['EMAILS_BATCH']

        announcements = Announcement.query \
            .filter(Announcement.send_email == False) \
            .filter(Announcement.email_sent == False) \
            .all()

        for announcement in announcements:
            if emails_count <= 0:
                break

            emails_count = announcement.sendEmails(emails_count)

        tickets_available = app.config['TICKETS_AVAILABLE'] - Ticket.count()

        if tickets_available > 0:
            waiting = Waiting.query.order_by(Waiting.waitingsince).all()

            for wait in waiting:
                if wait.waitingfor > tickets_available:
                    break

                tickets = []

                if wait.user.getsDiscount():
                    tickets.append(
                        Ticket(
                            wait.user,
                            None,
                            app.config['TICKET_PRICE'] - app.config['KEBLE_DISCOUNT']
                        )
                    )
                    start = 1
                else:
                    start = 0

                for x in xrange(start, wait.waitingfor):
                    tickets.append(
                        Ticket(
                            wait.user,
                            None,
                            app.config['TICKET_PRICE']
                        )
                    )

                if wait.referrer is not None:
                    for ticket in tickets:
                        ticket.setReferrer(wait.referrer)

                db.session.add_all(tickets)
                db.session.delete(wait)

                email_manager.sendTemplate(
                    wait.user.email,
                    'You have been allocated tickets',
                    'waitingAllocation.email',
                    user=wait.user,
                    numTickets=wait.waitingfor,
                    expiry=tickets[0].expires
                )

                db.session.commit()

        tickets_expired = Ticket.query \
            .filter(Ticket.expires != None) \
            .filter(Ticket.expires < datetime.utcnow()) \
            .filter(Ticket.paid == False) \
            .all()

        for ticket in tickets_expired:
            ticket.addNote('Cancelled due to non-payment within time limit')
            ticket.cancelled = True

        db.session.commit()

        users_expired = User.query \
            .filter(User.secretkeyexpiry != None) \
            .filter(User.secretkeyexpiry < datetime.utcnow()) \
            .all()

        for user in users_expired:
            user.secretkeyexpiry = None
            user.secretkey = None

        db.session.commit()

    if difference > timedelta(minutes=20):
        statistic_limit = now - app.config['STATISTICS_KEEP']

        Statistic.query.filter(Statistic.timestamp < statistic_limit).delete()

        statistics = []

        def maybe_int(value):
            if value is None:
                return 0
            else:
                return int(value)

        sales_statistics = {
            'Available':
                app.config['TICKETS_AVAILABLE'],
            'Ordered':
                Ticket.count(),
            'Paid':
                Ticket.query.filter(Ticket.paid == True).count(),
            'Cancelled':
                Ticket.query.filter(Ticket.cancelled == True).count(),
            'Collected':
                Ticket.query.filter(Ticket.collected == True).count(),
            'Waiting':
                maybe_int(db.session.query(func.sum(Waiting.waitingfor)).scalar()),
        }

        for key, value in sales_statistics.iteritems():
            statistics.append(
                Statistic(
                    'Sales',
                    key,
                    value
                )
            )

        paymentMethods = [
            'Battels',
            'Card',
            'Cash',
            'Cheque',
            'Free'
        ]

        for method in paymentMethods:
            statistics.append(
                Statistic(
                    'Payments',
                    method,
                    Ticket.query \
                        .filter(Ticket.paymentmethod == method) \
                        .filter(Ticket.paid == True) \
                        .count()
                )
            )

        colleges = College.query.all()

        for college in colleges:
            statistics.append(
                Statistic(
                    'Colleges',
                    college.name,
                    User.query.filter(User.college_id == college.id).count()
                )
            )

        db.session.add_all(statistics)
        db.session.commit()

    if difference > timedelta(days=1):
        _3days = now + timedelta(days=3)
        _2days = now + timedelta(days=3)
        _1day = now + timedelta(days=1)

        tickets_3days = Ticket.query \
            .filter(Ticket.expires != None) \
            .filter(Ticket.expires > _2days) \
            .filter(Ticket.expires < _3days) \
            .group_by(Ticket.owner_id) \
            .all()

        for ticket in tickets_3days:
            email_manager.sendTemplate(
                ticket.owner.email,
                'Tickets Expiring',
                'ticketsExpiring3days.email'
            )

        tickets_1day = Ticket.query \
            .filter(Ticket.expires != None) \
            .filter(Ticket.expires > now) \
            .filter(Ticket.expires < _1day) \
            .group_by(Ticket.owner_id) \
            .all()

        for ticket in tickets_1day:
            email_manager.sendTemplate(
                ticket.owner.email,
                'Final Warning: Tickets Expiring',
                'ticketsExpiring1day.email'
            )