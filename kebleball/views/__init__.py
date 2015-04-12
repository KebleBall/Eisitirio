# coding: utf-8
"""Helper giving access to all the views."""

# We make an exception to the usual rule of only importing modules here for
# neatness.
#
# pylint: disable=unused-import

from kebleball.views.admin import ADMIN
from kebleball.views.admin_users import ADMIN_USERS
from kebleball.views.admin_tickets import ADMIN_TICKETS
from kebleball.views.ajax import AJAX
from kebleball.views.dashboard import DASHBOARD
from kebleball.views.front import FRONT
from kebleball.views.purchase import PURCHASE
from kebleball.views.resale import RESALE
