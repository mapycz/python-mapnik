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

def test_render_mvt_basic():
    m = mapnik.Map(256, 256)
    mapnik.load_map(m, 'styles/mvt_render_test.xml')
    mvt = mapnik.VectorTileMerc(28, 12, 5)

    with open('data/tile3.mvt', 'rb') as f:
        buf = f.read();
        eq_(isinstance(buf, bytes), True)
        mapnik.merge_compressed_buffer(mvt, buf)

    im = mapnik.Image(m.width, m.height)
    mapnik.render_mvt_merc(mvt, m, im)

    expected = 'images/mvt/tile3.expected.png'
    actual = 'images/mvt/tile3.actual.png'
    im.save(actual, 'png32')
    eq_(compare_file_size(actual, expected, 100), True)


def test_render_mvt_merc():
    m = mapnik.Map(512, 512)
    mapnik.load_map(m, '../data-visual/styles/road-casings-grouped-rendering.xml')
    mvt = mapnik.VectorTileMerc(8796, 5374, 14)

    im2 = mapnik.Image(m.width, m.height)
    m.zoom_to_box(mvt.extent)
    mapnik.render(m, im2)
    actual2 = 'images/mvt/render_mvt_merc.classic.actual.png'
    expected2 = 'images/mvt/render_mvt_merc.classic.expected.png'
    im2.save(actual2, 'png32')
    eq_(compare_file_size(actual2, expected2, 100), True)

    mvt_buffer = mapnik.create_mvt_merc(m,
        mvt.x, mvt.y, mvt.z)
    mapnik.merge_compressed_buffer(mvt, mvt_buffer)

    im = mapnik.Image(m.width, m.height)
    mapnik.render_mvt_merc(mvt, m, im)

    actual = 'images/mvt/render_mvt_merc.mvt.actual.png'
    im.save(actual, 'png32')
    expected = 'images/mvt/render_mvt_merc.mvt.expected.png'
    eq_(compare_file_size(actual, expected, 100), True)


def test_render_mvt_merc_nested_layers():
    m = mapnik.Map(512, 512)
    mapnik.load_map(m, '../data-visual/styles/nested-layers-1.xml')
    mvt = mapnik.VectorTileMerc(0, 0, 0)

    im2 = mapnik.Image(m.width, m.height)
    m.zoom_to_box(mvt.extent)
    mapnik.render(m, im2)
    actual2 = 'images/mvt/nested_layers.classic.actual.png'
    expected2 = 'images/mvt/nested_layers.classic.expected.png'
    im2.save(actual2, 'png32')
    eq_(compare_file_size(actual2, expected2, 100), True)

    mvt_buffer = mapnik.create_mvt_merc(m,
        mvt.x, mvt.y, mvt.z)

    # Check number of layers of the MVT
    vti = mapnik.VectorTileInfo()
    vti.parse_from_string(mvt_buffer)
    eq_(vti.layers_size(), 2);

    mapnik.merge_compressed_buffer(mvt, mvt_buffer)

    m = mapnik.Map(512, 512)
    # Load a version of the style with no datasources
    mapnik.load_map(m, 'styles/nested-layers-1.xml')
    im = mapnik.Image(m.width, m.height)
    mapnik.render_mvt_merc(mvt, m, im)

    actual = 'images/mvt/nested_layers.mvt.actual.png'
    im.save(actual, 'png32')
    expected = 'images/mvt/nested_layers.mvt.expected.png'
    eq_(compare_file_size(actual, expected, 100), True)

def test_render_mvt_raster_with_large_overzoom():
    mvt = mapnik.VectorTileMerc(2788, 6533, 14);

    with open('images/mvt/14_2788_6533.webp', 'rb') as f:
        mapnik.add_image_layer(mvt, '_image', f.read())

    # Look into the tile if there is the image
    vti = mapnik.VectorTileInfo()
    vti.parse_from_string(mvt.get_buffer())
    eq_(vti.layers_size(), 1);
    layer = vti.layers(0)
    eq_(layer.features_size(), 1)
    feature = layer.features(0)
    raster = feature.raster()
    eq_(len(raster), 98618)
    img = mapnik.Image.frombuffer(raster)
    eq_(img.width(), 512)
    eq_(img.height(), 512)

    m = mapnik.Map(256, 256)
    mapnik.load_map(m, 'styles/large_overzoom.xml')

    im = mapnik.Image(m.width, m.height)
    mapnik.render_mvt_merc(mvt, m, im,
        x=2855279, y=6690105, z=24,
        scale_factor=1, buffer_size=256)

    expected = 'images/mvt/large_overzoom.expected.png'
    actual = 'images/mvt/large_overzoom.actual.png'
    im.save(actual, 'png32')
    eq_(compare_file_size(actual, expected, 100), True)

def test_render_mvt_with_optional_arguments():
    # A dubious test ported from node-mapnik.
    # TODO: make these optional arguments to have actual effect.
    mvt = mapnik.VectorTileMerc(28, 12, 5)

    with open('data/tile3.mvt', 'rb') as f:
        buf = f.read();
        eq_(isinstance(buf, bytes), True)
        mapnik.merge_compressed_buffer(mvt, buf)

    eq_(len(mvt.get_buffer()), 987)
    eq_(mvt.is_painted, True)
    eq_(mvt.is_empty, False)

    m = mapnik.Map(256, 256)
    m.maximum_extent = mapnik.Box2d(-20037508.34, -20037508.34, 20037508.34, 20037508.34)
    mapnik.load_map(m, 'styles/mvt_render_test.xml')

    im = mapnik.Image(m.width, m.height)
    mapnik.render_mvt_merc(mvt, m, im,
        scale_factor=1.2, scale_denom=1.5,
        variables={ 'pizza': 'pie' })

    expected = 'images/mvt/tile3.expected.png'
    actual = 'images/mvt/tile3-2.actual.png'
    im.save(actual, 'png32')
    eq_(compare_file_size(actual, expected, 100), True)


if __name__ == "__main__":
    setup()
    exit(run_all(eval(x) for x in dir() if x.startswith("test_")))
