# coding: utf-8
"""Helper giving access to all the views."""

from __future__ import unicode_literals

# We make an exception to the usual rule of only importing modules here for
# neatness.
#
# pylint: disable=unused-import

from eisitirio.views.admin import ADMIN
from eisitirio.views.admin_photos import ADMIN_PHOTOS
from eisitirio.views.admin_tickets import ADMIN_TICKETS
from eisitirio.views.admin_users import ADMIN_USERS
from eisitirio.views.ajax import AJAX
from eisitirio.views.dashboard import DASHBOARD
from eisitirio.views.front import FRONT
from eisitirio.views.group_purchase import GROUP_PURCHASE
from eisitirio.views.purchase import PURCHASE
from eisitirio.views.resale import RESALE
