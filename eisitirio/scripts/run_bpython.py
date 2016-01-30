#!/usr/bin/env python2
# coding: utf-8
"""Script to run bpython with the appropriate env."""

from flask.ext import script
from bpython import curtsies

from eisitirio import app
from eisitirio.database import db
from eisitirio.database import models

class BpythonCommand(script.Command):
    """Flask-Script command for running bpython with the appropriate env."""

    help = 'Run bpython in the given environment'

    @staticmethod
    def run():
        """Call the bpython main loop

        Starts bpython with the app, database and models as local variables.
        """

        curtsies.main([], {'APP': app.APP, 'DB': db.DB, 'models': models})
