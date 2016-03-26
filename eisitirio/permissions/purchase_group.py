# coding: utf-8
"""Permissions/possessions related to purchase groups."""

from __future__ import unicode_literals

from eisitirio import app
from eisitirio.database import models

@models.User.permission()
def join_group(_, group):
    """Can the user join the given group."""
    return group.members.count() < app.APP.config['MAX_GROUP_MEMBERS']
