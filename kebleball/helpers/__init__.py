import random, string

__all__ = ['logger', 'login_manager']

def generate_key(length, choices=None):
    if choices is None:
        choices = (
            string.ascii_lowercase +
            string.ascii_uppercase +
            string.digits
        )

    return ''.join(random.choice(choices) for x in xrange(length))