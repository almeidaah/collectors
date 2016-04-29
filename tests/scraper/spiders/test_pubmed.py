# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from importlib import import_module

from scraper.spiders.pubmed.utils import make_start_urls


def test_make_start_urls():
    result = make_start_urls(
        'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi/',
        'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi/?db=pubmed&id={pmid}&retmode=xml',
        '2016-01-01', '2016-01-01')
    print(result)
    assert result
