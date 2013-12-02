PyBBM - Django forum solution
=============================

.. image:: https://secure.travis-ci.org/thoas/pybbm.png?branch=master
    :alt: Build Status
    :target: http://travis-ci.org/thoas/pybbm


Installation
------------

1. Download the package on GitHub_ or simply install it via PyPi
2. Add ``pybb`` to your ``INSTALLED_APPS`` ::

    INSTALLED_APPS = (
        'pybb',
    )

3. Sync your database using ``syncdb`` command from django command line
4. Configure settings


In the wild
-----------

This forum engine is used by:

- `Madmoizelle <http://forums.madmoizelle.com>`_
- `Ulule <http://ulule.com>`_

.. _GitHub: https://github.com/thoas/pybbm
