#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nose.tools import eq_

import mapnik

from .utilities import run_all


# Map initialization


def test_layer_init():
    l = mapnik.Layer('test')
    eq_(l.name, 'test')
    eq_(l.srs, '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
    eq_(l.envelope(), mapnik.Box2d())
    eq_(l.clear_label_cache, False)
    eq_(l.cache_features, False)
    eq_(l.visible(1), True)
    eq_(l.active, True)
    eq_(l.datasource, None)
    eq_(l.queryable, False)
    eq_(l.minimum_scale_denominator, 0.0)
    eq_(l.maximum_scale_denominator > 1e+6, True)
    eq_(l.group_by, "")
    eq_(l.maximum_extent, None)
    eq_(l.buffer_size, None)
    eq_(len(l.styles), 0)

def test_layer_sublayers():
    m = mapnik.Map(512, 512)
    strict = True
    filename = "../data/good_maps/nested-layers-1.xml"
    mapnik.load_map(m, filename, strict)

    eq_(len(m.layers), 1)
    eq_(len(m.layers[0].layers), 1)

    sublayer = m.layers[0].layers[0]
    eq_(sublayer.name, "text")

if __name__ == "__main__":
    exit(run_all(eval(x) for x in dir() if x.startswith("test_")))
