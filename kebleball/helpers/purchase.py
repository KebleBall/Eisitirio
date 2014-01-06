from kebleball.app import app
from kebleball.database.ticket import Ticket
from kebleball.database.user import User
from kebleball.database.waiting import Waiting
from datetime import datetime

def canBuy(user):
    if isinstance(app.config['TICKETS_ON_SALE'], datetime):
        if app.config['TICKETS_ON_SALE'] > datetime.utcnow():
            on_sale = 0
        else:
            on_sale = app.config['TICKETS_AVAILABLE']
    else:
        on_sale = app.config['TICKETS_AVAILABLE'] if app.config['TICKETS_ON_SALE'] else 0

    # Don't allow people to buy tickets unless waiting list is empty
    if Waiting.query.count() > 0:
        on_sale = 0

    return max(
        min(
            on_sale,
            app.config['TICKETS_AVAILABLE'] - Ticket.count(),
            app.config['MAX_TICKETS_PER_TRANSACTION'],
            app.config['MAX_UNPAID_TICKETS'] - user.tickets.filter(Ticket.paid==False).count(),
            app.config['MAX_TICKETS'] - user.tickets.count()
        ),
        0
    )

def canWait(user):
    can_wait_for = max(
        min(
            app.config['MAX_TICKETS_WAITING'] - user.waitingFor(),
            app.config['MAX_TICKETS'] - user.tickets.count()
        ),
        0
    )

    if isinstance(app.config['WAITING_OPEN'], datetime):
        if app.config['WAITING_OPEN'] > datetime.utcnow():
            return 0
        else:
            return can_wait_for
    else:
        return can_wait_for if app.config['WAITING_OPEN'] else 0

    return