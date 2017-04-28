#!/usr/bin/env python2
# coding: utf-8
"""Script to invoke Flask-Migrate."""

from __future__ import unicode_literals

import os
import sys

import flask_script as script
# from flask.ext import script
import flask_migrate as migrate
# from flask.ext import migrate

from eisitirio import app
from eisitirio import system # pylint: disable=unused-import
from eisitirio.database import db
from eisitirio.scripts import cron
from eisitirio.scripts import fix_graduand_postage
from eisitirio.scripts import prefill
from eisitirio.scripts import run_bpython
from eisitirio.scripts import update_battels
from eisitirio.scripts import create_qr_codes

EISITIRIO_DIR = os.path.realpath(__file__).replace('command.py',
                                                   'eisitirio')

def get_app(config):
    """Load the appropriate config into the app."""
    config_files = [
        filename
        for filename in os.listdir(os.path.join(EISITIRIO_DIR, 'config'))
        if filename.startswith(config)
    ]

    if not config_files:
        print 'No matching config file.'
    elif len(config_files) > 1:
        print 'Ambiguous config argument. Candidates: {0}'.format(
            ', '.join(filename[:-3] for filename in config_files)
        )
    elif not app.APP.config.from_pyfile(
            os.path.join(EISITIRIO_DIR, 'config', config_files[0])
    ):
        print 'Could not load config file {0}'.format(
            os.path.join(EISITIRIO_DIR, 'config', config_files[0])
        )
    else:
        return app.APP

    sys.exit(-1)

script.Server.help = 'Run the development server'

MIGRATE = migrate.Migrate(app.APP, db.DB)

MANAGER = script.Manager(get_app, with_default_commands=False)

MANAGER.add_option('config', default=None,
                   help="Configuration file to load before running commands")

MANAGER.add_command('bpython', run_bpython.BpythonCommand)
MANAGER.add_command('cron', cron.CronCommand)
MANAGER.add_command('fix_graduand_postage',
                    fix_graduand_postage.FixGraduandPostageCommand)
MANAGER.add_command('db', migrate.MigrateCommand)
MANAGER.add_command('prefill', prefill.PrefillCommand)
MANAGER.add_command('run', script.Server)
MANAGER.add_command('update_battels', update_battels.UpdateBattelsCommand)
MANAGER.add_command('send_qr_tickets', create_qr_codes.CreateQRCodes)

if __name__ == '__main__':
    MANAGER.run()
