#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from nose.tools import assert_almost_equal, eq_, raises

import mapnik

from .utilities import READ_FLAGS, execution_path, get_unique_colors, run_all

PYTHON3 = sys.version_info[0] == 3
if PYTHON3:
    buffer = memoryview


def setup():
    # All of the paths used are relative, if we run the tests
    # from another directory we need to chdir()
    os.chdir(execution_path('.'))


def test_encode():
    im = mapnik.Image(256, 256)
    tiles = {
        1: im.view(0, 0, 256, 256),
        2: im.view(0, 0, 256, 256),
        3: "do not encode",
    }
    mapnik.encode_parallel(tiles, "png8")
    #eq_(im.get_type(), mapnik.ImageType.rgba8)



if __name__ == "__main__":
    setup()
    exit(run_all(eval(x) for x in dir() if x.startswith("test_")))
