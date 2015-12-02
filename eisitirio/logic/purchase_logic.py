# coding: utf-8
"""Various business logic functions for the purchase flow."""

import collections
import json

import flask
from flask.ext import login

from eisitirio import app
from eisitirio.database import models
from eisitirio.helpers import postage_option

LARGE_NUMBER = 999999
APP = app.APP

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
        return json.dumps({
            "guest_tickets_available": self.guest_tickets_available,
            "total_tickets_available": self.total_tickets_available,
            "ticket_types": [
                ticket_type.to_json_dict(limit)
                for ticket_type, limit in self.ticket_types
            ]
        })

def _guest_tickets_available():
    """Return how many guest tickets are available."""
    guest_ticket_count = models.Ticket.query.filter(
        models.Ticket.ticket_type in app.APP.config['GUEST_TYPE_SLUGS'] and
        not models.Ticket.cancelled
    ).count()

    return max(
        0,
        app.APP.config['GUEST_TICKETS_AVAILABLE'] - guest_ticket_count
    )

def _total_tickets_available(user):
    return max(0, min(
        app.APP.config['MAX_TICKETS'] - user.tickets.filter(
            models.Ticket.cancelled == False
        ).count(),
        app.APP.config['MAX_TICKETS_PER_TRANSACTION']
    ))

def _type_limit_per_person(user, ticket_type):
    if ticket_type.limit_per_person == -1:
        return LARGE_NUMBER

    return max(0, ticket_type.limit_per_person - user.tickets.filter(
        models.Ticket.ticket_type == ticket_type.slug
    ).filter(
        models.Ticket.cancelled == False
    ).count())

def _type_total_limit(ticket_type):
    if ticket_type.total_limit == -1:
        return LARGE_NUMBER

    return max(0, ticket_type.total_limit - models.Ticket.query.filter(
        models.Ticket.ticket_type == ticket_type.slug
    ).filter(
        models.Ticket.cancelled == False
    ).count())

def _get_ticket_limit(user, ticket_type, ticket_info):
    """Get the number of tickets of |type| that |user| can purchase.

    Args:
        user: (models.User) The user purchasing tickets.
        ticket_type: (eisitirio.helpers.ticket_type.TicketType) the type of
            ticket being purchased

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
        _guest_tickets_available(),
        _total_tickets_available(user),
        []
    )

    for ticket_type in app.APP.config['TICKET_TYPES']:
        if ticket_type.can_buy(user):
            ticket_limit = _get_ticket_limit(user, ticket_type, ticket_info)

            if ticket_limit > 0:
                ticket_info.ticket_types.append((ticket_type, ticket_limit))

    return ticket_info

def validate_tickets(ticket_info, num_tickets, ticket_names):
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

    if len(ticket_names) > total_ticket_count:
        flashes.append("You have entered too many ticket names.")

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

def create_tickets(user, ticket_info, num_tickets, ticket_names):
    """Create the ticket objects from the user's selection."""
    tickets = [
        models.Ticket(user, ticket_type.slug, ticket_type.price)
        for ticket_type, _ in ticket_info.ticket_types
        for _ in xrange(num_tickets[ticket_type.slug])
    ]

    for i, name in enumerate(ticket_names):
        tickets[i].name = name

    return tickets

def check_payment_method(flashes):
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

def check_postage(flashes):
    if not APP.config['ENABLE_POSTAGE']:
        return None, None

    postage = None
    address = None

    if 'postage' not in flask.request.form:
        flashes.append('You must select a postage option')
    elif flask.request.form['postage'] == 'graduand':
        return postage_option.PostageOption(
            'Tickets included in Graduand pack',
            'graduand',
            0,
            'Your tickets will be included in your Graduand pack.',
            False
        ), None
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
