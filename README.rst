django-vacuum - Sucks the lint from your Django templates
--------------------------------------------------------

``django-vacuum`` checks your Django templates for nasties.


Installation:
=============

1. Get the latest source from github (there's no releases yet, sorry)::

    git clone git://github.com/craigds/django-vacuum.git

2. Run setup.py::

    cd django-vacuum
    python setup.py build
    sudo python setup.py install

3. Add 'vacuum' to your INSTALLED_APPS in your django settings file::

    INSTALLED_APPS = (
        # ...,
        'vacuum',
    )


Checking your templates:
========================

Just run::

    django-admin.py checktemplates

Reporting Bugs:
===============

I've only tested this on Django 1.2 with Python 2.6. You *will* find bugs.
When you do, please report them on Github at https://github.com/craigds/django-vacuum/issues

Ideas for new rules (things to check for) are welcome there also.
