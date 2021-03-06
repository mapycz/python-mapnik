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
#include "boost_std_shared_shim.hpp"

#pragma GCC diagnostic push
#include <mapnik/warning_ignore.hpp>
#include <boost/python.hpp>
#include <boost/noncopyable.hpp>
#include <boost/python/iterator.hpp>
#include <boost/python/call_method.hpp>
#include <boost/python/tuple.hpp>
#include <boost/python/to_python_converter.hpp>
#pragma GCC diagnostic pop

// mapnik
#include <mapnik/value_types.hpp>
#include <mapnik/feature.hpp>
#include <mapnik/feature_factory.hpp>
#include <mapnik/feature_kv_iterator.hpp>
#include <mapnik/datasource.hpp>
#include <mapnik/wkb.hpp>
//#include <mapnik/wkt/wkt_factory.hpp>
#include <mapnik/json/feature_parser.hpp>
#include <mapnik/json/feature_generator.hpp>

// stl
#include <stdexcept>

namespace {

using mapnik::geometry_utils;
using mapnik::context_type;
using mapnik::context_ptr;
using mapnik::feature_kv_iterator;

mapnik::feature_ptr from_geojson_impl(std::string const& json, mapnik::context_ptr const& ctx)
{
    mapnik::feature_ptr feature(mapnik::feature_factory::create(ctx,1));
    if (!mapnik::json::from_geojson(json,*feature))
    {
        throw std::runtime_error("Failed to parse geojson feature");
    }
    return feature;
}

std::string feature_to_geojson(mapnik::feature_impl const& feature)
{
    std::string json;
    if (!mapnik::json::to_geojson(json,feature))
    {
        throw std::runtime_error("Failed to generate GeoJSON");
    }
    return json;
}

mapnik::value  __getitem__(mapnik::feature_impl const& feature, std::string const& name)
{
    return feature.get(name);
}

mapnik::value  __getitem2__(mapnik::feature_impl const& feature, std::size_t index)
{
    return feature.get(index);
}

void __setitem__(mapnik::feature_impl & feature, std::string const& name, mapnik::value const& val)
{
    feature.put_new(name,val);
}

boost::python::dict attributes(mapnik::feature_impl const& f)
{
    boost::python::dict attributes;
    feature_kv_iterator itr = f.begin();
    feature_kv_iterator end = f.end();

    for ( ;itr!=end; ++itr)
    {
        attributes[std::get<0>(*itr)] = std::get<1>(*itr);
    }

    return attributes;
}

} // end anonymous namespace

struct unicode_string_from_python_str
{
    unicode_string_from_python_str()
    {
        boost::python::converter::registry::push_back(
            &convertible,
            &construct,
            boost::python::type_id<mapnik::value_unicode_string>());
    }

    static void* convertible(PyObject* obj_ptr)
    {
        if (!(PyBytes_Check(obj_ptr) || PyUnicode_Check(obj_ptr)))
            return 0;
        return obj_ptr;
    }

    static void construct(
        PyObject* obj_ptr,
        boost::python::converter::rvalue_from_python_stage1_data* data)
    {
        char * value=0;
        if (PyUnicode_Check(obj_ptr)) {
            PyObject *encoded = PyUnicode_AsEncodedString(obj_ptr, "utf8", "replace");
            if (encoded) {
                value = PyBytes_AsString(encoded);
                Py_DecRef(encoded);
            }
        } else {
            value = PyBytes_AsString(obj_ptr);
        }
        if (value == 0) boost::python::throw_error_already_set();
        void* storage = (
            (boost::python::converter::rvalue_from_python_storage<mapnik::value_unicode_string>*)
            data)->storage.bytes;
        new (storage) mapnik::value_unicode_string(value);
        data->convertible = storage;
    }
};


struct value_null_from_python
{
    value_null_from_python()
    {
        boost::python::converter::registry::push_back(
            &convertible,
            &construct,
            boost::python::type_id<mapnik::value_null>());
    }

    static void* convertible(PyObject* obj_ptr)
    {
        if (obj_ptr == Py_None) return obj_ptr;
        return 0;
    }

    static void construct(
        PyObject* obj_ptr,
        boost::python::converter::rvalue_from_python_stage1_data* data)
    {
        if (obj_ptr != Py_None) boost::python::throw_error_already_set();
        void* storage = (
            (boost::python::converter::rvalue_from_python_storage<mapnik::value_null>*)
            data)->storage.bytes;
        new (storage) mapnik::value_null();
        data->convertible = storage;
    }
};

void export_feature()
{
    using namespace boost::python;

    // Python to mapnik::value converters
    // NOTE: order matters here. For example value_null must be listed before
    // bool otherwise Py_None will be interpreted as bool (false)
    implicitly_convertible<mapnik::value_unicode_string,mapnik::value>();
    implicitly_convertible<mapnik::value_null,mapnik::value>();
    implicitly_convertible<mapnik::value_integer,mapnik::value>();
    implicitly_convertible<mapnik::value_double,mapnik::value>();
    implicitly_convertible<mapnik::value_bool,mapnik::value>();

    // http://misspent.wordpress.com/2009/09/27/how-to-write-boost-python-converters/
    unicode_string_from_python_str();
    value_null_from_python();

    class_<context_type,context_ptr,boost::noncopyable>
        ("Context",init<>("Default ctor."))
        .def("push", &context_type::push)
        ;

    class_<mapnik::feature_impl,std::shared_ptr<mapnik::feature_impl>,
        boost::noncopyable>("Feature",init<context_ptr,mapnik::value_integer>("Default ctor."))
        .def("id",&mapnik::feature_impl::id)
        .add_property("geometry",
                      make_function(&mapnik::feature_impl::get_geometry,return_value_policy<reference_existing_object>()),
                      &mapnik::feature_impl::set_geometry_copy)
        .def("envelope", &mapnik::feature_impl::envelope)
        .def("has_key", &mapnik::feature_impl::has_key)
        .add_property("attributes",&attributes)
        .def("__setitem__",&__setitem__)
        .def("__contains__",&__getitem__)
        .def("__getitem__",&__getitem__)
        .def("__getitem__",&__getitem2__)
        .def("__len__", &mapnik::feature_impl::size)
        .def("context",&mapnik::feature_impl::context)
        .def("to_geojson",&feature_to_geojson)
        .def("from_geojson",from_geojson_impl)
        .staticmethod("from_geojson")
        ;
}
