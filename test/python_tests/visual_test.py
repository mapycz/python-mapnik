#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess

from nose.tools import eq_, raises

from .utilities import execution_path

def setup():
    # All of the paths used are relative, if we run the tests
    # from another directory we need to chdir()
    os.chdir(execution_path('.'))

# Include visual tests to the suite
def test_visual():
    subprocess.check_call(['../visual.py', '-q', '--only-errors'])

