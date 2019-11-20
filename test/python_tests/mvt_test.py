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

def test_create_mvt_merc_style_level_filter_1():
    m = mapnik.Map(256, 256)
    mapnik.load_map(m, 'styles/rule_level_filter_style.xml')
    mvt_buffer = mapnik.create_mvt_merc(m, 2048, 2047, 12, style_level_filter=True);

    tile = mapnik.VectorTileInfo()
    tile.parse_from_string(mvt_buffer);
    eq_(tile.layers_size(), 2);

    eq_(tile.layers(0).features_size(), 1)
    eq_(tile.layers(1).features_size(), 1)

    eq_(tile.layers(0).name(), "L1")
    eq_(tile.layers(1).name(), "L2")

def test_create_mvt_merc_style_level_filter_2():
    m = mapnik.Map(256, 256)
    mapnik.load_map(m, 'styles/rule_level_filter_style.xml')
    mvt_buffer = mapnik.create_mvt_merc(m, 2048, 2047, 12, style_level_filter=False);

    tile = mapnik.VectorTileInfo()
    tile.parse_from_string(mvt_buffer);
    eq_(tile.layers_size(), 2);

    eq_(tile.layers(0).features_size(), 1)
    eq_(tile.layers(1).features_size(), 2)

    eq_(tile.layers(0).name(), "L1")
    eq_(tile.layers(1).name(), "L2")

def test_create_mvt_merc_filter_by_scale_denom_1():
    m = mapnik.Map(256, 256)
    mapnik.load_map(m, 'styles/style_level_filter_style.xml')
    mvt_buffer = mapnik.create_mvt_merc(
        m, 2048, 2047, 12,
        scale_denom=200000,
        style_level_filter=True);

    tile = mapnik.VectorTileInfo()
    tile.parse_from_string(mvt_buffer);
    eq_(tile.layers_size(), 2);

    eq_(tile.layers(0).features_size(), 1)
    eq_(tile.layers(1).features_size(), 2)

    eq_(tile.layers(0).name(), "L1")
    eq_(tile.layers(1).name(), "L2")

def test_create_mvt_merc_filter_by_scale_denom_2():
    m = mapnik.Map(256, 256)
    mapnik.load_map(m, 'styles/style_level_filter_style.xml')
    mvt_buffer = mapnik.create_mvt_merc(
        m, 2048, 2047, 12,
        scale_denom=2 * 200000,
        style_level_filter=True);

    tile = mapnik.VectorTileInfo()
    tile.parse_from_string(mvt_buffer);
    eq_(tile.layers_size(), 1);

    eq_(tile.layers(0).features_size(), 2)

    eq_(tile.layers(0).name(), "L2")

def test_create_mvt_merc_filter_by_scale_denom_3():
    m = mapnik.Map(256, 256)
    mapnik.load_map(m, 'styles/style_level_filter_style.xml')
    mvt_buffer = mapnik.create_mvt_merc(
        m, 2048, 2047, 12,
        scale_denom=200000,
        style_level_filter=False);

    tile = mapnik.VectorTileInfo()
    tile.parse_from_string(mvt_buffer);
    eq_(tile.layers_size(), 2);

    eq_(tile.layers(0).features_size(), 1)
    eq_(tile.layers(1).features_size(), 2)

    eq_(tile.layers(0).name(), "L1")
    eq_(tile.layers(1).name(), "L2")

def test_create_mvt_merc_filter_by_scale_denom_4():
    m = mapnik.Map(256, 256)
    mapnik.load_map(m, 'styles/style_level_filter_style.xml')
    mvt_buffer = mapnik.create_mvt_merc(
        m, 2048, 2047, 12,
        scale_denom=2 * 200000,
        style_level_filter=False);

    tile = mapnik.VectorTileInfo()
    tile.parse_from_string(mvt_buffer);
    eq_(tile.layers_size(), 2);

    eq_(tile.layers(0).features_size(), 1)
    eq_(tile.layers(1).features_size(), 2)

    eq_(tile.layers(0).name(), "L1")
    eq_(tile.layers(1).name(), "L2")

def test_create_mvt_merc_with_raster():
    m = mapnik.Map(256, 256)
    mapnik.load_map(m, 'styles/raster.xml')
    mvt = mapnik.VectorTileMerc(136, 86, 8)
    mvt_buffer = mapnik.create_mvt_merc(m,
        mvt.x, mvt.y, mvt.z,
        tile_size=512,
        image_format="tiff")

    vti = mapnik.VectorTileInfo()
    vti.parse_from_string(mvt_buffer);
    eq_(vti.layers_size(), 1);
    layer = vti.layers(0)
    eq_(layer.features_size(), 1)
    feature = layer.features(0)
    raster = feature.raster()
    eq_(abs(len(raster) - 270050) < 10, True)
    img = mapnik.Image.frombuffer(raster)
    eq_(img.width(), 512)
    eq_(img.height(), 512)

    mapnik.merge_compressed_buffer(mvt, mvt_buffer)

    im = mapnik.Image(m.width, m.height)
    mapnik.render_mvt_merc(mvt, m, im)

    actual = 'images/mvt/raster.mvt.actual.png'
    im.save(actual, 'png32')
    expected = 'images/mvt/raster.mvt.expected.png'
    eq_(compare_file_size(actual, expected, 100), True)

    im2 = mapnik.Image(m.width, m.height)
    m.zoom_to_box(mvt.extent)
    mapnik.render(m, im2)
    actual2 = 'images/mvt/raster.actual.png'
    expected2 = 'images/mvt/raster.expected.png'
    im2.save(actual2, 'png32')
    eq_(compare_file_size(actual2, expected2, 100), True)

def test_compress():
    content = b'test' * 100
    eq_(len(content), 400)
    compressed = mapnik.compress_mvt(content)
    eq_(len(compressed), 29)
    decompressed = mapnik.decompress_mvt(compressed)
    eq_(len(decompressed), 400)

def test_buffer_size_from_style():
    m = mapnik.Map(256, 256)
    mapnik.load_map(m, 'styles/map_buffer_size.xml')
    mvt_buffer = mapnik.create_mvt_merc(
        m, 2048, 2047, 12,
        buffer_size=None);

    tile = mapnik.VectorTileInfo()
    tile.parse_from_string(mvt_buffer);

    eq_(tile.layers_size(), 1);
    eq_(tile.layers(0).features_size(), 2)

def test_buffer_size_from_style_by_default():
    m = mapnik.Map(256, 256)
    mapnik.load_map(m, 'styles/map_buffer_size.xml')
    mvt_buffer = mapnik.create_mvt_merc(
        m, 2048, 2047, 12);

    tile = mapnik.VectorTileInfo()
    tile.parse_from_string(mvt_buffer);

    eq_(tile.layers_size(), 1);
    eq_(tile.layers(0).features_size(), 2)

def test_buffer_size_from_style_overriden_by_parameter():
    m = mapnik.Map(256, 256)
    mapnik.load_map(m, 'styles/map_buffer_size.xml')
    mvt_buffer = mapnik.create_mvt_merc(
        m, 2048, 2047, 12,
        buffer_size=0);

    tile = mapnik.VectorTileInfo()
    tile.parse_from_string(mvt_buffer);

    eq_(tile.layers_size(), 1);
    eq_(tile.layers(0).features_size(), 1)

if __name__ == "__main__":
    setup()
    exit(run_all(eval(x) for x in dir() if x.startswith("test_")))
