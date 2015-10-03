# coding: utf-8
"""Helper function for drawing a graph and displaying it as a view."""

from __future__ import unicode_literals

import collections
import StringIO

from matplotlib import dates
from matplotlib import pyplot
import flask

from kebleball.database import models

COLORS = 'rgbcmyk'
POINTS = '^os*+xDH'
STYLES = [c + p + '-' for p in POINTS for c in COLORS]

_PlotDescriptor = collections.namedtuple('PlotDescriptor',
                                         ['timestamps', 'datapoints',
                                          'line_style', 'label',
                                          'current_value'])
class PlotDescriptor(_PlotDescriptor):
    """Describe a plot on a graph.

    Fields:
        timestamps: (list(datetime.datetime)) List of timestamps for the points
            to plot. Must be the same length as |datapoints|
        datapoints: (list(number)) List of data points corresponding to the
            entries in |timestamps|. Must be the same length as |timestamps|
        line_style: (str) A matplotlib descriptor of a line style.
        label: (str) The label to use for this plot in the legend
        current_value: (number) The current value of this statistic to display
            in the legend.
    """

def create_plot(group):
    """Create a plot for a set of statistics.

    Retrieves the data from the database and transforms it into a set of plot
    descriptors, and passes these to |render_plot| to create the graph.

    Args:
        group: (str) The statistics group to plot.

    Returns:
        a flask response object with the plot as a PNG image file
    """
    statistics = models.Statistic.query.filter(
        models.Statistic.group == group
    ).order_by(
        models.Statistic.timestamp
    ).all()

    style_index = 0

    plots = {}

    for statistic in statistics:
        if statistic.statistic not in plots:
            plots[statistic.statistic] = {
                'timestamps': [],
                'datapoints': [],
                'line_style': STYLES[style_index],
                'current_value': 0
            }
            style_index = (style_index + 1) % len(STYLES)

        plots[statistic.statistic]['timestamps'].append(statistic.timestamp)
        plots[statistic.statistic]['datapoints'].append(statistic.value)
        plots[statistic.statistic]['current_value'] = statistic.value

    return render_plot(
        [
            PlotDescriptor(
                timestamps=plot['timestamps'],
                datapoints=plot['datapoints'],
                line_style=plot['line_style'],
                current_value=plot['current_value'],
                label=label
            ) for (label, plot) in plots
        ],
        statistics[0].timestamp,
        statistics[-1].timestamp
    )

def render_plot(plots, x_lim_min, x_lim_max):
    """Render a graph as a view.

    Takes a set of plot descriptors for timeseries, and renders a line graph
    showing the plots.

    Args:
        plots: (list(PlotDescriptor)) list of plots to render
        x_lim_min: (datetime.datetime) the minimum timestamp to plot on the x
            axis
        x_lim_max: (datetime.datetime) the maximum timestamp to plot on the x
            axis

    Returns:
        a flask response object with the plot as a PNG image file
    """
    fig, axes = pyplot.subplots()

    for plot in plots:
        axes.plot_date(
            plot.timestamps,
            plot.datapoints,
            plot.line_style,
            label=(plot.label + ' - ' + str(plot.current_value)),
            markevery=18
        )


    axes.set_xlim(x_lim_min, x_lim_max)
    axes.grid(True, 'major', 'y')
    legend = axes.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    axes.spines['top'].set_visible(False)
    axes.spines['right'].set_visible(False)
    axes.xaxis.set_major_locator(dates.DayLocator())
    axes.xaxis.set_major_formatter(dates.DateFormatter('%a %d %B %Y'))

    axes.fmt_xdata = dates.DateFormatter('%Y-%m-%d %H:%M:%S')
    fig.autofmt_xdate()

    image = StringIO.StringIO()
    pyplot.savefig(
        image,
        format='png',
        bbox_extra_artists=(legend,),
        bbox_inches='tight',
        facecolor='white'
    )

    image.seek(0)
    return flask.send_file(image, mimetype='image/png', cache_timeout=900)
