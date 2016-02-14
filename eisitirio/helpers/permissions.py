# coding: utf-8
"""Helper system for permissions and properties logic."""

import collections

PERMISSIONS = collections.defaultdict(dict)
POSSESSIONS = collections.defaultdict(dict)

def permission(model, name=None):
    """Decorator to add a new permission accessible at |model|.can_|name|().

    If |name| is not given, defaults to the name of the decorated function
    """
    def decorator(func):
        """Add the permission function to the store."""
        PERMISSIONS[model][name or func.__name__] = func

        return func

    return decorator

def possession(model, name=None):
    """Decorator to add a new possession accessible at |model|.has_|name|().

    """
    def decorator(func):
        """Add the posession function to the store."""
        POSSESSIONS[model][name or func.__name__] = func

        return func

    return decorator
