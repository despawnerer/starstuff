#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name='Fallen',
    version='0.0.2',
    author=u'Алексей Шельф',
    author_email='despawn@gmail.com',
    license='GPL',
    packages=['fallen'],
    package_data={'fallen': ['ui/*']},
    scripts=['scripts/fallen'],
)

