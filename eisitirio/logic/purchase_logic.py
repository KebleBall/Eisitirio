# coding: utf-8
"""Various business logic functions for the purchase flow."""

from __future__ import unicode_literals

import collections
import datetime
import json

import flask
from flask.ext import login

from eisitirio import app
from eisitirio.database import models, db
from eisitirio.helpers import postage_option

LARGE_NUMBER = 999999
APP = app.APP
DB = db.DB

_TicketInfo = collections.namedtuple(
    "TicketInfo",
    [
        "guest_tickets_available",
        "total_tickets_available",
        "ticket_types"
    ]
)
class TicketInfo(_TicketInfo):
    """Parameter object with information about what tickets a user can buy.

    Attributes:
        guest_tickets_available: (int) How many guest tickets can be bought.
        total_tickets_available: (int) How many tickets the user can buy.
        transaction_limit: (int)
        ticket_types: (list(TicketType, int)) Available ticket types, along with
            how many of each ticket type can be bought.
    """

    def to_json(self):
        """Return a JSON object with useful information for JS scripts."""
        return json.dumps({
            "guest_tickets_available": self.guest_tickets_available,
            "total_tickets_available": self.total_tickets_available,
            "ticket_types": [
                ticket_type.to_json_dict(limit)
                for ticket_type, limit in self.ticket_types
            ]
        })

def guest_tickets_available():
    """Return how many guest tickets are available."""
    guest_ticket_count = models.Ticket.query.filter(
        models.Ticket.ticket_type.in_(app.APP.config['GUEST_TYPE_SLUGS'])
    ).filter(
        models.Ticket.cancelled == False  # pylint: disable=singleton-comparison
    ).count()

    return max(
        0,
        app.APP.config['GUEST_TICKETS_AVAILABLE'] - guest_ticket_count
    )

def _total_tickets_available(user, now):
    """Get how many tickets are available for a user to buy."""
    return max(0, min(
        app.APP.config.get('MAX_TICKETS', now=now) - user.active_ticket_count,
        app.APP.config.get('MAX_TICKETS_PER_TRANSACTION', now=now)
    ))

def _type_limit_per_person(user, ticket_type):
    """Get how many tickets of a given type the user can buy.

    Based on the per person limit. Returns an arbitrary excessively large number
    if no such limit is set.
    """
    if ticket_type.limit_per_person == -1:
        return LARGE_NUMBER

    return max(0, ticket_type.limit_per_person - user.active_tickets.filter(
        models.Ticket.ticket_type == ticket_type.slug
    ).count())

def _type_total_limit(ticket_type):
    """Get how many tickets of a given type the user can buy.

    Based on the limit on total sales. Returns an arbitrary excessively large
    number if no such limit is set.
    """
    if ticket_type.total_limit == -1:
        return LARGE_NUMBER

    return max(0, ticket_type.total_limit - models.Ticket.query.filter(
        models.Ticket.ticket_type == ticket_type.slug
    ).filter(
        models.Ticket.cancelled == False # pylint: disable=singleton-comparison
    ).count())

def _get_ticket_limit(user, ticket_type, ticket_info):
    """Get the number of tickets of |ticket_type| that |user| can purchase.

    Args:
        user: (models.User) The user purchasing tickets.
        ticket_type: (eisitirio.helpers.ticket_type.TicketType) the type of
            ticket being purchased
        ticket_info: (TicketInfo) Information about available tickets.

    Returns:
        (int) the number of |ticket_type| tickets that |user| can buy.
    """

    limit = min(
        _type_limit_per_person(user, ticket_type),
        _type_total_limit(ticket_type),
        ticket_info.total_tickets_available
    )

    if ticket_type.counts_towards_guest_limit:
        limit = min(limit, ticket_info.guest_tickets_available)

    return limit

def get_ticket_info(user):
    """Get information about what tickets |user| can purchase online."""

    ticket_info = TicketInfo(
        guest_tickets_available(),
        _total_tickets_available(user, datetime.datetime.utcnow()),
        []
    )

    for ticket_type in app.APP.config['TICKET_TYPES']:
        if ticket_type.can_buy(user):
            ticket_limit = _get_ticket_limit(user, ticket_type, ticket_info)

            if ticket_limit > 0:
                ticket_info.ticket_types.append((ticket_type, ticket_limit))

    return ticket_info

def get_ticket_info_for_upgrade(user):
    """Get information about what tickets |user| can purchase online."""
    upgraded_tickets = models.Ticket.query.filter(models.Ticket.note.like("%Upgrade%")).count()
    return max(0, 100 -  upgraded_tickets)

def _get_group_ticket_limit(user, ticket_type, ticket_info):
    """Get how many |ticket_type| tickets |user| can purchase in a group.

    Args:
        user: (models.User) The user purchasing tickets.
        ticket_type: (eisitirio.helpers.ticket_type.TicketType) the type of
            ticket being purchased
        ticket_info: (TicketInfo) Information about available tickets.

    Returns:
        (int) the number of |ticket_type| tickets that |user| can buy.
    """

    return min(
        _type_limit_per_person(user, ticket_type),
        ticket_info.total_tickets_available
    )

