# -*- coding: utf-8 -*-

"""
Created on Wed Jul 22 16:23:47 2015

@author: sergey
"""

from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='reWork server modules',
    version='1.0',
    packages=find_packages(),
    long_description=open(join(dirname(__file__), 'README.txt')).read(),
)
