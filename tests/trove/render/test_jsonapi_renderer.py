import json
from unittest import mock

from trove.render.jsonapi import RdfJsonapiRenderer
from trove.render._rendering import SimpleRendering
from ._inputs import BLARG
from . import _base


def _jsonapi_item_sortkey(jsonapi_item: dict):
    return (jsonapi_item.get('type'), jsonapi_item.get('id'))


class _BaseJsonapiRendererTest(_base.TroveJsonRendererTests):
    renderer_class = RdfJsonapiRenderer

    def setUp(self):
        super().setUp()
        self.enterContext(
            mock.patch('trove.render.jsonapi.time.time_ns', return_value=112358)
        )

    def _get_rendered_output(self, rendering):
        _json = super()._get_rendered_output(rendering)
        _included = _json.get('included')
        if _included:
            # order of includes does not matter
            _included.sort(key=_jsonapi_item_sortkey)
        return _json


class TestJsonapiRenderer(_BaseJsonapiRendererTest):
    expected_outputs = {
        'simple_card': SimpleRendering(
            mediatype='application/vnd.api+json',
            rendered_content=json.dumps({
                "data": {
                    "id": "aHR0cDovL2JsYXJnLmV4YW1wbGUvdm9jYWIvYUNhcmQ=",
                    "type": "index-card",
                    "attributes": {
                        "resourceIdentifier": [
                            BLARG.anItem
                        ],
                        "resourceMetadata": {
                            "@id": BLARG.anItem,
                            "title": "an item, yes"
                        }
                    },
                    "links": {
                        "self": BLARG.aCard
                    },
                    "meta": {
                        "foaf:primaryTopic": [
                            BLARG.anItem
                        ],
                        "dcterms:issued": [
                            "2024-01-01"
                        ],
                        "dcterms:modified": [
                            "2024-01-01"
                        ]
                    },
                }
            }),
        ),
        'various_types': SimpleRendering(
            mediatype='application/vnd.api+json',
            rendered_content=json.dumps({
                "data": {
                    "id": "aHR0cDovL2JsYXJnLmV4YW1wbGUvdm9jYWIvYVN1YmplY3Q=",
                    "type": BLARG.aType,
                    "meta": {
                        BLARG.hasIri: [BLARG.anIri],
                        BLARG.hasRdfStringLiteral: ["an rdf:string literal"],
                        BLARG.hasRdfLangStringLiteral: ['a rdf:langString literal'],
                        BLARG.hasIntegerLiteral: [17],
                        BLARG.hasDateLiteral: ["2024-01-01"],
                        BLARG.hasStrangeLiteral: ['a literal of strange datatype'],
                    },
                    "links": {"self": BLARG.aSubject},
                }
            }),
        ),
    }


