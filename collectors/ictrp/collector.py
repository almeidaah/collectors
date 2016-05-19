# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
from scrapy.crawler import CrawlerProcess
from .spider import Spider


def collect(conf, conn):
    process = CrawlerProcess(conf)
    process.crawl(Spider, conn=conn,
        http_user=os.environ['ICTRP_USER'],
        http_pass=os.environ['ICTRP_PASS'])
    process.start()
