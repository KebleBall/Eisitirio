# coding: utf-8
"""Views related to administering vouchers."""

from __future__ import unicode_literals

import datetime
import re

from dateutil import parser
from flask.ext import login
import flask

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.helpers import login_manager
from eisitirio.helpers import util

APP = app.APP
DB = db.DB

ADMIN_VOUCHERS = flask.Blueprint('admin_vouchers', __name__)

@ADMIN_VOUCHERS.route('/admin/vouchers', methods=['GET', 'POST'])
@ADMIN_VOUCHERS.route('/admin/vouchers/page/<int:page>',
                      methods=['GET', 'POST'])
@login.login_required
@login_manager.admin_required
def vouchers(page=1):
    """Manage vouchers.

    Handles the creation of discount vouchers, and allows their deletion.
    """
    form = {}

    if flask.request.method == 'POST':
        form = flask.request.form

        success = True

        expires = None

        if 'expires' in form and form['expires'] != '':
            try:
                expires = parser.parse(form['expires'])
                if expires < datetime.datetime.utcnow():
                    flask.flash(
                        'Expiry date cannot be in the past',
                        'warning'
                    )
                    success = False
            except (KeyError, ValueError) as _:
                flask.flash(
                    'Could not parse expiry date',
                    'warning'
                )
                success = False

        if 'voucher_type' not in form or form['voucher_type'] == '':
            flask.flash(
                'You must select a discount type',
                'warning'
            )
            success = False
        elif form['voucher_type'] == 'Fixed Price':
            value = util.parse_pounds_pence(flask.request.form,
                                            'fixed_price_pounds',
                                            'fixed_price_pence')
        elif form['voucher_type'] == 'Fixed Discount':
            value = util.parse_pounds_pence(flask.request.form,
                                            'fixed_discount_pounds',
                                            'fixed_discount_pence')

            if value == 0:
                flask.flash(
                    'Cannot give no discount',
                    'warning'
                )
                success = False
        else:
            try:
                value = int(form['fixed_discount'])
            except ValueError:
                value = 0

            if value == 0:
                flask.flash(
                    'Cannot give 0% discount',
                    'warning'
                )
                success = False
            elif value > 100:
                flask.flash(
                    'Cannot give greater than 100% discount',
                    'warning'
                )
                success = False

        if not re.match('[a-zA-Z0-9]+', form['voucher_prefix']):
            flask.flash(
                (
                    'Voucher prefix must be non-empty and contain only '
                    'letters and numbers'
                ),
                'warning'
            )
            success = False

        if success:
            num_vouchers = int(form['num_vouchers'])
            single_use = 'single_use' in form and form['single_use'] == 'yes'

            for _ in xrange(num_vouchers):
                key = util.generate_key(10)
                voucher = models.Voucher(
                    '{0}-{1}'.format(
                        form['voucher_prefix'],
                        key
                    ),
                    expires,
                    form['voucher_type'],
                    value,
                    form['applies_to'],
                    single_use
                )
                DB.session.add(voucher)

            DB.session.commit()

            flask.flash(
                'Voucher(s) created successfully',
                'success'
            )

            form = {}

    voucher_query = models.Voucher.query

    if 'search' in flask.request.args:
        voucher_query = voucher_query.filter(
            models.Voucher.code.like(
                '%{0}%'.format(
                    flask.request.args['search']
                )
            )
        )

    voucher_results = voucher_query.paginate(
        page,
        10
    )

    return flask.render_template(
        'admin_vouchers/vouchers.html',
        form=form,
        vouchers=voucher_results
    )

@ADMIN_VOUCHERS.route('/admin/voucher/<int:voucher_id>/delete')
@login.login_required
@login_manager.admin_required
def delete_voucher(voucher_id):
    """Delete a discount voucher."""
    voucher = models.Voucher.get_by_id(voucher_id)

    if voucher:
        DB.session.delete(voucher)
        DB.session.commit()
        flask.flash(
            'Voucher deleted successfully',
            'success'
        )
    else:
        flask.flash(
            'Could not find voucher to delete',
            'warning'
        )

    return flask.redirect(flask.request.referrer or
                          flask.url_for('admin_vouchers.vouchers'))