class TestJsonapiSearchRenderer(_BaseJsonapiRendererTest, _base.TrovesearchJsonRendererTests):
    expected_outputs = {
        'no_results': SimpleRendering(
            mediatype='application/vnd.api+json',
            rendered_content=json.dumps({
                "data": {
                    "id": "aHR0cDovL2JsYXJnLmV4YW1wbGUvdm9jYWIvYVNlYXJjaA==",
                    "type": "index-card-search",
                    "attributes": {
                        "totalResultCount": 0,
                    },
                    "links": {
                        "self": BLARG.aSearch,
                    }
                }
            }),
        ),
        'few_results': SimpleRendering(
            mediatype='application/vnd.api+json',
            rendered_content=json.dumps({
                "data": {
                    "id": "aHR0cDovL2JsYXJnLmV4YW1wbGUvdm9jYWIvYVNlYXJjaEZldw==",
                    "type": "index-card-search",
                    "attributes": {
                        "totalResultCount": 3
                    },
                    "relationships": {
                        "searchResultPage": {
                            "data": [
                                {
                                    "id": "dc0604c7e9c07576b57646119784de65e7204fc7c860cc1b9be8ebec5f2b96ba",
                                    "type": "search-result"
                                },
                                {
                                    "id": "367b30e8a0eece555ac15fda82bb28f535f1f8beb97397c01162d619cd7058bc",
                                    "type": "search-result"
                                },
                                {
                                    "id": "26afa96fdbd189e4c4aeac921a42e9d3f09eb94b59ffd4b9ad300c524536cc97",
                                    "type": "search-result"
                                }
                            ]
                        }
                    },
                    "links": {
                        "self": BLARG.aSearchFew
                    }
                },
                "included": [
                    {
                        "id": "dc0604c7e9c07576b57646119784de65e7204fc7c860cc1b9be8ebec5f2b96ba",
                        "type": "search-result",
                        "relationships": {
                            "indexCard": {
                                "data": {
                                    "id": "aHR0cDovL2JsYXJnLmV4YW1wbGUvdm9jYWIvYUNhcmQ=",
                                    "type": "index-card"
                                }
                            }
                        }
                    },
                    {
                        "id": "26afa96fdbd189e4c4aeac921a42e9d3f09eb94b59ffd4b9ad300c524536cc97",
                        "type": "search-result",
                        "relationships": {
                            "indexCard": {
                                "data": {
                                    "id": "db657130943f3c9f4cc527b23a6a246b095f62673f2cc7fc906d5914678bd337",
                                    "type": "index-card"
                                }
                            }
                        }
                    },
                    {
                        "id": "367b30e8a0eece555ac15fda82bb28f535f1f8beb97397c01162d619cd7058bc",
                        "type": "search-result",
                        "relationships": {
                            "indexCard": {
                                "data": {
                                    "id": "4e6134629cc3117a123cee8a8dc633a46401c9725f01d63f689d7b84f2422359",
                                    "type": "index-card"
                                }
                            }
                        }
                    },
                    {
                        "id": "aHR0cDovL2JsYXJnLmV4YW1wbGUvdm9jYWIvYUNhcmQ=",
                        "type": "index-card",
                        "meta": {
                            "foaf:primaryTopic": [
                                BLARG.anItem
                            ],
                            "dcterms:issued": [
                                "2024-01-01"
                            ],
                            "dcterms:modified": [
                                "2024-01-01"
                            ]
                        },
                        "attributes": {
                            "resourceIdentifier": [
                                BLARG.anItem
                            ],
                            "resourceMetadata": {
                                "@id": BLARG.anItem,
                                "title": "an item, yes"
                            }
                        },
                        "links": {
                            "self": BLARG.aCard
                        }
                    },
                    {
                        "id": "db657130943f3c9f4cc527b23a6a246b095f62673f2cc7fc906d5914678bd337",
                        "type": "index-card",
                        "meta": {
                            "foaf:primaryTopic": [
                                BLARG.anItemmm
                            ],
                            "dcterms:issued": [
                                "2024-03-03"
                            ],
                            "dcterms:modified": [
                                "2024-03-03"
                            ]
                        },
                        "attributes": {
                            "resourceIdentifier": [
                                BLARG.anItemmm
                            ],
                            "resourceMetadata": {
                                "@id": BLARG.anItemmm,
                                "title": "an itemmm, yes"
                            }
                        },
                        "links": {
                            "self": BLARG.aCarddd
                        }
                    },
                    {
                        "id": "4e6134629cc3117a123cee8a8dc633a46401c9725f01d63f689d7b84f2422359",
                        "type": "index-card",
                        "meta": {
                            "foaf:primaryTopic": [
                                BLARG.anItemm
                            ],
                            "dcterms:issued": [
                                "2024-02-02"
                            ],
                            "dcterms:modified": [
                                "2024-02-02"
                            ]
                        },
                        "attributes": {
                            "resourceIdentifier": [
                                BLARG.anItemm
                            ],
                            "resourceMetadata": {
                                "@id": BLARG.anItemm,
                                "title": "an itemm, yes"
                            }
                        },
                        "links": {
                            "self": BLARG.aCardd
                        }
                    }
                ],
            }),
        ),
    }
