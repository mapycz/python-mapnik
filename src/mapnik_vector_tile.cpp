/*****************************************************************************
 *
 * This file is part of Mapnik (c++ mapping toolkit)
 *
 * Copyright (C) 2015 Artem Pavlenko, Jean-Francois Doyon
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 *
 *****************************************************************************/

#include <mapnik/config.hpp>

#include <mapbox/mapnik-vector-tile/vector_tile_merc_tile.hpp>
#include <mapbox/mapnik-vector-tile/vector_tile_processor.hpp>
#include <mapbox/mapnik-vector-tile/vector_tile_compression.hpp>

// libprotobuf
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-parameter"
#pragma GCC diagnostic ignored "-Wsign-conversion"
#include "vector_tile.pb.h"
#pragma GCC diagnostic pop

#define BOOST_PYTHON_MAX_ARITY 20
#include <boost/python.hpp>

std::string create_mvt_merc(
    mapnik::Map const& map,
    std::uint64_t x,
    std::uint64_t y,
    std::uint64_t z,
    std::uint32_t tile_size,
    std::int32_t buffer_size,
    double scale_denom,
    int offset_x,
    int offset_y,
    bool style_level_filter,
    double simplify_distance,
    double area_threshold,
    bool process_all_rings,
    bool multi_polygon_union,
    mapnik::vector_tile_impl::polygon_fill_type fill_type,
    std::string const& image_format,
    mapnik::scaling_method_e scaling_method,
    std::launch threading_mode
    )
{
    mapnik::vector_tile_impl::processor proc(map);

    proc.set_area_threshold(area_threshold);
    proc.set_simplify_distance(simplify_distance);
    proc.set_multi_polygon_union(multi_polygon_union);
    proc.set_process_all_rings(process_all_rings);
    proc.set_fill_type(fill_type);
    proc.set_image_format(image_format);
    proc.set_scaling_method(scaling_method);
    proc.set_threading_mode(threading_mode);

    mapnik::vector_tile_impl::merc_tile tile(proc.create_tile(
        x, y, z, tile_size, buffer_size, scale_denom,
        offset_x, offset_y, style_level_filter));
    return tile.get_buffer();
}

std::string compress_mvt(std::string const & input)
{
    std::string output;
    mapnik::vector_tile_impl::zlib_compress(input, output);
    return output;
}

void export_tile()
{
    using namespace boost::python;
    using vector_tile::Tile;
    using vector_tile::Tile_Layer;

    class_<Tile_Layer>("VectorTileLayer")
        .def("parse_from_string", &Tile_Layer::ParseFromString,
             arg("buffer"),
             "Load data from PBF.")
        .def("features_size", &Tile_Layer::features_size,
             "Returns a number of features in the layer.")
        .def("name", &Tile_Layer::name,
             return_value_policy<copy_const_reference>())
        ;

    class_<Tile>("VectorTile")
        .def("parse_from_string", &Tile::ParseFromString,
             arg("buffer"),
             "Load data from PBF.")
        .def("layers", static_cast<Tile_Layer const& (Tile::*)(int) const>(&Tile::layers),
             arg("index"),
             return_internal_reference<>(),
             "Returns a layer by its index.")
        .def("layers_size", &Tile::layers_size,
             "Returns a number of layers.")
        ;
}

void export_create_mvt()
{
    using namespace boost::python;

    using fill_type = mapnik::vector_tile_impl::polygon_fill_type;
    enum_<fill_type>("polygon_fill_type")
        .value("even_odd", fill_type::even_odd_fill)
        .value("non_zero", fill_type::non_zero_fill)
        .value("positive", fill_type::positive_fill)
        .value("negative", fill_type::negative_fill)
    ;

    enum_<std::launch>("threading_mode")
        .value("async", std::launch::async)
        .value("deferred", std::launch::deferred)
    ;

    def("create_mvt_merc", &create_mvt_merc,
        (arg("map"),
         arg("x"),
         arg("y"),
         arg("z"),
         arg("tile_size") = 4096,
         arg("buffer_size") = 0,
         arg("scale_denom") = 0.0,
         arg("offset_x") = 0,
         arg("offset_y") = 0,
         // Filter features by rule conditions in styles.
         arg("style_level_filter") = false,
         // Positive value in the units of vector tile coordinates will turn on
         // douglas-peucker with given simplification distance.
         arg("simplify_distance") = 0.0,
         // Skip polygons with area below this threshold,
         // in vector tile coordinates units.
         arg("area_threshold") = 0.1,
         // Process all rings even exterior ring is degenerated
         // or smaller than area_threshold.
         arg("process_all_rings") = false,
         // Conflate multi-polygon.
         arg("multi_polygon_union") = false,
         // Polygon fill strategy used during clipping.
         arg("fill_type") = fill_type::positive_fill,
         // Raster image format.
         arg("image_format") = std::string("webp"),
         // Raster scaling method.
         arg("scaling_method") = mapnik::SCALING_BILINEAR,
         // Allows parallel processing of layers.
         arg("threading_mode") = std::launch::deferred),
        "Creates MVT into a buffer\n"
        "mapnik.create_mvt_merc(m, 2257, 1393, 12, 4096, 0, 0, 0, 0)");

    def("compress_mvt", &compress_mvt,
        "gzip compression");
}

void export_mvt()
{
    export_create_mvt();
    export_tile();
}