def get_group_ticket_info(user):
    """Get information about what tickets |user| can purchase online."""

    ticket_info = TicketInfo(
        LARGE_NUMBER,
        _total_tickets_available(user,
                                 app.APP.config['GENERAL_RELEASE_STARTS']),
        []
    )

    for ticket_type in app.APP.config['TICKET_TYPES']:
        if ticket_type.can_buy(user, True):
            ticket_limit = _get_group_ticket_limit(user, ticket_type,
                                                   ticket_info)

            if ticket_limit > 0:
                ticket_info.ticket_types.append((ticket_type, ticket_limit))

    return ticket_info

def validate_tickets(ticket_info, num_tickets):
    """Validate the number of tickets selected by the user and the names."""
    flashes = []

    guest_ticket_count = 0
    total_ticket_count = 0

    for ticket_type, type_limit in ticket_info.ticket_types:
        ordered = num_tickets[ticket_type.slug]

        if ordered > type_limit:
            flashes.append("You can order at most {0} {1} tickets.".format(
                type_limit,
                ticket_type.name
            ))

        if ticket_type.counts_towards_guest_limit:
            guest_ticket_count += ordered

        total_ticket_count += ordered

    if guest_ticket_count > ticket_info.guest_tickets_available:
        flashes.append("You can order at most {0} {1} tickets.".format(
            ticket_info.guest_tickets_available,
            _to_list(
                ticket_type.name
                for ticket_type, _ in ticket_info.ticket_types
                if ticket_type.counts_towards_guest_limit
            )
        ))

    if total_ticket_count > ticket_info.total_tickets_available:
        flashes.append("You can order at most {0} tickets.".format(
            ticket_info.total_tickets_available
        ))

    if total_ticket_count == 0:
        flashes.append("You haven't ordered any tickets.")

    return flashes

def _to_list(*args):
    """Convert a list to a comma separated string with an oxford comma."""
    argc = len(args)
    if argc == 0:
        return ""
    elif argc == 1:
        return args[0]
    elif argc == 2:
        return "{0} or {1}".format(args[0], args[1])
    else:
        return "{0}, or {1}".format(", ".join(args[:-1]), args[-1])

def create_tickets(user, ticket_info, num_tickets):
    """Create the ticket objects from the user's selection."""
    tickets = [
        models.Ticket(user, ticket_type.slug, ticket_type.price)
        for ticket_type, _ in ticket_info.ticket_types
        for _ in xrange(num_tickets[ticket_type.slug])
    ]

    return tickets

def check_payment_method(flashes):
    """Validate the payment method selected in the purchase form.

    Args:
        flashes: (list(str)) List of error messages. Mutated if an error is
            found.

    Returns:
        (str or None, str or None) Selected payment method, and term for battels
        payment.
    """
    payment_method = None
    payment_term = None

    if 'payment_method' not in flask.request.form:
        flashes.append('You must select a payment method')
    elif (
            flask.request.form['payment_method'] not in
            APP.config['PAYMENT_METHODS']
    ):
        flashes.append('That is not a valid payment method')
    elif flask.request.form['payment_method'].startswith('Battels'):
        payment_method = 'Battels'
        payment_term = flask.request.form['payment_method'][8:]

        if not login.current_user.can_pay_by_battels():
            flashes.append('You cannot pay by battels')
        else:
            available_terms = {
                'MT': ['MT', 'MTHT'],
                'HT': ['HT']
            }

            if payment_term not in available_terms[APP.config['CURRENT_TERM']]:
                flashes.append(
                    'You have selected an invalid battels payment term'
                )
    else:
        payment_method = 'Card'
        payment_term = None

    return payment_method, payment_term

def check_roundup_donation(flashes):
    if not APP.config['ENABLE_ROUNDUP_DONATION']:
        return 0

    if 'roundup_donation' not in flask.request.form:
        flashes.append('You must select a roundup donation option')
    elif flask.request.form['roundup_donation'] == 'make_roundup_donation':
        return APP.config['ROUNDUP_DONATION_AMT']

    return 0


def check_postage(flashes):
    """Validate the postage method selected in the purchase form.

    Args:
        flashes: (list(str)) List of error messages. Mutated if an error is
            found.

    Returns:
        (postage_option.PostageOption or None, str or None) the selected postage
        method and address to post to.
    """
    if not APP.config['ENABLE_POSTAGE']:
        return None, None

    postage = None
    address = None

    if 'postage' not in flask.request.form:
        flashes.append('You must select a postage option')
    elif flask.request.form['postage'] == 'graduand':
        return APP.config['GRADUAND_POSTAGE_OPTION'], None
    elif flask.request.form['postage'] not in app.APP.config['POSTAGE_OPTIONS']:
        flashes.append('That is not a valid postage option')
    else:
        postage = APP.config['POSTAGE_OPTIONS'][
            flask.request.form['postage']
        ]

        if postage.needs_address and (
                'address' not in flask.request.form or
                flask.request.form['address'] == ''
        ):
            flashes.append('You must enter a postage address')
        else:
            address = flask.request.form['address']

    return postage, address

def wait_available(user):
    """How many tickets can the user join the waiting list for."""
    if not app.APP.config['WAITING_OPEN']:
        return 0

    return max(0, min(
        app.APP.config['MAX_TICKETS'] - user.active_ticket_count,
        _type_limit_per_person(user, app.APP.config['DEFAULT_TICKET_TYPE']),
        _type_total_limit(app.APP.config['DEFAULT_TICKET_TYPE']),
        app.APP.config['MAX_TICKETS_WAITING'] - user.waiting_for
    ))
