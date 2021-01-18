#!/usr/bin/env python3

import os
import os.path
import re
import shutil
import subprocess
import sys
import glob
from distutils import sysconfig
from ctypes.util import find_library

from setuptools import Command, Extension, setup

NEEDED_BOOST_LIBS = ['python', 'thread', 'system']

# Utils
def check_output(args, shell=False):
    output = subprocess.check_output(args, shell=shell)
    output = output.decode()
    return output.rstrip('\n')

def boost_suffixes():
    suffixes = []

    # boost-python

    # Debian naming convention for versions installed in parallel
    suffixes.append("-py%d%d" % (sys.version_info.major,
                                 sys.version_info.minor))
    # standard suffix for Python3
    suffixes.append(sys.version_info.major)
    # Gentoo
    suffixes.append("-{}.{}".format(sys.version_info.major, sys.version_info.minor))

    # Other

    suffixes.extend([
        "",  # standard naming
        "-mt"  # former naming schema for multithreading build
    ])

    return suffixes

def find_boost_library(_id):
    for suf in boost_suffixes():
        name = "%s%s" % (_id, suf)
        lib = find_library(name)
        if lib is not None:
            return name

def get_boost_library_names():
    found = []
    missing = []
    for _id in NEEDED_BOOST_LIBS:
        _id = 'boost_' + _id
        name = os.environ.get("%s_LIB" % _id.upper(), find_boost_library(_id))
        if name:
            found.append(name)
        else:
            missing.append(_id)
    if missing:
        msg = ""
        for name in missing:
            msg += ("\nMissing {} boost library, try to add its name with "
                    "{}_LIB environment var.").format(name, name.upper())
        raise EnvironmentError(msg)
    return found


def get_boost_library_static_paths():
    """
    Paths for static linking
    """
    paths = []

    boost_path = os.environ.get("BOOST_LIBS")
    if not boost_path:
        boost_system_path = check_output(['ld -o /dev/null -lboost_system --verbose 2>/dev/null | grep succeeded | grep -o "/[^ ]*"'], shell=True)
        if boost_system_path:
            boost_path = os.path.dirname(boost_system_path)

    if not boost_path:
        raise Exception("Failed to find boost libs")

    for name in NEEDED_BOOST_LIBS:
        for suf in boost_suffixes():
            lib_path = os.path.join(boost_path,
                'libboost_{}{}.a'.format(name, suf))
            if os.path.exists(lib_path):
                paths.append(lib_path)
                break

    return paths


class WhichBoostCommand(Command):
    description = 'Output found boost names. Useful for debug.'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        print("Static Boost libs:")
        print("\n".join(get_boost_library_static_paths()))
        print("Dynamic Boost libs:")
        print("\n".join(get_boost_library_names()))


cflags = sysconfig.get_config_var('CFLAGS')
sysconfig._config_vars['CFLAGS'] = re.sub(
    ' +', ' ', cflags.replace('-g ', '').replace('-Os', '').replace('-arch i386', ''))
opt = sysconfig.get_config_var('OPT')
sysconfig._config_vars['OPT'] = re.sub(
    ' +', ' ', opt.replace('-g ', '').replace('-Os', ''))
ldshared = sysconfig.get_config_var('LDSHARED')
sysconfig._config_vars['LDSHARED'] = re.sub(
    ' +', ' ', ldshared.replace('-g ', '').replace('-Os', '').replace('-arch i386', ''))
ldflags = sysconfig.get_config_var('LDFLAGS')
if ldflags:
    sysconfig._config_vars['LDFLAGS'] = re.sub(
        ' +', ' ', ldflags.replace('-g ', '').replace('-Os', '').replace('-arch i386', ''))
pycflags = sysconfig.get_config_var('PY_CFLAGS')
sysconfig._config_vars['PY_CFLAGS'] = re.sub(
    ' +', ' ', pycflags.replace('-g ', '').replace('-Os', '').replace('-arch i386', ''))
sysconfig._config_vars['CFLAGSFORSHARED'] = ''
os.environ['ARCHFLAGS'] = ''

if os.environ.get("MASON_BUILD", "false") == "true":
    # run bootstrap.sh to get mason builds
    subprocess.call(['./bootstrap.sh'])
    mapnik_config = 'mason_packages/.link/bin/mapnik-config'
    mason_build = True
else:
    mapnik_config = 'mapnik-config'
    mason_build = False


linkflags = []
lib_path = os.path.join(check_output([mapnik_config, '--prefix']),'lib')
linkflags.extend(check_output([mapnik_config, '--libs']).split(' '))
linkflags.extend(check_output([mapnik_config, '--ldflags']).split(' '))
linkflags.extend([ '-lmapnik-wkt', '-lmapnik-json'])
linkflags.append('-lprotobuf-lite')
linkflags.append('-lpq')

