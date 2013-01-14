import django.dispatch

mentioned = django.dispatch.Signal(providing_args=['user', 'post'])
