# coding: utf-8
"""Views related to the group purchase process."""

from __future__ import unicode_literals

from flask.ext import login
import flask

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.logic import purchase_logic
from eisitirio.logic import payment_logic

APP = app.APP
DB = db.DB

GROUP_PURCHASE = flask.Blueprint('group_purchase', __name__)

@GROUP_PURCHASE.route('/purchase/group/dashboard')
@login.login_required
def dashboard():
    """Display the group purchase dashboard."""
    if not login.current_user.purchase_group:
        return flask.render_template(
            'group_purchase/dashboard.html'
        )

    ticket_info = purchase_logic.get_group_ticket_info(login.current_user)

@GROUP_PURCHASE.route('/purchase/group/create')
@login.login_required
def create():
    """Create a new purchase group."""
    if login.current_user.purchase_group:
        flask.flash('You are already a member of a purchase group', 'error')
    else:
        group = models.PurchaseGroup(login.current_user)

        DB.session.add(group)
        DB.session.commit()

    return flask.redirect(flask.url_for('group_purchase.dashboard'))

@GROUP_PURCHASE.route('/purchase/group/join', methods=['GET', 'POST'])
@login.login_required
def join():
    """Join a pre-existing purchase group."""
    if flask.request.method != 'POST':
        return flask.redirect(flask.request.referrer or
                              flask.url_for('dashboard.dashboard_home'))

    if login.current_user.purchase_group:
        flask.flash('You are already a member of a purchase group', 'error')
    else:
        group = None
        if (
                'code' in flask.request.form and
                flask.request.form['code'] != ''
        ):
            group = models.PurchaseGroup.get_by_code(flask.request.form['code'])

        if group:
            group.members.append(login.current_user)
            DB.session.commit()
        else:
            flask.flash('Could not join group', 'error')

    return flask.redirect(flask.url_for('group_purchase.dashboard'))

@GROUP_PURCHASE.route('/purchase/group/disband')
@login.login_required
def disband():
    """Disband a purchase group, cancelling all requests.

    Only the leader of a group can disband it.
    """
    if (
            not login.current_user.purchase_group or
            not login.current_user == login.current_user.purchase_group.leader
    ):
        flask.flash('You are not the leader of any purchase group', 'error')
    else:
        DB.session.delete(login.current_user.purchase_group)
        DB.session.commit()

    return flask.redirect(flask.url_for('group_purchase.dashboard'))

@GROUP_PURCHASE.route('/purchase/group/leave')
@login.login_required
def leave():
    """Leave a purchase group.

    The leader of a group may not leave it.
    """
    if not login.current_user.purchase_group:
        flask.flash('You are not a member of any purchase group', 'error')
    elif login.current_user == login.current_user.purchase_group.leader:
        flask.flash('You can not leave a purchase group you lead', 'error')
    else:
        login.current_user.purchase_group.members.remove(login.current_user)
        DB.session.commit()

    return flask.redirect(flask.url_for('group_purchase.dashboard'))
