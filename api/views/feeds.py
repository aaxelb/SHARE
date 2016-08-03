from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed
from django.conf import settings

import bleach
import dateparser
import json
import re
import requests
import urllib

from share.models.creative import AbstractCreativeWork

RESULTS_PER_PAGE = 250

RE_XML_ILLEGAL = u'([\u0000-\u0008\u000b-\u000c\u000e-\u001f\ufffe-\uffff])' + \
                 u'|' + \
                 u'([%s-%s][^%s-%s])|([^%s-%s][%s-%s])|([%s-%s]$)|(^[%s-%s])' % \
                 (chr(0xd800), chr(0xdbff), chr(0xdc00), chr(0xdfff),
                 chr(0xd800), chr(0xdbff), chr(0xdc00), chr(0xdfff),
                 chr(0xd800), chr(0xdbff), chr(0xdc00), chr(0xdfff))

RE_XML_ILLEGAL_COMPILED = re.compile(RE_XML_ILLEGAL)

def sanitize_for_xml(s):
    if s:
        s = RE_XML_ILLEGAL_COMPILED.sub('', s)
        return bleach.clean(s, strip=True, tags=[], attributes=[], styles=[])
    return s

class ShareAtomFeed(Atom1Feed):
    def add_root_elements(self, handler):
        super(ShareAtomFeed, self).add_root_elements(handler)
        for link in self.feed['links']:
            handler.addQuickElement('link', '', link)

class CreativeWorksAtom(Feed):
    feed_type = ShareAtomFeed
    subtitle = 'Updates to the SHARE open dataset'
    author_name = 'COS'
    link = '/'

    def title(self, obj):
        query = json.dumps(obj.get('query', 'All'))
        return sanitize_for_xml('SHARE: Atom feed for query: {}'.format(query))

    def get_object(self, request):
        elastic_query = request.GET.get('elasticQuery')
        page = int(request.GET.get('page', 1))

        elastic_data = {
            'sort': { 'date_modified': 'desc' },
            'from': (page - 1) * RESULTS_PER_PAGE,
            'size': RESULTS_PER_PAGE
        }
        if elastic_query:
            elastic_data['query'] = json.loads(elastic_query)

        return {
            'elastic_data': elastic_data,
            'page': page,
            'self_url': request.build_absolute_uri()
        }

    def feed_extra_kwargs(self, obj):
        page = obj['page']
        url = obj['self_url']
        separator = '&' if '?' in url else '?'
        links = [
            {'href': '{}{}page={}'.format(url, separator, page + 1), 'rel': 'next'},
        ]
        if page > 1:
            links.extend([
                {'href': '{}{}page={}'.format(url, separator, page - 1), 'rel': 'previous'},
                {'href': '{}{}page=1'.format(url, separator), 'rel': 'first'}
            ])
        return { 'links': links }

    def items(self, obj):
        elastic_data = json.dumps(obj['elastic_data'])
        headers = {'Content-Type': 'application/json'}
        elastic_url = '{}{}/abstractcreativework/_search'.format(settings.ELASTICSEARCH_URL, settings.ELASTICSEARCH_INDEX)

        elastic_response = requests.post(elastic_url, data=elastic_data, headers=headers)
        json_response = elastic_response.json()

        if elastic_response.status_code != 200 or 'error' in json_response:
            return

        def get_item(hit):
            source = hit.get('_source')
            source['@id'] = hit.get('_id')
            return source

        return [get_item(hit) for hit in json_response['hits']['hits']]

    def item_title(self, item):
        return sanitize_for_xml(item.get('title', 'No title provided.'))

    def item_description(self, item):
        return sanitize_for_xml(item.get('description', 'No description provided.'))

    def item_link(self, item):
        # Link to SHARE curate page
        return '{}{}/curate/{}/{}'.format(settings.SHARE_API_URL, settings.EMBER_SHARE_PREFIX, item.get('@type'), item.get('@id'))

    def item_pubdate(self, item):
        pubdate = item.get('date')
        return dateparser.parse(pubdate) if pubdate else None

    def item_updateddate(self, item):
        updateddate = item.get('date_updated')
        return dateparser.parse(updateddate) if updateddate else None

    def item_categories(self, item):
        categories = [item.get('subject')]
        categories.extend(item.get('tags'))
        return [sanitize_for_xml(c) for c in categories if c]