# Dynamically make the mapnik/paths.py file if it doesn't exist.
if os.path.isfile('mapnik/paths.py'):
    create_paths = False
else:
    create_paths = True
    f_paths = open('mapnik/paths.py', 'w')
    f_paths.write('import os\n')
    f_paths.write('\n')

input_plugin_path = check_output([mapnik_config, '--input-plugins'])
font_path = check_output([mapnik_config, '--fonts'])

if mason_build:
    try:
        if sys.platform == 'darwin':
            base_f = 'libmapnik.dylib'
        else:
            base_f = 'libmapnik.so.3.0'
        f = os.path.join(lib_path, base_f)
        if not os.path.exists(os.path.join('mapnik', 'lib')):
            os.makedirs(os.path.join('mapnik', 'lib'))
        shutil.copyfile(f, os.path.join('mapnik', 'lib', base_f))
    except shutil.Error:
        pass
    input_plugin_files = os.listdir(input_plugin_path)
    input_plugin_files = [os.path.join(
        input_plugin_path, f) for f in input_plugin_files]
    if not os.path.exists(os.path.join('mapnik', 'plugins', 'input')):
        os.makedirs(os.path.join('mapnik', 'plugins', 'input'))
    for f in input_plugin_files:
        try:
            shutil.copyfile(f, os.path.join(
                'mapnik', 'plugins', 'input', os.path.basename(f)))
        except shutil.Error:
            pass
    font_files = os.listdir(font_path)
    font_files = [os.path.join(font_path, f) for f in font_files]
    if not os.path.exists(os.path.join('mapnik', 'plugins', 'fonts')):
        os.makedirs(os.path.join('mapnik', 'plugins', 'fonts'))
    for f in font_files:
        try:
            shutil.copyfile(f, os.path.join(
                'mapnik', 'plugins', 'fonts', os.path.basename(f)))
        except shutil.Error:
            pass
    if create_paths:
        f_paths.write(
            'mapniklibpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "plugins")\n')
        f_paths.write("inputpluginspath = os.path.join(mapniklibpath,'input')\n")
        f_paths.write("fontscollectionpath = os.path.join(mapniklibpath,'fonts')\n")
elif create_paths:
    if os.environ.get('LIB_DIR_NAME'):
        mapnik_lib_path = lib_path + os.environ.get('LIB_DIR_NAME')
    else:
        mapnik_lib_path = lib_path + "/mapnik"
    f_paths.write("mapniklibpath = '{path}'\n".format(path=mapnik_lib_path))
    f_paths.write('mapniklibpath = os.path.normpath(mapniklibpath)\n')
    f_paths.write(
        "inputpluginspath = '{path}'\n".format(path=input_plugin_path))
    f_paths.write(
        "fontscollectionpath = '{path}'\n".format(path=font_path))

if create_paths:
    f_paths.write(
        "__all__ = [mapniklibpath,inputpluginspath,fontscollectionpath]\n")
    f_paths.close()


if mason_build:

    share_dir = 'share'

    for dep in ['icu','gdal','proj']:
        share_path = os.path.join('mapnik', share_dir, dep)
        if not os.path.exists(share_path):
            os.makedirs(share_path)

    icu_path = 'mason_packages/.link/share/icu/*/*.dat'
    icu_files = glob.glob(icu_path)
    if len(icu_files) != 1:
        raise Exception("Failed to find icu dat file at "+ icu_path)
    for f in icu_files:
        shutil.copyfile(f, os.path.join(
            'mapnik', share_dir, 'icu', os.path.basename(f)))

    gdal_path = 'mason_packages/.link/share/gdal/'
    gdal_files = os.listdir(gdal_path)
    gdal_files = [os.path.join(gdal_path, f) for f in gdal_files]
    for f in gdal_files:
        try:
            shutil.copyfile(f, os.path.join(
                'mapnik', share_dir, 'gdal', os.path.basename(f)))
        except shutil.Error:
            pass

    proj_path = 'mason_packages/.link/share/proj/'
    proj_files = os.listdir(proj_path)
    proj_files = [os.path.join(proj_path, f) for f in proj_files]
    for f in proj_files:
        try:
            shutil.copyfile(f, os.path.join(
                'mapnik', share_dir, 'proj', os.path.basename(f)))
        except shutil.Error:
            pass

extra_comp_args = check_output([mapnik_config, '--cflags']).split(' ')
extra_comp_args.append('-I/usr/src/mapbox/mapnik-vector-tile')

if os.environ.get("PYCAIRO", "true") == "true":
    try:
        extra_comp_args.append('-DHAVE_PYCAIRO')
        print("-I%s/include/pycairo".format(sys.exec_prefix))
        extra_comp_args.append("-I{0}/include/pycairo".format(sys.exec_prefix))
        #extra_comp_args.extend(check_output(["pkg-config", '--cflags', 'pycairo']).strip().split(' '))
        #linkflags.extend(check_output(["pkg-config", '--libs', 'pycairo']).strip().split(' '))
    except:
        raise Exception("Failed to find compiler options for pycairo")

