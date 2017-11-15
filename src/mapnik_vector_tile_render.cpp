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
#include <mapnik/layer.hpp>
#include <mapnik/map.hpp>
#include <mapnik/projection.hpp>
#include <mapnik/image_any.hpp>
#include <mapnik/agg_renderer.hpp>
#include <mapnik/scale_denominator.hpp>

#include <mapbox/mapnik-vector-tile/vector_tile_tile.hpp>
#include <mapbox/mapnik-vector-tile/vector_tile_projection.hpp>
#define MAPNIK_VECTOR_TILE_LIBRARY
#include <mapbox/mapnik-vector-tile/vector_tile_load_tile.hpp>
#include <mapbox/mapnik-vector-tile/vector_tile_datasource_pbf.hpp>
#include <mapbox/mapnik-vector-tile/vector_tile_merc_tile.hpp>

#include <boost/python.hpp>

#include "python_to_value.hpp"


bool set_mvt_datasource(mapnik::layer & lyr,
                        mapnik::box2d<double> const& buffered_extent,
                        std::string const& map_srs,
                        mapnik::vector_tile_impl::merc_tile const& tile)
{
    protozero::pbf_reader layer_msg;
    if (tile.layer_reader(lyr.name(), layer_msg))
    {
        lyr.set_srs(map_srs);
        using ds_type = mapnik::vector_tile_impl::tile_datasource_pbf;
        using ds_holder_type = std::shared_ptr<ds_type>;
        ds_holder_type ds = std::make_shared<ds_type>(
            layer_msg, tile.x(), tile.y(), tile.z());
        ds->set_envelope(buffered_extent);
        lyr.set_datasource(ds);
        return true;
    }
    return false;
}

void prepare_sublayers(mapnik::layer & lyr,
                       mapnik::box2d<double> const& buffered_extent,
                       double scale_denom,
                       std::string const& map_srs,
                       mapnik::vector_tile_impl::merc_tile const& tile)
{
    for (auto & sublyr : lyr.layers())
    {
        bool sublayer_used = sublyr.visible(scale_denom) &&
            set_mvt_datasource(sublyr, buffered_extent, map_srs, tile);
        sublyr.set_active(sublayer_used);
        if (sublayer_used)
        {
            prepare_sublayers(sublyr, buffered_extent,
                              scale_denom, map_srs, tile);
        }
    }
}

template <typename Renderer>
void process_layers(Renderer & ren,
                    mapnik::request const& m_req,
                    mapnik::projection const& map_proj,
                    std::vector<mapnik::layer> const& layers,
                    double scale_denom,
                    std::string const& map_srs,
                    mapnik::vector_tile_impl::merc_tile const& tile)
{
    mapnik::box2d<double> buffered_extent = m_req.get_buffered_extent();
    for (auto const& lyr : layers)
    {
        if (lyr.visible(scale_denom))
        {
            mapnik::layer lyr_copy(lyr);
            if (set_mvt_datasource(lyr_copy, buffered_extent, map_srs, tile))
            {
                prepare_sublayers(lyr_copy, buffered_extent,
                                  scale_denom, map_srs, tile);
                protozero::pbf_reader layer_msg;
                std::set<std::string> names;
                ren.apply_to_layer(lyr_copy,
                                   ren,
                                   map_proj,
                                   m_req.scale(),
                                   scale_denom,
                                   m_req.width(),
                                   m_req.height(),
                                   m_req.extent(),
                                   m_req.buffer_size(),
                                   names);
            }
        }
    }
}

void render_mvt_merc(mapnik::vector_tile_impl::merc_tile const& mvt,
                     mapnik::Map const& map,
                     mapnik::image_any& image,
                     boost::python::dict const& vars_dict,
                     double scale_factor,
                     double scale_denominator,
                     boost::optional<std::int32_t> buffer_size,
                     boost::optional<std::uint64_t> const& x,
                     boost::optional<std::uint64_t> const& y,
                     boost::optional<std::uint64_t> const& z)
{
    mapnik::projection map_proj(map.srs(), true);

    mapnik::box2d<double> map_extent = mvt.extent();

    if (x || y || z)
    {
        map_extent = mapnik::vector_tile_impl::merc_extent(1, *x, *y, *z);
    }

    mapnik::request m_req(image.width(), image.height(), map_extent);
    m_req.set_buffer_size(buffer_size ? *buffer_size : map.buffer_size());

    if (scale_factor <= 0.0)
    {
        scale_factor = 1.0;
    }

    double scale_denom = scale_denominator;
    if (scale_denom <= 0.0)
    {
        scale_denom = mapnik::scale_denominator(m_req.scale(), map_proj.is_geographic());
    }
    scale_denom *= scale_factor;

    std::vector<mapnik::layer> const& layers = map.layers();
    mapnik::attributes vars = mapnik::dict2attr(vars_dict);

    if (image.is<mapnik::image_rgba8>())
    {
        mapnik::image_rgba8 & image_data = mapnik::util::get<mapnik::image_rgba8>(image);
        mapnik::agg_renderer<mapnik::image_rgba8> ren(map,
                                                      m_req,
                                                      vars,
                                                      image_data,
                                                      scale_factor);
        ren.start_map_processing(map);
        process_layers(ren, m_req, map_proj, layers, scale_denom, map.srs(), mvt);
        ren.end_map_processing(map);
    }
    else
    {
        throw std::runtime_error("This image type is not currently supported for rendering.");
    }
}

void export_mvt_render()
{
    using namespace boost::python;

    def("render_mvt_merc", &render_mvt_merc,
        (arg("tile"),
         arg("map"),
         arg("image"),
         arg("variables") = boost::python::dict(),
         arg("scale_factor") = 1.0,
         // Override auto-calculated scale denominator
         arg("scale_denom") = 0.0,
         // Override buffer_size from Map
         arg("buffer_size") = boost::optional<std::int32_t>(),
         // Override MVT coordinates
         arg("x") = boost::optional<std::uint64_t>(),
         arg("y") = boost::optional<std::uint64_t>(),
         arg("z") = boost::optional<std::uint64_t>()),
        "Render vector tile in Mercator to a surface/image");
}

