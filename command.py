#!/usr/bin/env python2
# coding: utf-8
"""Script to invoke Flask-Migrate."""

from __future__ import unicode_literals

import os
import sys

from flask.ext import script
from flask.ext import migrate

from eisitirio import app
from eisitirio import system # pylint: disable=unused-import
from eisitirio.database import db
from eisitirio.scripts import check_eway
from eisitirio.scripts import cron
from eisitirio.scripts import prefill
from eisitirio.scripts import run_bpython
from eisitirio.scripts import update_battels

def get_app(config):
    """Load the appropriate config into the app."""
    config_file = os.path.join('config', '{0}.py'.format(config))

    eisitirio_dir = os.path.realpath(__file__).replace('command.py',
                                                       'eisitirio')

    if not (
            os.path.exists(os.path.join(eisitirio_dir, config_file))
            and app.APP.config.from_pyfile(config_file)
    ):
        print 'Could not load config file {0}'.format(
            os.path.join(eisitirio_dir, config_file)
        )

        sys.exit(-1)

    return app.APP

script.Server.help = 'Run the development server'

MIGRATE = migrate.Migrate(app.APP, db.DB)

MANAGER = script.Manager(get_app, with_default_commands=False)

MANAGER.add_option('config', default=None,
                   help="Configuration file to load before running commands")

MANAGER.add_command('bpython', run_bpython.BpythonCommand)
MANAGER.add_command('check_eway', check_eway.CheckEwayCommand)
MANAGER.add_command('cron', cron.CronCommand)
MANAGER.add_command('db', migrate.MigrateCommand)
MANAGER.add_command('prefill', prefill.PrefillCommand)
MANAGER.add_command('run', script.Server)
MANAGER.add_command('update_battels', update_battels.UpdateBattelsCommand)

if __name__ == '__main__':
    MANAGER.run()
