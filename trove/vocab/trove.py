from django.conf import settings
from gather import primitive_rdf

from share.util.rdfutil import IriLabeler
from trove.vocab.namespaces import TROVE, JSONAPI, RDF, RDFS, OWL


# using linked anchors on the jsonapi spec as iris (probably fine)
JSONAPI_MEMBERNAME = JSONAPI['document-member-names']
JSONAPI_RELATIONSHIP = JSONAPI['document-resource-object-relationships']
JSONAPI_ATTRIBUTE = JSONAPI['document-resource-object-attributes']


# some assumed-safe assumptions for iris in trovespace:
# - a name ending in forward slash (`/`) is a namespace
# - an iri fragment (after `#`) is a `,`-separated list
#   of iris; a path of predicates from the root of that
#   index card (for the iri with `#` and after removed)
# - TODO: each iri is an irL that resolves to rdf, html

TROVE_API_VOCAB: primitive_rdf.RdfTripleDictionary = {

    # types:
    TROVE.Indexcard: {
        RDF.type: {RDFS.Class},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('index-card', language_tag='en'),
        },
    },
    TROVE.Cardsearch: {
        RDF.type: {RDFS.Class},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('index-card-search', language_tag='en'),
        },
    },
    TROVE.Propertysearch: {
        RDF.type: {RDFS.Class},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('index-property-search', language_tag='en'),
        },
    },
    TROVE.Valuesearch: {
        RDF.type: {RDFS.Class},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('index-value-search', language_tag='en'),
        },
    },
    TROVE.CardsearchResult: {
        RDF.type: {RDFS.Class},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('search-result', language_tag='en'),
        },
    },
    TROVE.ValuesearchResult: {
        RDF.type: {RDFS.Class},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('value-search-result', language_tag='en'),
        },
    },
    TROVE.TextMatchEvidence: {
        RDF.type: {RDFS.Class},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('TextMatchEvidence', language_tag='en'),
        },
    },
    TROVE.IriMatchEvidence: {
        RDF.type: {RDFS.Class},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('IriMatchEvidence', language_tag='en'),
        },
    },

    # attributes:
    TROVE.totalResultCount: {
        RDF.type: {RDF.Property, OWL.FunctionalProperty, JSONAPI_ATTRIBUTE},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('totalResultCount', language_tag='en'),
        },
    },
    TROVE.cardsearchText: {
        RDF.type: {RDF.Property, OWL.FunctionalProperty, JSONAPI_ATTRIBUTE},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('cardSearchText', language_tag='en'),
        },
    },
    TROVE.propertysearchText: {
        RDF.type: {RDF.Property, OWL.FunctionalProperty, JSONAPI_ATTRIBUTE},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('propertySearchText', language_tag='en'),
        },
    },
    TROVE.valuesearchText: {
        RDF.type: {RDF.Property, OWL.FunctionalProperty, JSONAPI_ATTRIBUTE},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('valueSearchText', language_tag='en'),
        },
    },
    TROVE.valuesearchPropertyPath: {
        RDF.type: {RDF.Property, OWL.FunctionalProperty, JSONAPI_ATTRIBUTE},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('valueSearchPropertyPath', language_tag='en'),
        },
    },
    TROVE.cardsearchFilter: {
        RDF.type: {RDF.Property, JSONAPI_ATTRIBUTE},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('cardSearchFilter', language_tag='en'),
        },
    },
    TROVE.propertysearchFilter: {
        RDF.type: {RDF.Property, JSONAPI_ATTRIBUTE},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('propertySearchFilter', language_tag='en'),
        },
    },
    TROVE.valuesearchFilter: {
        RDF.type: {RDF.Property, JSONAPI_ATTRIBUTE},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('valueSearchFilter', language_tag='en'),
        },
    },
    TROVE.matchEvidence: {
        RDF.type: {RDF.Property, JSONAPI_ATTRIBUTE},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('matchEvidence', language_tag='en'),
        },
    },
    TROVE.resourceIdentifier: {
        RDF.type: {RDF.Property, JSONAPI_ATTRIBUTE},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('resourceIdentifier', language_tag='en'),
        },
    },
    TROVE.resourceMetadata: {
        RDF.type: {RDF.Property, OWL.FunctionalProperty, JSONAPI_ATTRIBUTE},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('resourceMetadata', language_tag='en'),
        },
    },
    TROVE.matchingHighlight: {
        RDF.type: {RDF.Property, JSONAPI_ATTRIBUTE},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('matchingHighlight', language_tag='en'),
        },
    },
    TROVE.propertyPath: {
        RDF.type: {RDF.Property, OWL.FunctionalProperty},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('iriPropertyPath', language_tag='en'),
        },
    },
    TROVE.osfmapPropertyPath: {
        RDF.type: {RDF.Property, OWL.FunctionalProperty},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('osfmapPropertyPath', language_tag='en'),
        },
    },
    TROVE.filterType: {
        RDF.type: {RDF.Property, OWL.FunctionalProperty},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('filterType', language_tag='en'),
        },
    },
    TROVE.filterValue: {
        RDF.type: {RDF.Property},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('filterValue', language_tag='en'),
        },
    },
    TROVE.iriValue: {
        RDF.type: {RDF.Property, OWL.FunctionalProperty, JSONAPI_ATTRIBUTE},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('iriValue', language_tag='en'),
        },
    },
    TROVE.matchUsageCount: {
        RDF.type: {RDF.Property, OWL.FunctionalProperty, JSONAPI_ATTRIBUTE},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('matchUsageCount', language_tag='en'),
        },
    },
    TROVE.totalUsageCount: {
        RDF.type: {RDF.Property, OWL.FunctionalProperty, JSONAPI_ATTRIBUTE},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('totalUsageCount', language_tag='en'),
        },
    },
    TROVE.namelikeText: {
        RDF.type: {RDF.Property, JSONAPI_ATTRIBUTE},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('namelikeText', language_tag='en'),
        },
    },

    # relationships:
    TROVE.searchResultPage: {
        RDF.type: {RDF.Property, JSONAPI_RELATIONSHIP},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('searchResultPage', language_tag='en'),
        },
    },
    TROVE.evidenceCard: {
        RDF.type: {RDF.Property, OWL.FunctionalProperty, JSONAPI_RELATIONSHIP},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('evidenceCard', language_tag='en'),
        },
    },
    TROVE.relatedPropertysearch: {
        RDF.type: {RDF.Property, JSONAPI_RELATIONSHIP},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('relatedPropertySearch', language_tag='en'),
        },
    },
    TROVE.indexCard: {
        RDF.type: {RDF.Property, OWL.FunctionalProperty, JSONAPI_RELATIONSHIP},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('indexCard', language_tag='en'),
        },
    },

    # values:
    TROVE['ten-thousands-and-more']: {
        RDF.type: {RDF.Property},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('ten-thousands-and-more', language_tag='en'),
        },
    },
    TROVE['any-of']: {
        RDF.type: {RDF.Property},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('any-of', language_tag='en'),
        },
    },
    TROVE['none-of']: {
        RDF.type: {RDF.Property},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('none-of', language_tag='en'),
        },
    },
    TROVE.before: {
        RDF.type: {RDF.Property},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('before', language_tag='en'),
        },
    },
    TROVE.after: {
        RDF.type: {RDF.Property},
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('after', language_tag='en'),
        },
    },

    # other:
    RDF.type: {
        JSONAPI_MEMBERNAME: {
            primitive_rdf.text('@type'),
        },
    },
}

trove_labeler = IriLabeler(TROVE_API_VOCAB, label_iri=JSONAPI_MEMBERNAME)


def trove_indexcard_namespace():
    return primitive_rdf.IriNamespace(f'{settings.SHARE_API_URL}trove/index-card/')


def trove_indexcard_iri(indexcard_uuid):
    return trove_indexcard_namespace()[str(indexcard_uuid)]
