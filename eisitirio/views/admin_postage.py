# coding: utf-8
"""Views related to administering postage."""

from __future__ import unicode_literals

from flask.ext import login
import flask

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.helpers import login_manager

APP = app.APP
DB = db.DB

ADMIN_POSTAGE = flask.Blueprint('admin_postage', __name__)

@ADMIN_POSTAGE.route('/admin/postage/<postage_type>')
@ADMIN_POSTAGE.route('/admin/postage')
@ADMIN_POSTAGE.route('/admin/postage/<postage_type>/page/<int:page>')
@ADMIN_POSTAGE.route('/admin/postage/page/<int:page>')
@login.login_required
@login_manager.admin_required
def postage_dashboard(postage_type=None, page=1):
    """Provide an interface for packing posted tickets."""
    postage_query = models.Postage.query.filter(
        models.Postage.paid == True # pylint: disable=singleton-comparison
    ).filter(
        models.Postage.cancelled == False # pylint: disable=singleton-comparison
    ).filter(
        models.Postage.posted == False # pylint: disable=singleton-comparison
    ).order_by(
        models.Postage.postage_type
    ).order_by(
        models.Postage.owner.surname
    ).order_by(
        models.Postage.owner.forenames
    )

    if postage_type == 'graduand':
        postage_query = postage_query.filter(
            models.Postage.postage_type ==
            APP.config['GRADUAND_POSTAGE_TYPE'].name
        )
    elif postage_type == 'posted':
        postage_query = postage_query.filter(
            models.Postage.postage_type !=
            APP.config['GRADUAND_POSTAGE_TYPE'].name
        )

    return flask.render_template(
        'admin_postage/postage.html',
        postage_entries=postage_query.paginate(page=page),
        postage_type=postage_type
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
        flask.flash('Not all of the tickets for this entry have been posted.',
                    'error')
    else:
        postage.posted = True

        DB.session.commit()

        flask.flash('Entry marked as posted.', 'success')

    return flask.redirect(flask.request.referrer or
                          flask.url_for('admin_postage.postage_dashboard'))
