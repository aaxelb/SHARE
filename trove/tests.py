import json

from django.test import TestCase


SCHEMA_URL = 'https://mordor.osf.io/one-schema.xsd'
SCHEMA_METADATA_HASH = '64cdcaf2954e37aba5952db79c0bfbd8723a9048a913e5db2725f5c6edd4a377'
SCHEMA_METADATA_MEDIATYPE = 'a bedtime story for lil sauron'
SCHEMA_METADATA = b'''
one schema to rule them all
one schema to find them
one schema to bring them all
and in the darkness, bind them.
'''


def assert_mediatypes(response, expected_mediatypes):
    response_json = json.loads(response.content)
    observed_mediatypes = response_json['mediatype-basket']
    assert set(observed_mediatypes) == set(expected_mediatypes)


def assert_raw_expression(response, expected_raw, expected_mediatype):
    observed_mediatype = response.headers['content-type']
    assert observed_mediatype == expected_mediatype

    observed_raw_expression = response.content
    assert observed_raw_expression == expected_raw


def assert_expression_basket(response, expected_hashes):
    response_json = json.loads(response.content)
    observed_hashes = [
        exp['raw-hash']
        for exp in response_json['expression-basket']
    ]
    assert set(observed_hashes) == set(expected_hashes)


def assert_feed(response, expected_hashes):
    response_json = json.loads(response.content)
    observed_hashes = [
        exp['raw-hash']
        for exp in response_json['expression-feed']
    ]
    assert set(observed_hashes) == set(expected_hashes)


class TroveTests(TestCase):
    def test_one_flow(self):
        # start out with nothin
        mediatype_response = self.client.get('/trove/mediatype-basket')
        assert_mediatypes(mediatype_response, expected_mediatypes=[])
        feed_response = self.client.get(f'/trove/expression-feed///{SCHEMA_METADATA_MEDIATYPE}')
        assert_feed(feed_response, expected_hashes=[])

        # put a thing in
        put_response = self.client.put(
            f'/trove/expression-basket///{SCHEMA_URL}',
            content_type=SCHEMA_METADATA_MEDIATYPE,
            data=SCHEMA_METADATA,
        )
        assert put_response.status_code == 201

        # is something there now?
        mediatype_response = self.client.get('/trove/mediatype-basket')
        assert_mediatypes(
            mediatype_response,
            expected_mediatypes=[SCHEMA_METADATA_MEDIATYPE],
        )
        raw_response = self.client.get(f'/trove/raw-expression///{SCHEMA_METADATA_HASH}')
        assert_raw_expression(
            raw_response,
            expected_raw=SCHEMA_METADATA,
            expected_mediatype=SCHEMA_METADATA_MEDIATYPE,
        )
        expression_basket_response = self.client.get(f'/trove/expression-basket///{SCHEMA_URL}')
        assert_expression_basket(
            expression_basket_response,
            expected_hashes=[SCHEMA_METADATA_HASH],
        )
        feed_response = self.client.get(f'/trove/expression-feed///{SCHEMA_METADATA_MEDIATYPE}')
        assert_feed(
            feed_response,
            expected_hashes=[SCHEMA_METADATA_HASH],
        )
