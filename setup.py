#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name='Starstuff',
    version='0.0.1',
    author=u'Алексей Шельф',
    author_email='despawn@gmail.com',
    license='GPL',
    packages=['starstuff'],
    package_data={'starstuff': ['ui/*']},
    scripts=['scripts/starstuff'],
)

