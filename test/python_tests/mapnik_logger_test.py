from nose.tools import eq_

import mapnik

from .utilities import run_all


def test_logger_init():
    eq_(mapnik.severity_type.Debug, 0)
    eq_(mapnik.severity_type.Warn, 1)
    eq_(mapnik.severity_type.Error, 2)
    eq_(getattr(mapnik.severity_type, "None"), 3)
    default = mapnik.logger.get_severity()
    mapnik.logger.set_severity(mapnik.severity_type.Debug)
    eq_(mapnik.logger.get_severity(), mapnik.severity_type.Debug)
    mapnik.logger.set_severity(default)
    eq_(mapnik.logger.get_severity(), default)

if __name__ == "__main__":
    exit(run_all(eval(x) for x in dir() if x.startswith("test_")))
