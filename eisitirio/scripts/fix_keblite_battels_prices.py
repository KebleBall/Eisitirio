# coding: utf-8
"""Script to update battels accounts for keblites that were overcharged"""

from __future__ import unicode_literals

from flask.ext import script
from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.logic.custom_logic import ticket_logic

APP = app.APP
DB = db.DB

f1 = open("./output", "w+")

class FixKebliteBattelsPricesCommand(script.Command):
    """Flask-Script command for rebating keblites that were charged too much"""

    help = 'rebating keblites that were charged too much'

    @staticmethod
    def run():
        """Update the battels"""

        with APP.app_context():
            #APP.log_manager.log_event('Started Keblite Rebates', in_app=False)

            successful_rebates = 0
            failed_rebates = 0

            for user in models.User.query.all():
                if user_needs_rebate(user):
                    if refund_user(user):
                        successful_rebates += 1
                    else:
                        failed_rebates += 1

            print >> f1, "SUCCESSFUL REBATES: {0}".format(successful_rebates)
            print >> f1, "FAILED REBATES: {0}".format(failed_rebates)

            # APP.log_manager.log_event(
            #     'Finished Keblite Rebates. Successes: {0}, failures: {1}'.format(
            #         successful_rebates,
            #         failed_rebates
            #     ),
            #     in_app = False
            # )

def user_needs_rebate(user):
    return all(ticket.price_ > 9000 for ticket in user.tickets) and ticket_logic.can_buy_keblite(user) and (user.active_ticket_count > 0)

def refund_user(user):
    print >> f1, '###########################################################################'
    print >> f1, '########### Refund user {0}:{1} {2} pounds #######'.format(user.full_name, user.email, 1000)
    print >> f1, '########### Current tickets that the user owns are #######'
    print >> f1, '+--------------------------------------------------------------------------'
    for i, ticket in enumerate(user.tickets):
        print >> f1, '| Ticket {0}: {1} price: {2}'.format(i, ticket, ticket.price_pounds)
    print >> f1, '+--------------------------------------------------------------------------'
    return True

#def refund_user(user):
#
#    # Get the admin user
#    admin_user = models.User.get_by_id(1);
#
#    refunded_ticket = None
#    for ticket in tickets:
#        if ticket.price_ > 9000:
#            refunded_ticket = ticket
#            break
#
#    if refunded_ticket is None:
#        #APP.log_manager.log_event(
#        #    'Failed: Keblite Battels Refund',
#        #    tickets=user.tickets,
#        #    user=user,
#        #    in_app=False
#        #)
#
#    else:
#        refunded_ticket.add_note("Refund 10 pounds for keblite ticket")
#        refund_transaction = models.AdminFeeTransactionItem(
#                    models.BattelsTransaction(user),
#                    create_admin_fee_refund(1000, "Keblite Refund", user, admin_user),
#                    is_refund=True
#                )
#
#
#        print refund_transaction.value
#        
#        #APP.log_manager.log_event(
#        #    'Keblite Battels Refund',
#        #    tickets=user.tickets,
#        #    user=user,
#        #    in_app=False
#        #)
