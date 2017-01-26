# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import mock
import random
import urlparse
import pytest
from scrapy.http import Request, HtmlResponse
from collectors.fda_dap.spider import Spider


@pytest.mark.skip(reason='the site was redesigned')
class TestFDADAP(object):
    def test_make_requests_from_url(self):
        url = 'http://www.accessdata.fda.gov/somewhere.cfm'
        spider = Spider()
        request = spider.make_requests_from_url(url)

        assert request.url == url
        assert request.callback == spider.parse_search_results

    def test_parse_search_results(self, get_url):
        url = 'http://www.accessdata.fda.gov/scripts/cder/drugsatfda/index.cfm?fuseaction=Search.SearchResults_Browse&DrugInitial=A'
        random_seed = '123'

        response = get_url(url)
        response.headers['Set-Cookie'] = 'foo=bar;'
        spider = Spider()
        random.seed(random_seed)
        requests = [request
                    for request in spider.parse_search_results(response)]

        assert len(requests) == 100

        random.seed(random_seed)
        expected_cookiejars = [random.random() for _ in range(len(requests))]
        cookiejars = [request.meta['cookiejar'] for request in requests]
        assert cookiejars == expected_cookiejars

        for request in requests:
            assert request.dont_filter
            assert request.callback == spider.parse_drug_details_or_overview
            assert request.meta.get('original_url') == request.url
            original_cookies = [(cookie['name'], cookie['value'])
                                for cookie in request.meta.get('original_cookies')]
            assert original_cookies == [('foo', 'bar')]

    def test_parse_drug_details_or_overview_delegates_to_parse_drug_details_when_response_in_drug_details(self):
        url = 'http://www.accessdata.fda.gov/scripts/cder/drugsatfda/index.cfm?fuseaction=Search.DrugDetails'
        mock_response = HtmlResponse(url=url)
        expected_result = 'expected_result'

        with mock.patch.object(Spider,
                               'parse_drug_details',
                               return_value=expected_result) as mock_method:
            spider = Spider()
            result = spider.parse_drug_details_or_overview(mock_response)

        mock_method.assert_called_once_with(mock_response)
        assert result == expected_result

    def test_parse_drug_details_or_overview_delegates_to_parse_drug_details_when_response_in_drug_overview(self):
        url = 'http://www.accessdata.fda.gov/scripts/cder/drugsatfda/index.cfm?fuseaction=Search.Overview&DrugName=E-BASE'
        mock_response = HtmlResponse(url=url)
        expected_result = 'expected_result'

        with mock.patch.object(Spider,
                               'parse_drug_overview',
                               return_value=expected_result) as mock_method:
            spider = Spider()
            result = spider.parse_drug_details_or_overview(mock_response)

        mock_method.assert_called_once_with(mock_response)
        assert result == expected_result

    def test_parse_drug_details_or_overview_generates_new_request_if_redirected_to_search_page(self):
        url = 'http://www.accessdata.fda.gov/scripts/cder/drugsatfda/index.cfm?fuseaction=Search.Search_Drug_Name'
        meta = {
            'original_url': 'http://www.accessdata.fda.gov/somewhere.cfm',
            'original_cookies': {
                'foo': 'bar',
            },
        }
        mock_response = HtmlResponse(url=url)
        mock_response.request = Request(url, meta=meta)

        with mock.patch('random.random', return_value='random_cookiejar'):
            spider = Spider()
            request = spider.parse_drug_details_or_overview(mock_response)

        assert request.url == meta['original_url']
        assert request.cookies == meta['original_cookies']
        assert request.dont_filter
        assert request.callback == spider.parse_drug_details_or_overview
        assert request.meta['cookiejar'] == 'random_cookiejar'

    def test_parse_drug_details_or_overview_raises_exception_for_unknown_pages(self):
        url = 'http://www.accessdata.fda.gov/'
        mock_response = HtmlResponse(url=url)

        with pytest.raises(Exception):
            spider = Spider()
            spider.parse_drug_details_or_overview(mock_response)

    def test_parse_drug_details(self, get_url):
        url = 'http://www.accessdata.fda.gov/scripts/cder/drugsatfda/index.cfm?fuseaction=Search.Overview&DrugName=EFFEXOR%20XR'

        response = get_url(url, request_kwargs={'meta': {'cookiejar': 123}})
        spider = Spider()
        result = spider.parse_drug_details(response)

        assert 'Search.Label_ApprovalHistory' in result.url
        assert result.dont_filter
        assert result.meta.get('cookiejar') == 123
        assert result.callback == spider.parse_approval_history

    def test_parse_drug_overview(self, get_url):
        random_seed = '123'
        search_url = 'http://www.accessdata.fda.gov/scripts/cder/drugsatfda/index.cfm?fuseaction=Search.SearchResults_Browse&DrugInitial=E'
        url = 'http://www.accessdata.fda.gov/scripts/cder/drugsatfda/index.cfm?fuseaction=Search.Overview&DrugName=E%2DBASE'

        get_url(search_url)  # Needed to set up the session
        response = get_url(url)

        random.seed(random_seed)
        spider = Spider()
        requests = [request
                    for request in spider.parse_drug_overview(response)]

        requests_urls = [urlparse.urlparse(request.url)
                         for request in requests]
        application_nums = [urlparse.parse_qs(request_url.query)['ApplNo'][0]
                            for request_url in requests_urls]

        assert len(requests) == 3
        assert application_nums == ['062999', '063028', '063086']

        random.seed(random_seed)
        expected_cookiejars = [random.random() for _ in range(len(requests))]
        cookiejars = [request.meta['cookiejar'] for request in requests]
        assert cookiejars == expected_cookiejars

        for request in requests:
            assert request.dont_filter
            assert request.callback == spider.parse_drug_details_or_overview

    def test_parse_drug_overview_only_follow_links_to_drug_details_page(self, get_url):
        '''There might be tables with links in multiple columns. We're only
        interested in links on the first column (Drug Name).
        '''
        search_url = 'http://www.accessdata.fda.gov/scripts/cder/drugsatfda/index.cfm?fuseaction=Search.SearchResults_Browse&DrugInitial=F'
        url = 'http://www.accessdata.fda.gov/scripts/cder/drugsatfda/index.cfm?fuseaction=Search.Overview&DrugName=FYCOMPA'

        get_url(search_url)  # Needed to set up the session
        response = get_url(url)

        requests = [request for request in Spider().parse_drug_overview(response)]

        assert len(requests) == 2
        for request in requests:
            assert 'goto=Search.Label_ApprovalHistory' not in request.url

    def test_parse_approval_history(self, get_url):
        search_overview_url = 'http://www.accessdata.fda.gov/scripts/cder/drugsatfda/index.cfm?fuseaction=Search.Overview&DrugName=EFFEXOR%20XR'
        url = 'http://www.accessdata.fda.gov/scripts/cder/drugsatfda/index.cfm?fuseaction=Search.Label_ApprovalHistory#apphist'

        get_url(search_overview_url)
        response = get_url(url)

        spider = Spider()
        items = [item
                 for item in spider.parse_approval_history(response)]

        expected_item = {
            'id': 'NDA020699-001',
            'drug_name': 'EFFEXOR XR',
            'active_ingredients': 'VENLAFAXINE HYDROCHLORIDE',
            'company': 'WYETH PHARMS INC',
            'fda_application_num': 'NDA020699',
            'action_date': datetime.date(1999, 3, 11),
            'supplement_number': 1,
            'approval_type': 'New or Modified Indication',
            'documents': [
                {
                    'name': 'Label',
                    'urls': [
                        'http://www.accessdata.fda.gov/drugsatfda_docs/label/1999/20699s1lbl.pdf',
                    ],
                },
                {
                    'name': 'Letter',
                    'urls': [
                        'http://www.accessdata.fda.gov/drugsatfda_docs/appletter/1999/20699s1ltr.pdf',
                    ],
                },
            ]
        }
        complete_item = items[-3]
        item_without_meta = dict([(key, value)
                                  for key, value in complete_item.items()
                                  if not key.startswith('meta_')])
        assert item_without_meta == expected_item

        incomplete_item_request = items[-1]
        incomplete_item = incomplete_item_request.meta.get('item')

        assert incomplete_item is not None
        assert incomplete_item['documents'] == []
        assert incomplete_item_request.url == 'http://www.accessdata.fda.gov/drugsatfda_docs/nda/97/020699_effexorxr_toc.cfm'

    def test_parse_dap_page(self, get_url):
        url = 'http://www.accessdata.fda.gov/drugsatfda_docs/nda/97/020699_effexorxr_toc.cfm'
        mock_item = {
            'documents': [
                {'name': 'Foo', 'urls': ['http://foo.com/bar.pdf']},
            ]
        }

        response = get_url(url)
        response.meta['item'] = mock_item

        spider = Spider()
        item = spider.parse_dap_page(response)

        documents = item['documents']
        assert len(documents) == 6
        assert documents[0] == mock_item['documents'][0]

        assert documents[2] == {
            'name': 'Medical Review',
            'urls': [
                'http://www.accessdata.fda.gov/drugsatfda_docs/nda/97/020699ap_effexor_medrp1.pdf',
                'http://www.accessdata.fda.gov/drugsatfda_docs/nda/97/020699ap_effexor_medrp2.pdf',
            ],
        }

    def test_parse_dap_page_with_page_with_paragraphs_inside_lis(self, get_url):
        '''Test that we can extract the document names from DAPs which <li>
        elements contain <p> elements.'''

        url = 'http://www.accessdata.fda.gov/drugsatfda_docs/nda/2003/21-385_Ertaczo.cfm'
        mock_item = {
            'documents': []
        }

        response = get_url(url)
        response.meta['item'] = mock_item

        spider = Spider()
        item = spider.parse_dap_page(response)

        documents = item['documents']
        documents_names = [document['name'] for document in documents]

        assert documents_names == [
            'Approval Letter',
            'Printed Labeling',
            'Medical Review',
            'Chemistry Review',
            'Pharmacology Review',
            'Statistical Review',
            'Microbiology Review',
            'Clinical Pharmacology Biopharmaceutics Review',
            'Administrative Document',
            'Correspondence',
        ]

    def test_parse_dap_page_on_page_with_documents_sizes(self, get_url):
        url = 'http://www.accessdata.fda.gov/drugsatfda_docs/nda/99/020500S005.cfm'
        mock_item = {
            'documents': [],
        }
        response = get_url(url)
        response.meta['item'] = mock_item

        item = Spider().parse_dap_page(response)

        documents = item['documents']
        documents_names = [document['name'] for document in documents]

        assert documents_names == [
            'Approval Letter & Printed Labeling',
            'Medical/Statistical Review',
            'Chemistry Review Microbiology Review Clinical Pharmacology Biopharmaceutics Review',
            'Administrative Document/Correspondence',
        ]

    def test_parse_dap_page_on_page_with_empty_documents_sizes(self, get_url):
        url = 'http://www.accessdata.fda.gov/drugsatfda_docs/nda/98/020634s04.cfm'
        mock_item = {
            'documents': [],
        }
        response = get_url(url)
        response.meta['item'] = mock_item

        item = Spider().parse_dap_page(response)

        documents = item['documents']
        documents_names = [document['name'] for document in documents]

        assert documents_names == [
            'Approval Letter',
            'Printed Labeling',
            'Medical Review',
            'Chemistry Review, Environmental Assessment & Statistical Review',
            'Microbiology Review & Clinical Pharmacology Biopharmaceutics Review',
            'Administrative Document/Correspondence',
        ]

    def test_parse_dap_page_on_page_with_vision_impaired_notices(self, get_url):
        url = 'http://www.accessdata.fda.gov/drugsatfda_docs/nda/2006/021871TOC.cfm'
        mock_item = {
            'documents': [],
        }
        response = get_url(url)
        response.meta['item'] = mock_item

        item = Spider().parse_dap_page(response)

        documents = item['documents']
        documents_names = [document['name'] for document in documents]

        assert documents_names == [
            'Approval Letter',
            'Printed Labeling',
            'Medical Review',
            'Chemistry Review',
            'Pharmacology Review',
            'Statistical Review',
            'Clinical Pharmacology Biopharmaceutics Review',
            'Administrative Document & Correspondence',
        ]

    def test_parse_dap_page_on_page_with_unnamed_multipart_document_only(self, get_url):
        url = 'http://www.accessdata.fda.gov/drugsatfda_docs/nda/2000/019901_s028_Altace.cfm'
        mock_item = {
            'documents': [],
        }
        response = get_url(url)
        response.meta['item'] = mock_item
        response.meta['document_name'] = 'document_name'

        item = Spider().parse_dap_page(response)

        documents = item['documents']

        assert item['documents'] == [
            {
                'name': response.meta['document_name'],
                'urls': [
                    'http://www.accessdata.fda.gov/drugsatfda_docs/nda/2000/019901_S028_Altace_p1.pdf',
                    'http://www.accessdata.fda.gov/drugsatfda_docs/nda/2000/019901_S028_Altace_p2.pdf',
                    'http://www.accessdata.fda.gov/drugsatfda_docs/nda/2000/019901_S028_Altace_p3.pdf',
                    'http://www.accessdata.fda.gov/drugsatfda_docs/nda/2000/019901_S028_Altace_p4.pdf',
                ]
            },
        ]

    def test_parse_dap_page_on_page_multipart_doc_with_suffix_part_number_only(self, get_url):
        url = 'http://www.accessdata.fda.gov/drugsatfda_docs/nda/96/020430_toc.cfm'
        mock_item = {
            'documents': [],
        }
        response = get_url(url)
        response.meta['item'] = mock_item

        item = Spider().parse_dap_page(response)

        documents = item['documents']

        assert item['documents'] == [
            {
                'name': 'Review',
                'urls': [
                    'http://www.accessdata.fda.gov/drugsatfda_docs/nda/96/020430ap-1.pdf',
                    'http://www.accessdata.fda.gov/drugsatfda_docs/nda/96/020430ap-2.pdf',
                ]
            },
        ]

    def test_parse_dap_page_on_page_multipart_doc_with_prefix_part_number_only(self, get_url):
        url = 'http://www.accessdata.fda.gov/drugsatfda_docs/nda/98/20713.cfm'
        mock_item = {
            'documents': [],
        }
        response = get_url(url)
        response.meta['item'] = mock_item

        item = Spider().parse_dap_page(response)

        documents = item['documents']

        assert item['documents'] == [
            {
                'name': 'Drug Review',
                'urls': [
                    'http://www.accessdata.fda.gov/drugsatfda_docs/nda/98/20713-1.pdf',
                    'http://www.accessdata.fda.gov/drugsatfda_docs/nda/98/20713-2.pdf',
                ]
            },
        ]

    def test_parse_dap_page_on_page_with_multipart_doc_among_normal_ones(self, get_url):
        url = 'http://www.accessdata.fda.gov/drugsatfda_docs/nda/2003/103628s5021TOC.cfm'
        mock_item = {
            'documents': [],
        }
        response = get_url(url)
        response.meta['item'] = mock_item

        item = Spider().parse_dap_page(response)

        documents = item['documents']
        documents_names = [document['name'] for document in documents]

        assert documents_names == [
            'Approval Letter',
            'Summary Basis for Approval',
            'Chemistry, Manufacture and Control Review',
            'Printed Labeling',
            'Medication Guide',
            'Clinical Review',
            'Licensing Action',
            'Review of Assay Validation',
            'Immunogenicity Review',
            'Pharmacology Toxicology Review',
            'Toxicologist Review',
        ]
        assert item['documents'][2]['urls'] == [
            'http://www.accessdata.fda.gov/drugsatfda_docs/nda/2003/103268s5021CMCreview1.pdf',
            'http://www.accessdata.fda.gov/drugsatfda_docs/nda/2003/103628s5021CMCreview2.pdf',
        ]

    def test_parse_dap_page_on_page_with_pdf_in_brackets(self, get_url):
        url = 'http://www.accessdata.fda.gov/drugsatfda_docs/nda/pre96/019002-S2_VASCOR%20TABLETS_toc.cfm'
        mock_item = {
            'documents': [],
        }
        response = get_url(url)
        response.meta['item'] = mock_item

        item = Spider().parse_dap_page(response)

        documents = item['documents']
        documents_names = [document['name'] for document in documents]

        assert documents_names == [
            'Approval Letter',
            'Chemistry Review',
        ]
