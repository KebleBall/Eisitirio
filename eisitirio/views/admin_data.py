# coding: utf-8
"""Views related to data and statistics."""

from __future__ import unicode_literals

import csv
import os
import StringIO

from flask.ext import login
import flask

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models
from eisitirio.database import static
from eisitirio.helpers import login_manager
from eisitirio.helpers import statistics

APP = app.APP
DB = db.DB

ADMIN_DATA = flask.Blueprint('admin_data', __name__)

@ADMIN_DATA.route('/admin/statistics')
@login.login_required
@login_manager.admin_required
def view_statistics():
    """Display statistics about the ball.

    Computes a number of statistics about the ball (live), and displays them
    alongside graphs.
    """
    return flask.render_template(
        'admin_data/statistics.html',
        statistic_groups=static.STATISTIC_GROUPS,
        revenue=statistics.get_revenue(),
        num_postage=models.Postage.query.filter(
            models.Postage.paid == True # pylint: disable=singleton-comparison
        ).filter(
            models.Postage.cancelled == False # pylint: disable=singleton-comparison
        ).filter(
            models.Postage.postage_type !=
            APP.config['GRADUAND_POSTAGE_OPTION'].name
        ).count()
    )

@ADMIN_DATA.route('/admin/graphs/<group>')
@login.login_required
@login_manager.admin_required
def graph(group):
    """Render graph showing statistics for the given statistic group."""
    image_filename = os.path.join(
        APP.config['GRAPH_STORAGE_FOLDER'],
        '{0}.png'.format(group)
    )
    return flask.send_file(
        image_filename,
        mimetype='image/png',
        cache_timeout=900
    )

@ADMIN_DATA.route('/admin/data/<group>')
@login.login_required
@login_manager.admin_required
def data(group):
    """Export statistics as CSV.

    Exports the statistics used to render the graphs as a CSV file.
    """
    stats = models.Statistic.query.filter(
        models.Statistic.group == group.title()
    ).order_by(
        models.Statistic.timestamp
    ).all()

    csvdata = StringIO.StringIO()
    csvwriter = csv.writer(csvdata)

    for stat in stats:
        csvwriter.writerow(
            [
                stat.timestamp.strftime('%c'),
                stat.statistic,
                stat.value
            ]
        )

    csvdata.seek(0)
    return flask.send_file(csvdata, mimetype='text/csv', cache_timeout=900)

@ADMIN_DATA.route('/admin/dietary_requirements')
@login.login_required
@login_manager.admin_required
def dietary_requirements():
    """Export dietary requirements as a csv."""
    requirements = models.DietaryRequirements.query.all()

    csvdata = StringIO.StringIO()
    csvwriter = csv.writer(csvdata)

    csvwriter.writerow([
        'Pescetarian',
        'Vegetarian',
        'Vegan',
        'Gluten free',
        'Nut free',
        'Dairy free',
        'Egg free',
        'Seafood free',
        'Other',
    ])

    for requirement in requirements:
        csvwriter.writerow([
            'Yes' if requirement.pescetarian else 'No',
            'Yes' if requirement.vegetarian else 'No',
            'Yes' if requirement.vegan else 'No',
            'Yes' if requirement.gluten_free else 'No',
            'Yes' if requirement.nut_free else 'No',
            'Yes' if requirement.dairy_free else 'No',
            'Yes' if requirement.egg_free else 'No',
            'Yes' if requirement.seafood_free else 'No',
            requirement.other
        ])

    csvdata.seek(0)
    return flask.send_file(csvdata, mimetype='text/csv', cache_timeout=900)
