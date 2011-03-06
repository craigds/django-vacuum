#!/usr/bin/env python

from distutils.core import setup
import vacuum

setup(name='django-vacuum',
    version=vacuum.VERSION,
    description='Sucks the lint from your Django templates',
    author='Craig de Stigter',
    author_email='craig.ds@gmail.com',
    url='https://github.com/craigds/django-vacuum',
    packages=[
        'vacuum',
        'vacuum.management',
        'vacuum.management.commands',
    ],
    package_data={
        'vacuum': ['entities.txt'],
    }
)
