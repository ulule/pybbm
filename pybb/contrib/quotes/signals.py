import django.dispatch

quoted = django.dispatch.Signal(providing_args=['user', 'from_post', 'to_post'])
