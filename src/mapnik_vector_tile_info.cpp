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

// libprotobuf
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-parameter"
#pragma GCC diagnostic ignored "-Wsign-conversion"
#include "vector_tile.pb.h"
#pragma GCC diagnostic pop

#include <boost/python.hpp>

// TODO: Make this conversion automatic
boost::python::object feature_get_raster(vector_tile::Tile_Feature const& feature)
{
    std::string const& raster = feature.raster();
    return boost::python::object(boost::python::handle<>(
        PyBytes_FromStringAndSize(raster.data(), raster.size())));
}

void export_mvt_info()
{
    using namespace boost::python;
    using vector_tile::Tile;
    using vector_tile::Tile_Layer;
    using vector_tile::Tile_Feature;

    class_<Tile_Feature>("VectorTileFeatureInfo")
        .def("has_raster", &Tile_Feature::has_raster)
        .def("raster", feature_get_raster)
        ;

    using features_overload = Tile_Feature const& (Tile_Layer::*)(int) const;

    class_<Tile_Layer>("VectorTileLayerInfo")
        .def("parse_from_string", &Tile_Layer::ParseFromString,
             arg("buffer"),
             "Load data from PBF.")
        .def("features_size", &Tile_Layer::features_size,
             "Returns a number of features in the layer.")
        .def("name", &Tile_Layer::name,
             return_value_policy<copy_const_reference>())
        .def("features_size", &Tile_Layer::features_size)
        .def("features", static_cast<features_overload>(&Tile_Layer::features),
             arg("index"),
             return_internal_reference<>())
        ;

    using layers_overload = Tile_Layer const& (Tile::*)(int) const;

    class_<Tile>("VectorTileInfo")
        .def("parse_from_string", &Tile::ParseFromString,
             arg("buffer"),
             "Load data from PBF.")
        .def("layers", static_cast<layers_overload>(&Tile::layers),
             arg("index"),
             return_internal_reference<>(),
             "Returns a layer by its index.")
        .def("layers_size", &Tile::layers_size,
             "Returns a number of layers.")
        ;
}

