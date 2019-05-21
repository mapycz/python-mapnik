#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import tempfile

from nose.tools import eq_, raises

import mapnik

from .utilities import execution_path, run_all, compare_file_size


def setup():
    # All of the paths used are relative, if we run the tests
    # from another directory we need to chdir()
    os.chdir(execution_path('.'))

def test_preview_mvt():
    mvt = mapnik.VectorTileMerc(28, 12, 5)

    with open('data/tile3.mvt', 'rb') as f:
        buf = f.read();
        eq_(isinstance(buf, bytes), True)
        mapnik.merge_compressed_buffer(mvt, buf)

    im = mapnik.Image(4096, 4096)
    mapnik.preview_mvt_merc(mvt, im)

    expected = 'images/mvt/tile3.preview.expected.png'
    actual = 'images/mvt/tile3.preview.actual.png'
    im.save(actual, 'png32')
    eq_(compare_file_size(actual, expected, 100), True)
