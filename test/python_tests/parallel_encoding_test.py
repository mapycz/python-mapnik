from nose.tools import eq_
import mapnik

def test_encode():
    im = mapnik.Image(256, 256)
    tiles = {
        1: im.view(0, 0, 256, 256),
        2: im.view(0, 0, 256, 256),
        3: ["do not encode"],
    }
    mapnik.encode_parallel(tiles, "png8")
    eq_(type(tiles[1]), bytes)
    eq_(type(tiles[2]), bytes)
    eq_(type(tiles[3]), list)
