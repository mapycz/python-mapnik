#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import traceback

from nose.plugins.errorclass import ErrorClass, ErrorClassPlugin
from nose.tools import assert_almost_equal

import mapnik

PYTHON3 = sys.version_info[0] == 3
READ_FLAGS = 'rb' if PYTHON3 else 'r'
if PYTHON3:
    xrange = range

HERE = os.path.dirname(__file__)


def execution_path(filename):
    return os.path.join(os.path.dirname(
        sys._getframe(1).f_code.co_filename), filename)


class Todo(Exception):
    pass


class TodoPlugin(ErrorClassPlugin):
    name = "todo"

    todo = ErrorClass(Todo, label='TODO', isfailure=False)


def contains_word(word, bytestring_):
    """
    Checks that a bytestring contains a given word. len(bytestring) should be
    a multiple of len(word).

    >>> contains_word("abcd", "abcd"*5)
    True

    >>> contains_word("ab", "ba"*5)
    False

    >>> contains_word("ab", "ab"*5+"a")
    Traceback (most recent call last):
    ...
    AssertionError: len(bytestring_) not multiple of len(word)
    """
    n = len(word)
    assert len(bytestring_) % n == 0, "len(bytestring_) not multiple of len(word)"
    chunks = [bytestring_[i:i + n] for i in xrange(0, len(bytestring_), n)]
    return word in chunks


def pixel2channels(pixel):
    alpha = (pixel >> 24) & 0xff
    red = pixel & 0xff
    green = (pixel >> 8) & 0xff
    blue = (pixel >> 16) & 0xff
    return red, green, blue, alpha


def pixel2rgba(pixel):
    return 'rgba(%s,%s,%s,%s)' % pixel2channels(pixel)


def get_unique_colors(im):
    pixels = []
    for x in range(im.width()):
        for y in range(im.height()):
            pixel = im.get_pixel(x, y)
            if pixel not in pixels:
                pixels.append(pixel)
    pixels = sorted(pixels)
    return list(map(pixel2rgba, pixels))


def run_all(iterable):
    failed = 0
    for test in iterable:
        try:
            test()
            sys.stderr.write("\x1b[32m✓ \x1b[m" + test.__name__ + "\x1b[m\n")
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()
            failed += 1
            sys.stderr.write("\x1b[31m✘ \x1b[m" + test.__name__ + "\x1b[m\n")
            for mline in traceback.format_exception_only(exc_type, exc_value):
                for line in mline.rstrip().split("\n"):
                    sys.stderr.write("  \x1b[31m" + line + "\x1b[m\n")
            sys.stderr.write("  Traceback:\n")
            for mline in traceback.format_tb(exc_tb):
                for line in mline.rstrip().split("\n"):
                    if not 'utilities.py' in line and not 'trivial.py' in line and not line.strip() == 'test()':
                        sys.stderr.write("  " + line + "\n")
        sys.stderr.flush()
    return failed


def side_by_side_image(left_im, right_im):
    width = left_im.width() + 1 + right_im.width()
    height = max(left_im.height(), right_im.height())
    im = mapnik.Image(width, height)
    im.composite(left_im, mapnik.CompositeOp.src_over, 1.0, 0, 0)
    if width > 80:
        im.composite(
            mapnik.Image.open(
                HERE +
                '/images/expected.png'),
            mapnik.CompositeOp.difference,
            1.0,
            0,
            0)
    im.composite(
        right_im,
        mapnik.CompositeOp.src_over,
        1.0,
        left_im.width() + 1,
        0)
    if width > 80:
        im.composite(
            mapnik.Image.open(
                HERE +
                '/images/actual.png'),
            mapnik.CompositeOp.difference,
            1.0,
            left_im.width() +
            1,
            0)
    return im


def assert_box2d_almost_equal(a, b, msg=None):
    msg = msg or ("%r != %r" % (a, b))
    assert_almost_equal(a.minx, b.minx, msg=msg)
    assert_almost_equal(a.maxx, b.maxx, msg=msg)
    assert_almost_equal(a.miny, b.miny, msg=msg)
    assert_almost_equal(a.maxy, b.maxy, msg=msg)


def compare_file_size(file1, file2, max_diff):
    size1 = os.path.getsize(file1);
    size2 = os.path.getsize(file2);
    return abs(size1 - size2) < max_diff

