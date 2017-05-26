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
    int offset_y
{
    mapnik::vector_tile_impl::processor proc(map);
    mapnik::vector_tile_impl::merc_tile tile(proc.create_tile(
        x, y, z, tile_size, buffer_size, scale_denom, offset_x, offset_y));
    return tile.get_buffer();
}

std::string compress_mvt(std::string const & input)
{
    std::string output;
    mapnik::vector_tile_impl::zlib_compress(input, output);
    return output;
}

void export_mvt()
{
    using namespace boost::python;

    def("create_mvt_merc", &create_mvt_merc,
        (arg("map"),
         arg("x"),
         arg("y"),
         arg("z"),
         arg("tile_size") = 4096,
         arg("buffer_size") = 0,
         arg("scale_denom") = 0.0,
         arg("offset_x") = 0,
         arg("offset_y") = 0),
        "Creates MVT into a buffer\n"
        "mapnik.create_mvt_merc(m, 2257, 1393, 12, 4096, 0, 0, 0, 0)");

    def("compress_mvt", &compress_mvt,
        "gzip compression");
}
