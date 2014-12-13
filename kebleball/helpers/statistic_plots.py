from flask import send_file
from matplotlib import pyplot
from matplotlib.dates import DayLocator, DateFormatter
from StringIO import StringIO

def create_plot(plots, x_lim_min, x_lim_max):
    fig, axes = pyplot.subplots()

    for label, plot in plots.iteritems():
        axes.plot_date(
            plot['timestamps'],
            plot['datapoints'],
            plot['line'],
            label=(label + ' - ' + str(plot['currentValue'])),
            markevery=18
        )


    axes.set_xlim(x_lim_min, x_lim_max)
    axes.grid(True, 'major', 'y')
    legend = axes.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    axes.spines['top'].set_visible(False)
    axes.spines['right'].set_visible(False)
    axes.xaxis.set_major_locator(DayLocator())
    axes.xaxis.set_major_formatter(DateFormatter('%a %d %B %Y'))

    axes.fmt_xdata = DateFormatter('%Y-%m-%d %H:%M:%S')
    fig.autofmt_xdate()

    image = StringIO()
    pyplot.savefig(
        image,
        format="png",
        bbox_extra_artists=(legend,),
        bbox_inches='tight',
        facecolor='white'
    )

    image.seek(0)
    return send_file(image, mimetype="image/png", cache_timeout=900)
