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

#pragma GCC diagnostic push
#include <mapnik/warning_ignore.hpp>
#include <boost/python.hpp>
#include <boost/python/module.hpp>
#include <boost/python/def.hpp>
#include <boost/python/stl_iterator.hpp>
#pragma GCC diagnostic pop

// mapnik
#include <mapnik/image_util.hpp>
#include <mapnik/util/parallelize.hpp>

struct encoding_chunk
{
    const boost::python::object & key;
    mapnik::image_any const & img;
};

unsigned jobs_by_chunks(unsigned chunks, unsigned max_concurrency=0)
{
    unsigned max_jobs = max_concurrency ? max_concurrency :
        std::max(1u, std::thread::hardware_concurrency() / 2);
    return std::max(1u, std::min(chunks, max_jobs));
}

struct encoding_func
{
};

void encode_parallel(boost::python::dict & tiles)
{
    using namespace boost::python;

    std::vector<encoding_chunk> chunks;

    auto tiles_iterator = tiles.iteritems();
    stl_input_iterator<tuple> it(tiles_iterator), end;

    for (; it != end; ++it)
    {
        extract<mapnik::image_any const &> img((*it)[1]);
        //mapnik::image_any const & img = extract<mapnik::image_any const &>((*it)[1]);
        if (img.check())
        {
            chunks.emplace_back(encoding_chunk{ (*it)[0], img() });
        }
    }

    unsigned jobs = jobs_by_chunks(chunks.size());

    util::parallelize(comp_func, jobs, src.height());
    /*
    for (auto & tile_kv : tiles.iteritems())
    {
        chunks.emplace_back({ tile_kv->
    }
    */
}

void export_encode_parallel()
{
    using namespace boost::python;
}
