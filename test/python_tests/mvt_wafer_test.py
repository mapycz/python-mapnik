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

def test_create_mvt_merc_style_level_filter_1():
    style = """
        <Map srs="+init=epsg:3857">
            <Layer name="polygon" srs="+init=epsg:4326">
                <Datasource>
                    <Parameter name="type">geojson</Parameter>
                    <Parameter name="inline">
                        {"type":"Polygon","coordinates":[[
                            [ 10,  10],
                            [-10,  10],
                            [-10, -10],
                            [ 10, -10],
                            [ 10,  10]
                        ]]}
                    </Parameter>
                </Datasource>
            </Layer>
        </Map>
    """
    mapnikMap = mapnik.Map(256, 256)
    mapnik.load_map_from_string(mapnikMap, style)

    wafer = mapnik.create_mvt_wafer_merc(mapnikMap, 0, 0, 3, 8)
    eq_(len(wafer), 64)
    tile_buffer = wafer[3 * 8 + 3]
    tile = mapnik.VectorTileInfo()
    tile.parse_from_string(tile_buffer);
    eq_(tile.layers_size(), 1);
    eq_(tile.layers(0).features_size(), 1)


if __name__ == "__main__":
    setup()
    exit(run_all(eval(x) for x in dir() if x.startswith("test_")))
