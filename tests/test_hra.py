# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import pytz
import pytest
import dataset
import datetime
from importlib import import_module
from collectors.hra.collector import collect, _make_request_url


# Tests

def test_collect(conf, conn):
    if conf['HRA_ENV'] == 'staging':
        with pytest.raises(SystemExit):
            collect(conf, conn, '2015-01-01', '2015-01-01')
        assert conn['warehouse']['hra'].count() > 10


def test_make_request_url():
    date_from = datetime.date(2015, 01, 01)
    date_to = datetime.date(2015, 12, 31)
    actual = _make_request_url('prefix', date_from, date_to)
    expect = 'prefix?datePublishedFrom=2015-01-01&datePublishedTo=2015-12-31'
    assert actual == expect
