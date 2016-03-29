# coding: utf-8
"""Views related to administering postage."""

from __future__ import unicode_literals

import csv
import StringIO

from flask.ext import login
import flask

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.helpers import login_manager

APP = app.APP
DB = db.DB

ADMIN_POSTAGE = flask.Blueprint('admin_postage', __name__)

def get_postage_query(postage_type, unposted_only=True):
    """Get a query object for the postage entries."""
    postage_query = models.Postage.query.filter(
        models.Postage.paid == True # pylint: disable=singleton-comparison
    ).join(
        models.Postage.owner
    ).filter(
        models.Postage.cancelled == False # pylint: disable=singleton-comparison
    ).order_by(
        models.Postage.postage_type
    ).order_by(
        models.User.surname
    ).order_by(
        models.User.forenames
    )

    if unposted_only:
        postage_query = postage_query.filter(
            models.Postage.posted == False # pylint: disable=singleton-comparison
        )

    if postage_type == 'graduand':
        return postage_query.filter(
            models.Postage.postage_type ==
            APP.config['GRADUAND_POSTAGE_OPTION'].name
        )
    elif postage_type == 'posted':
        return postage_query.filter(
            models.Postage.postage_type !=
            APP.config['GRADUAND_POSTAGE_OPTION'].name
        )

    return postage_query

@ADMIN_POSTAGE.route('/admin/postage/<postage_type>')
@ADMIN_POSTAGE.route('/admin/postage')
@ADMIN_POSTAGE.route('/admin/postage/<postage_type>/page/<int:page>')
@ADMIN_POSTAGE.route('/admin/postage/page/<int:page>')
@login.login_required
@login_manager.admin_required
def postage_dashboard(postage_type=None, page=1):
    """Provide an interface for packing posted tickets."""
    return flask.render_template(
        'admin_postage/postage_dashboard.html',
        postage_entries=get_postage_query(postage_type).paginate(page=page),
        postage_type=postage_type,
        page=page
    )

@ADMIN_POSTAGE.route('/admin/postage/<int:postage_id>/mark_posted')
@login.login_required
@login_manager.admin_required
def mark_as_posted(postage_id):
    """Mark a postage entry as packed/posted."""
    postage = models.Postage.get_by_id(postage_id)

    if not postage:
        flask.flash('Could not load postage entry', 'error')
    elif not all(ticket.collected for ticket in postage.tickets):
        flask.flash('Not all of the tickets for this entry have been assigned.',
                    'error')
    else:
        postage.posted = True

        DB.session.commit()

        flask.flash('Entry marked as packed/posted.', 'success')

    return flask.redirect(flask.request.referrer or
                          flask.url_for('admin_postage.postage_dashboard'))


@ADMIN_POSTAGE.route('/admin/postage/export/<unposted_only>')
@ADMIN_POSTAGE.route('/admin/postage/export/<unposted_only>/<postage_type>')
@login.login_required
@login_manager.admin_required
def export_postage(unposted_only, postage_type=None):
    """Export postage entries as CSV.

    Exports the statistics used to render the graphs as a CSV file.
    """
    csvdata = StringIO.StringIO()
    csvwriter = csv.writer(csvdata)

    csvwriter.writerow(
        [
            'user_id',
            'user_name',
            'postage_type',
            'address',
            'status',
            'num_tickets',
            'ticket_ids',
        ]
    )

    for postage in get_postage_query(postage_type, unposted_only == 'unposted'):
        csvwriter.writerow(
            [
                postage.owner.object_id,
                postage.owner.full_name,
                postage.postage_type,
                postage.address if postage.address is not None else 'N/A',
                '{0}Posted/Packed'.format('' if postage.posted else 'Not '),
                postage.tickets.count(),
                ';'.join(str(ticket.object_id) for ticket in postage.tickets),
            ]
        )

    csvdata.seek(0)
    return flask.send_file(csvdata, mimetype='text/csv', cache_timeout=900)
