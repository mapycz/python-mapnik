import os

from nose.tools import eq_

import mapnik

from .utilities import execution_path, run_all


def setup():
    # All of the paths used are relative, if we run the tests
    # from another directory we need to chdir()
    os.chdir(execution_path('.'))


def test_clearing_image_data():
    im = mapnik.Image(256, 256)
    # make sure it equals itself
    bytes = im.tostring()
    eq_(im.tostring(), bytes)
    # set background, then clear
    im.fill(mapnik.Color('green'))
    eq_(im.tostring() != bytes, True)
    # clear image, should now equal original
    im.clear()
    eq_(im.tostring(), bytes)


def make_map():
    ds = mapnik.MemoryDatasource()
    context = mapnik.Context()
    context.push('Name')
    pixel_key = 1
    f = mapnik.Feature(context, pixel_key)
    f['Name'] = str(pixel_key)
    f.geometry = mapnik.Geometry.from_wkt(
        'POLYGON ((0 0, 0 256, 256 256, 256 0, 0 0))')
    ds.add_feature(f)
    s = mapnik.Style()
    r = mapnik.Rule()
    symb = mapnik.PolygonSymbolizer()
    r.symbols.append(symb)
    s.rules.append(r)
    lyr = mapnik.Layer('Places')
    lyr.datasource = ds
    lyr.styles.append('places_labels')
    width, height = 256, 256
    m = mapnik.Map(width, height)
    m.append_style('places_labels', s)
    m.layers.append(lyr)
    m.zoom_all()
    return m

if __name__ == "__main__":
    setup()
    exit(run_all(eval(x) for x in dir() if x.startswith("test_")))
