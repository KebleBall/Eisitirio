# coding: utf-8
"""Permissions/possessions related to purchase groups."""

from eisitirio import app
from eisitirio.database import models

@models.User.possession()
def purchase_group(user):
    return user.purchase_group is not None

@models.User.permission()
def join_group(_, group):
    return group.members.count() < app.APP.config['MAX_GROUP_MEMBERS']
