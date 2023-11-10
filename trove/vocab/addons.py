from primitive_metadata import primitive_rdf as rdf
from trove.vocab.namespaces import (
    DCAT,
    DCTERMS,
    FOAF,
    RDF,
    RDFS,
)


ADDONS = rdf.IriNamespace('https://addons.osf.io/vocab/2023/')

EXAMPLE_DATA = {
    'http://foo.example/storage/checksum': {
        RDF.type: {ADDONS.StorageProvider},
        FOAF.name: {rdf.literal('checksum-keyed archive', language='en')},
        DCTERMS.description: {rdf.literal('...')},
        ADDONS.supportsInterface: {
            ADDONS.read_by_key,
            ADDONS.write_by_key,
            ADDONS.static_key,
            ADDONS.bulk_download,
            ADDONS.public_storage,
            ADDONS.longterm_archive,
        },
    },
    'http://foo.example/storage/dropbox': {
        RDF.type: {ADDONS.StorageProvider},
        FOAF.name: {rdf.literal('dropbox maybe', language='en')},
        DCTERMS.description: {rdf.literal('...')},
        ADDONS.supportsInterface: {
            ADDONS.read_by_key,
            ADDONS.write_by_key,
            ADDONS.copy_by_key,
            ADDONS.path_key,
            ADDONS.versioned_key,
            ADDONS.bulk_download,
            ADDONS.public_storage,
        },
        ADDONS.maxConcurrentDownloads: {rdf.literal(42)},
        ADDONS.maxUploadMB: {rdf.literal(150)},
        ADDONS.icon: {'http://foo.example/storage/dropbox/icon.svg'},
        # ...
    },
    'http://foo.example/authorized/aoeu': {
        RDF.type: {ADDONS.AuthorizedStorage},
        DCTERMS.creator: {'https://osf.io/blarg'},
        DCAT.accessService: {'http://foo.example/addon/checksum'},
        ADDONS.authorizedInterface: {
            ADDONS.read_by_key,
            ADDONS.write_by_key,
            ADDONS.static_key,
        },
        # auth stuff...
    },
    'http://foo.example/connected/snth': {
        RDF.type: {ADDONS.ConnectedStorage},
        ADDONS.authorizedStorage: {'http://foo.example/authorized/aoeu'},
        ADDONS.connectedResource: {'https://osf.io/prjct'},
        ADDONS.connectedInterface: {
            ADDONS.read_by_key,
        },
    },
    'http://foo.example/authorized/my-dropbox': {
        RDF.type: {ADDONS.AuthorizedStorage},
        DCTERMS.creator: {'https://osf.io/blarg'},
        DCAT.accessService: {'http://foo.example/addon/dropbox'},
        ADDONS.authorizedInterface: {
            ADDONS.read_by_key,
            ADDONS.write_by_key,
            ADDONS.copy_by_key,
            ADDONS.path_key,
            ADDONS.versioned_key,
            ADDONS.bulk_download,
            ADDONS.public_storage,
        },
        # auth stuff...
    },
    'http://foo.example/connected/my-dropbox': {
        RDF.type: {ADDONS.ConnectedStorage},
        ADDONS.authorizedStorage: {'http://foo.example/authorized/my-dropbox'},
        ADDONS.connectedResource: {'https://osf.io/prjct'},
        ADDONS.connectedInterface: {
            ADDONS.read_by_key,
            ADDONS.write_by_key,
            ADDONS.path_key,
        },
    },
}

ADDONS_VOCAB = {
    ADDONS.ExternalAccount: {
        RDF.type: {RDFS.Class}
    },
    ADDONS.supportsInterface: {
        RDF.type: {RDF.Property}
    },
    ADDONS.read_by_key: {
        RDF.type: {ADDONS.Interface}
    },
    ADDONS.write_by_key: {
        RDF.type: {ADDONS.Interface}
    },
    ADDONS.static_key: {
        RDF.type: {ADDONS.Interface}
    },
    ADDONS.path_key: {
        RDF.type: {ADDONS.Interface}
    },
    ADDONS.StorageProvider: {
        RDF.type: {RDFS.Class, ADDONS.Category},
    },
}