if sys.platform == 'darwin':
    extra_comp_args.append('-mmacosx-version-min=10.11')
    # silence warning coming from boost python macros which
    # would is hard to silence via pragma
    extra_comp_args.append('-Wno-parentheses-equality')
    linkflags.append('-mmacosx-version-min=10.11')
else:
    linkflags.append('-lrt')
    linkflags.append('-Wl,-z,origin')
    linkflags.append('-Wl,-rpath=$ORIGIN/lib')

static_boost = bool(os.environ.get("STATIC_BOOST", False))

if not static_boost:
    linkflags.extend(['-l%s' % i for i in get_boost_library_names()])

if os.environ.get("CC", False) == False:
    os.environ["CC"] = check_output([mapnik_config, '--cxx'])
if os.environ.get("CXX", False) == False:
    os.environ["CXX"] = check_output([mapnik_config, '--cxx'])

# monkey-patch for parallel compilation
def parallelCCompile(self, sources, output_dir=None, macros=None, include_dirs=None, debug=0, extra_preargs=None, extra_postargs=None, depends=None):
    # those lines are copied from distutils.ccompiler.CCompiler directly
    macros, objects, extra_postargs, pp_opts, build = self._setup_compile(output_dir, macros, include_dirs, sources, depends, extra_postargs)
    cc_args = self._get_cc_args(pp_opts, debug, extra_preargs)
    # parallel code
    N=int(os.environ.get("JOBS", 2)) # number of parallel compilations
    import multiprocessing.pool
    def _single_compile(obj):
        try: src, ext = build[obj]
        except KeyError: return
        self._compile(obj, src, ext, cc_args, extra_postargs, pp_opts)
    # convert to list, imap is evaluated on-demand
    list(multiprocessing.pool.ThreadPool(N).imap(_single_compile,objects))
    return objects

if int(os.environ.get("JOBS", 1)) > 1:
    import distutils.ccompiler
    distutils.ccompiler.CCompiler.compile=parallelCCompile

setup(
    name="mapnik",
    version="0.1",
    packages=['mapnik'],
    author="Blake Thompson",
    author_email="flippmoke@gmail.com",
    description="Python bindings for Mapnik",
    license="GNU LESSER GENERAL PUBLIC LICENSE",
    keywords="mapnik mapbox mapping cartography",
    url="http://mapnik.org/",
    tests_require=[
        'nose',
    ],
    package_data={
        'mapnik': ['lib/*', 'plugins/*/*', 'share/*/*'],
    },
    test_suite='nose.collector',
    cmdclass={
        'whichboost': WhichBoostCommand,
    },
    ext_modules=[
        Extension('mapnik._mapnik', [
            'src/mapnik_color.cpp',
            'src/mapnik_coord.cpp',
            'src/mapnik_datasource.cpp',
            'src/mapnik_datasource_cache.cpp',
            'src/mapnik_envelope.cpp',
            'src/mapnik_expression.cpp',
            'src/mapnik_feature.cpp',
            'src/mapnik_featureset.cpp',
            'src/mapnik_font_engine.cpp',
            'src/mapnik_fontset.cpp',
            'src/mapnik_gamma_method.cpp',
            'src/mapnik_geometry.cpp',
            'src/mapnik_image.cpp',
            'src/mapnik_image_view.cpp',
            'src/mapnik_label_collision_detector.cpp',
            'src/mapnik_layer.cpp',
            'src/mapnik_logger.cpp',
            'src/mapnik_map.cpp',
            'src/mapnik_palette.cpp',
            'src/mapnik_parameters.cpp',
            'src/mapnik_proj_transform.cpp',
            'src/mapnik_projection.cpp',
            'src/mapnik_python.cpp',
            'src/mapnik_query.cpp',
            'src/mapnik_raster_colorizer.cpp',
            'src/mapnik_rule.cpp',
            'src/mapnik_scaling_method.cpp',
            'src/mapnik_style.cpp',
            'src/mapnik_svg_generator_grammar.cpp',
            'src/mapnik_symbolizer.cpp',
            'src/mapnik_text_placement.cpp',
            'src/mapnik_view_transform.cpp',
            'src/mapnik_connection_manager.cpp',
            'src/mapnik_vector_tile.cpp',
            'src/mapnik_vector_tile_render.cpp',
            'src/mapnik_vector_tile_preview.cpp',
            'src/mapnik_vector_tile_info.cpp',
            '/usr/src/mapbox/mapnik-vector-tile/vector_tile.pb.cc',
            'src/parallel_encoding.cpp',
        ],
            language='c++',
            extra_compile_args=extra_comp_args,
            extra_link_args=linkflags,
            extra_objects=(get_boost_library_static_paths() if static_boost else [])
        )
    ]
)
