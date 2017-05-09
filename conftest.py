import os
import sys

from django import setup

sys.path.insert(0, os.path.dirname(__file__))


def pytest_configure():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')
    setup()
