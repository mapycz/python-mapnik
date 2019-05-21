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
#include <mapnik/load_map.hpp>

#include <mapbox/mapnik-vector-tile/vector_tile_tile.hpp>
#define MAPNIK_VECTOR_TILE_LIBRARY
#include <mapbox/mapnik-vector-tile/vector_tile_load_tile.hpp>
#include <mapbox/mapnik-vector-tile/vector_tile_datasource_pbf.hpp>
#include <mapbox/mapnik-vector-tile/vector_tile_merc_tile.hpp>

#include <boost/python.hpp>

struct preview_map
{
    static const std::string style_xml;
    mapnik::Map map;

    preview_map() : map(256, 256)
    {
        mapnik::load_map_string(map, style_xml);
    }
};

const std::string preview_map::style_xml(R"preview_style(
<Map srs="+init=epsg:3857">
    <Style name="preview">
        <Rule>
            <Filter>[mapnik::geometry_type] = linestring or [mapnik::geometry_type] = polygon</Filter>
            <LineSymbolizer
                stroke="black"
                stroke-width="1"
                />
        </Rule>
        <Rule>
            <Filter>[mapnik::geometry_type] = point</Filter>
            <MarkersSymbolizer
                allow-overlap="true"
                ignore-placement="true"
                />
        </Rule>
    </Style>

    <Layer name="preview">
        <StyleName>preview</StyleName>
    </Layer>
</Map>
)preview_style");

static const preview_map preview_map_;

void preview_mvt_merc_custom(mapnik::vector_tile_impl::merc_tile const& mvt,
                             mapnik::Map const& map,
                             mapnik::image_any& image)
{
    if (!image.is<mapnik::image_rgba8>())
    {
        throw std::runtime_error("This image type is not currently supported for rendering.");
    }

    if (map.layer_count() == 0)
    {
        throw std::runtime_error("The input style has no layers.");
    }

    const mapnik::projection map_proj(map.srs(), true);
    const mapnik::box2d<double> map_extent = mvt.extent();
    const mapnik::request m_req(image.width(), image.height(), map_extent);
    const mapnik::attributes vars;
    const double scale_denom = 0;
    const double scale_factor = 1;
    mapnik::layer layer(map.get_layer(0));

    mapnik::image_rgba8 & image_data = mapnik::util::get<mapnik::image_rgba8>(image);
    mapnik::agg_renderer<mapnik::image_rgba8> ren(map, m_req, vars, image_data, scale_factor);
    ren.start_map_processing(map);

    for (std::size_t i = 0; i < mvt.get_layers().size(); i++)
    {
        protozero::pbf_reader layer_msg;
        if (mvt.layer_reader(i, layer_msg))
        {
            using ds_type = mapnik::vector_tile_impl::tile_datasource_pbf;
            using ds_holder_type = std::shared_ptr<ds_type>;
            ds_holder_type ds = std::make_shared<ds_type>(
                layer_msg, mvt.x(), mvt.y(), mvt.z());
            ds->set_envelope(map_extent);
            layer.set_datasource(ds);

            std::set<std::string> names;
            ren.apply_to_layer(layer,
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

    ren.end_map_processing(map);
}

void preview_mvt_merc(mapnik::vector_tile_impl::merc_tile const& mvt,
                      mapnik::image_any& image)
{
    preview_mvt_merc_custom(mvt, preview_map_.map, image);
}

void export_mvt_preview()
{
    using namespace boost::python;

    def("preview_mvt_merc", &preview_mvt_merc_custom,
        (arg("tile"),
         arg("map"),
         arg("image")),
        "Render all geometries of a MVT with custom style");

    def("preview_mvt_merc", &preview_mvt_merc,
        (arg("tile"),
         arg("image")),
        "Render all geometries of a MVT");
}

