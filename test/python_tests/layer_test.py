#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nose.tools import eq_
import os

import mapnik

from .utilities import execution_path, run_all


def setup():
    # All of the paths used are relative, if we run the tests
    # from another directory we need to chdir()
    os.chdir(execution_path('.'))


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
    eq_(l.opacity, 1.0)
    eq_(l.comp_op, None)
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


def test_layer_sublayers_modify():
    m = mapnik.Map(512, 512)
    m.layers.append(mapnik.Layer("1"))
    m.layers.append(mapnik.Layer("2"))
    eq_(len(m.layers), 2)

    layer2 = m.layers[1]
    eq_(layer2.name, "2")
    layer2.layers.append(mapnik.Layer("2_1"))
    layer2.layers.append(mapnik.Layer("2_2"))
    eq_(len(layer2.layers), 2)
    del layer2.layers[0]
    eq_(len(layer2.layers), 1)
    eq_(layer2.layers[0].name, "2_2")

    del m.layers[:]
    eq_(len(m.layers), 0)


def test_layer_comp_op():
    l = mapnik.Layer('test')
    eq_(l.comp_op, None)
    l.comp_op = mapnik.CompositeOp.dst_out
    eq_(l.comp_op, mapnik.CompositeOp.dst_out)


def test_layer_opacity():
    l = mapnik.Layer('test')
    eq_(l.opacity, 1.0)
    l.opacity = 0.5
    eq_(l.opacity, 0.5)


if __name__ == "__main__":
    setup()
    exit(run_all(eval(x) for x in dir() if x.startswith("test_")))
