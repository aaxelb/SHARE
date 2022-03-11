import pytest

from django.test.client import Client


SCHEMA_URL = 'https://mordor.osf.io/one-schema.xsd'
SCHEMA_METADATA_HASH = '64cdcaf2954e37aba5952db79c0bfbd8723a9048a913e5db2725f5c6edd4a377'
SCHEMA_METADATA_MEDIATYPE = 'a bedtime story for lil sauron'
SCHEMA_METADATA = b'''
one schema to rule them all
one schema to find them
one schema to bring them all
and in the darkness, bind them.
'''


def assert_mediatypes(client, expected_mediatypes):
    response = client.get('/trove/mediatype_basket')
    observed_mediatypes = response.json()['data']
    assert set(observed_mediatypes) == set(expected_mediatypes)


def assert_raw_expression(client, hashed_expression, expected_raw_expression):
    response = client.get(f'/trove/raw_expression///{hashed_expression}')
    observed_raw_expression = response.body
    assert observed_raw_expression == expected_raw_expression


def assert_expression_basket(client, url_to_the_thing, expected_hashes):
    response = client.get(f'/trove/expression_basket///{url_to_the_thing}')
    observed_hashes = [
        exp['hashed_expression']
        for exp in response.json()['data']
    ]
    assert set(observed_hashes) == set(expected_hashes)


@pytest.mark.django_db
def test_one_flow(self):
    client = Client()

    # start out with nothin
    assert_mediatypes(client, [])

    # put a thing in
    put_response = client.put(
        f'/trove/expression_basket///{SCHEMA_URL}',
        mediatype=SCHEMA_METADATA_MEDIATYPE,
        data=SCHEMA_METADATA,
    )
    assert put_response.status == 201

    # is the thing there?
    assert_mediatypes(
        client,
        expected_mediatypes=[SCHEMA_METADATA_MEDIATYPE],
    )
    assert_raw_expression(
        client,
        hashed_expression=SCHEMA_METADATA_HASH,
        expected_raw_expression=SCHEMA_METADATA,
    )
    assert_expression_basket(
        client,
        url_to_the_thing=SCHEMA_URL,
        expected_hashes=[SCHEMA_METADATA_HASH],
    )
