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

#include <mapbox/mapnik-vector-tile/vector_tile_processor.hpp>
#include <mapbox/mapnik-vector-tile/vector_tile_compression.hpp>
#include <mapbox/mapnik-vector-tile/vector_tile_load_tile.hpp>
#include <mapbox/mapnik-vector-tile/vector_tile_datasource_pbf.hpp>
#include <mapbox/mapnik-vector-tile/vector_tile_tile.hpp>
#include <mapbox/mapnik-vector-tile/vector_tile_merc_tile.hpp>

#define BOOST_PYTHON_MAX_ARITY 20
#include <boost/python.hpp>

boost::python::object create_mvt_merc(
    mapnik::Map const& map,
    std::uint64_t x,
    std::uint64_t y,
    std::uint64_t z,
    std::uint32_t tile_size,
    boost::optional<std::int32_t> buffer_size,
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
    std::launch threading_mode)
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

    std::string const& buffer = tile.get_buffer();
    return boost::python::object(boost::python::handle<>(
        PyBytes_FromStringAndSize(buffer.data(), buffer.size())));
}

boost::python::object compress_mvt(std::string const& input)
{
    std::string output;
    mapnik::vector_tile_impl::zlib_compress(input, output);
    return boost::python::object(boost::python::handle<>(
        PyBytes_FromStringAndSize(output.data(), output.size())));
}

boost::python::object decompress_mvt(std::string const& input)
{
    std::string output;
    mapnik::vector_tile_impl::zlib_decompress(input, output);
    return boost::python::object(boost::python::handle<>(
        PyBytes_FromStringAndSize(output.data(), output.size())));
}

void export_mvt_create()
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
         // If None, buffer size is taken from the Map.
         arg("buffer_size") = boost::optional<std::int32_t>(),
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
         arg("image_format") = std::string("tiff"),
         // Raster scaling method.
         arg("scaling_method") = mapnik::SCALING_BILINEAR,
         // Allows parallel processing of layers.
         arg("threading_mode") = std::launch::deferred),
        "Creates MVT into a buffer\n"
        "mapnik.create_mvt_merc(m, 2257, 1393, 12, 4096, 0, 0, 0, 0)");

    def("compress_mvt", &compress_mvt,
        "gzip compression");

    def("decompress_mvt", &decompress_mvt,
        "decompress zlib or gzip compressed data");
}

void merge_compressed_buffer(mapnik::vector_tile_impl::merc_tile & tile,
                             std::string const& buf)
{
    merge_from_compressed_buffer(tile, buf.data(), buf.size());
}

void add_image_layer(mapnik::vector_tile_impl::merc_tile & tile,
                     std::string const& layer_name,
                     std::string const& image_buffer)
{
    add_image_buffer_as_tile_layer(tile,
                                   layer_name,
                                   image_buffer.data(),
                                   image_buffer.size());
}

boost::python::object mvt_get_buffer(mapnik::vector_tile_impl::tile const& tile)
{
    std::string const& buf = tile.get_buffer();
    return boost::python::object(boost::python::handle<>(
        PyBytes_FromStringAndSize(buf.data(), buf.size())));
}

extern void export_mvt_render();
extern void export_mvt_info();

void export_mvt()
{
    using namespace boost::python;
    using mapnik::vector_tile_impl::tile;
    using mapnik::vector_tile_impl::merc_tile;
    using tile_size_get = std::uint32_t (tile::*)() const;
    using tile_size_set = void (tile::*)(std::uint32_t);
    using buffer_size_get = std::int32_t (tile::*)() const;
    using buffer_size_set = void (tile::*)(std::int32_t);
    using xyz_get = std::uint64_t (merc_tile::*)() const;
    using xyz_set = void (merc_tile::*)(std::uint64_t);

    class_<tile>("VectorTile",
        "Represents a MVT",
        init<mapnik::box2d<double> const&,
            std::uint32_t, std::int32_t>(
            (arg("extent"),
             arg("tile_size") = 4096,
             arg("buffer_size") = 128)
        ))
        .add_property("tile_size",
                      static_cast<tile_size_get>(&merc_tile::tile_size),
                      static_cast<tile_size_set>(&merc_tile::tile_size))
        .add_property("buffer_size",
                      static_cast<buffer_size_get>(&merc_tile::buffer_size),
                      static_cast<buffer_size_set>(&merc_tile::buffer_size))
        .add_property("is_empty", &merc_tile::is_empty)
        .add_property("is_painted", &merc_tile::is_painted)
        .add_property("extent", make_function(&merc_tile::extent,
            return_value_policy<copy_const_reference>()))
        .def("get_buffer", mvt_get_buffer)
        ;

    class_<merc_tile, bases<tile>>("VectorTileMerc",
        "A specialization of MVT for Mercator",
        init<std::uint64_t, std::uint64_t, std::uint64_t,
            std::uint32_t, std::int32_t>(
            (arg("x"), arg("y"), arg("z"),
            arg("tile_size") = 4096,
            arg("buffer_size") = 128)
        ))
        .add_property("x",
                      static_cast<xyz_get>(&merc_tile::x),
                      static_cast<xyz_set>(&merc_tile::x))
        .add_property("y",
                      static_cast<xyz_get>(&merc_tile::y),
                      static_cast<xyz_set>(&merc_tile::y))
        .add_property("z",
                      static_cast<xyz_get>(&merc_tile::z),
                      static_cast<xyz_set>(&merc_tile::z))
        ;

    def("merge_compressed_buffer", &merge_compressed_buffer,
        "Merge MVT buffer with given tile. The buffer can be compressed.");

    def("add_image_layer", &add_image_layer,
        "Creates new layer with bitmap image content.");

    export_mvt_create();
    export_mvt_info();
    export_mvt_render();
}

