import os

from nose.tools import eq_

import mapnik

from .utilities import execution_path, run_all


def setup():
    # All of the paths used are relative, if we run the tests
    # from another directory we need to chdir()
    os.chdir(execution_path('.'))


def test_introspect_symbolizers():
    # create a symbolizer
    p = mapnik.PointSymbolizer()
    p.file = "../data/images/dummy.png"
    p.allow_overlap = True
    p.opacity = 0.5

    # make sure the defaults
    # are what we think they are
    eq_(p.allow_overlap, True)
    eq_(p.opacity, 0.5)
    eq_(p.filename, '../data/images/dummy.png')

    # contruct objects to hold it
    r = mapnik.Rule()
    r.symbols.append(p)
    s = mapnik.Style()
    s.rules.append(r)
    m = mapnik.Map(0, 0)
    m.append_style('s', s)

    # try to figure out what is
    # in the map and make sure
    # style is there and the same

    s2 = m.find_style('s')
    rules = s2.rules
    eq_(len(rules), 1)
    r2 = rules[0]
    syms = r2.symbols
    eq_(len(syms), 1)

    # TODO here, we can do...
    sym = syms[0]
    p2 = sym.extract()
    assert isinstance(p2, mapnik.PointSymbolizer)

    eq_(p2.allow_overlap, True)
    eq_(p2.opacity, 0.5)
    eq_(p2.filename, '../data/images/dummy.png')

    # Make sure that extract() does not copy
    # the symbolizer object

    # Take new reference
    p3 = sym.extract()

    # Modify the object through the old reference
    p2.allow_overlap = False
    p2.opacity = 1.0
    p2.file = '../data/images/xxx.png'

    eq_(p2.allow_overlap, p3.allow_overlap)
    eq_(p2.opacity, p3.opacity)
    eq_(p2.file, p3.file)


def test_mutability_of_styles_by_find_style():
    """
    Should be able to mutate style by a reference
    returned from find_style()
    """
    p = mapnik.PointSymbolizer()
    p.allow_overlap = True
    p.opacity = 0.5

    r = mapnik.Rule()
    r.symbols.append(p)
    s = mapnik.Style()
    s.rules.append(r)
    m = mapnik.Map(256, 256)
    m.append_style('s', s)

    s2 = m.find_style('s')
    eq_(len(s2.rules), 1)

    s3 = m.find_style('s')
    s3.rules.append(mapnik.Rule())

    # Both referefences should point to the same object
    eq_(len(s3.rules), 2)
    eq_(len(s2.rules), 2)


def test_mutability_of_styles_from_iterator():
    """
    Should be able to mutate style by a reference
    returned from the iterator
    """
    p = mapnik.PointSymbolizer()
    p.allow_overlap = True
    p.opacity = 0.5

    r = mapnik.Rule()
    r.symbols.append(p)
    s = mapnik.Style()
    s.rules.append(r)
    m = mapnik.Map(256, 256)
    m.append_style('s', s)

    for style_name, style in m.styles:
        eq_(style_name, 's')
        eq_(len(style.rules), 1)
        style.rules.append(mapnik.Rule())
        eq_(len(style.rules), 2)

    for style_name, style in m.styles:
        eq_(style_name, 's')
        eq_(len(style.rules), 2)


if __name__ == "__main__":
    setup()
    exit(run_all(eval(x) for x in dir() if x.startswith("test_")))
