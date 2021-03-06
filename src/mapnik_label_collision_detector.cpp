/*****************************************************************************
 *
 * This file is part of Mapnik (c++ mapping toolkit)
 *
 * Copyright (C) 2015 Artem Pavlenko
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
#include "boost_std_shared_shim.hpp"

#pragma GCC diagnostic push
#include <mapnik/warning_ignore.hpp>
#include <boost/python.hpp>
#include <boost/python/module.hpp>
#include <boost/python/def.hpp>
#pragma GCC diagnostic pop

#include <mapnik/collision_cache.hpp>
#include <mapnik/map.hpp>
#include <mapnik/value_error.hpp>

#include <list>

using collision_detector = mapnik::keyed_collision_cache<
    mapnik::label_collision_detector_boost>;
using mapnik::box2d;
using mapnik::Map;

namespace
{

std::shared_ptr<collision_detector>
create_label_collision_detector_from_extent(box2d<double> const &extent)
{
    return std::make_shared<collision_detector>(extent);
}

std::shared_ptr<collision_detector>
create_label_collision_detector_from_map(Map const &m)
{
    double buffer = m.buffer_size();
    box2d<double> extent(-buffer, -buffer, m.width() + buffer, m.height() + buffer);
    return std::make_shared<collision_detector>(extent);
}

boost::python::list
make_label_boxes(std::shared_ptr<collision_detector> cache)
{
    boost::python::list boxes;
    std::vector<std::string> keys(cache->keys());

    for (auto const & key : keys)
    {
        auto & det = cache->detector(key);
        for (auto jtr = det.begin(); jtr != det.end(); ++jtr)
        {
            boxes.append<box2d<double>>(jtr->first);
        }
    }

    return boxes;
}

void insert_box(
    std::shared_ptr<collision_detector> cache,
    box2d<double> const & box,
    boost::python::list const & keys)
{
    boost::python::ssize_t num_keys = boost::python::len(keys);
    std::vector<std::string> keys_vector;

    for (boost::python::ssize_t i = 0; i < num_keys; ++i)
    {
        boost::python::extract<std::string> key(keys[i]);
        if (key.check())
        {
            keys_vector.push_back(key());
        }
        else
        {
            std::stringstream s;
            s << "list of keys must be strings";
            throw mapnik::value_error(s.str());
        }
    }

    cache->insert(box, keys_vector);
}

}

void export_label_collision_detector()
{
    using namespace boost::python;

    class_<collision_detector, std::shared_ptr<collision_detector>, boost::noncopyable>
        ("LabelCollisionDetector",
         "Object to detect collisions between labels, used in the rendering process.",
         no_init)

        .def("__init__", make_constructor(create_label_collision_detector_from_extent),
             "Creates an empty collision detection object with a given extent. Note "
             "that the constructor from Map objects is a sensible default and usually "
             "what you want to do.\n"
             "\n"
             "Example:\n"
             ">>> m = Map(size_x, size_y)\n"
             ">>> buf_sz = m.buffer_size\n"
             ">>> extent = mapnik.Box2d(-buf_sz, -buf_sz, m.width + buf_sz, m.height + buf_sz)\n"
             ">>> detector = mapnik.LabelCollisionDetector(extent)")

        .def("__init__", make_constructor(create_label_collision_detector_from_map),
             "Creates an empty collision detection object matching the given Map object. "
             "The created detector will have the same size, including the buffer, as the "
             "map object. This is usually what you want to do.\n"
             "\n"
             "Example:\n"
             ">>> m = Map(size_x, size_y)\n"
             ">>> detector = mapnik.LabelCollisionDetector(m)")

        .def("extent", &collision_detector::extent, return_value_policy<copy_const_reference>(),
             "Returns the total extent (bounding box) of all labels inside the detector.\n"
             "\n"
             "Example:\n"
             ">>> detector.extent()\n"
             "Box2d(573.252589209,494.789179821,584.261023823,496.83610261)")

        .def("boxes", &make_label_boxes,
             "Returns a list of all the label boxes inside the detector.")

        .def("insert", &insert_box,
             "Insert a 2d box into collision detectors by given keys. This can be used to ensure that "
             "some space is left clear on the map for later overdrawing, for example by "
             "non-Mapnik processes.\n"
             "\n"
             "Example:\n"
             ">>> m = Map(size_x, size_y)\n"
             ">>> detector = mapnik.LabelCollisionDetector(m)"
             ">>> detector.insert(mapnik.Box2d(196, 254, 291, 389), ['default', 'waterfield'])")
        ;
}
