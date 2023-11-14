from primitive_metadata import primitive_rdf as rdf
from trove.vocab.namespaces import (
    DCAT,
    DCTERMS,
    FOAF,
    RDF,
    RDFS,
)


# try describing osf:addons data in rdf

ADDONS = rdf.IriNamespace('https://addons.osf.example/vocab/2023/')

EXAMPLE_ADDONS_DATA = {
    # osfstorage provider:
    'https://addons.osf.example/storage/osfstorage': {
        RDF.type: {ADDONS.StorageProvider},
        FOAF.name: {rdf.literal('osf:storage', language='en')},
        DCTERMS.description: {rdf.literal('...')},
        ADDONS.supportedInterface: {
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
        ADDONS.icon: {'https://addons.osf.example/storage/osfstorage/icon.svg'},
        # ...
    },
    # hypothetical checksum-keyed archive:
    'https://addons.osf.example/storage/checksum': {
        RDF.type: {ADDONS.StorageProvider},
        FOAF.name: {rdf.literal('checksum-keyed archive', language='en')},
        DCTERMS.description: {rdf.literal('(seems like a good idea)')},
        ADDONS.supportedInterface: {
            ADDONS.read_by_key,
            ADDONS.write_by_key,
            ADDONS.static_key,  # guaranteed not to change (until checksum collision)
            ADDONS.bulk_download,
            ADDONS.public_storage,
            ADDONS.longterm_archive,
        },
    },
    # authorization for osf:storage:
    'https://addons.osf.example/authorized/my-osfstorage': {
        RDF.type: {ADDONS.AuthorizedStorage},
        DCTERMS.creator: {'https://osf.io/blarg'},
        DCAT.accessService: {'https://addons.osf.example/addon/osfstorage'},
        ADDONS.authorizedInterface: {
            ADDONS.read_by_key,
            ADDONS.write_by_key,
            ADDONS.copy_by_key,
            ADDONS.path_key,  # supports filetree-like operations on key
            ADDONS.versioned_key,
            ADDONS.bulk_download,
            ADDONS.public_storage,
        },
        ADDONS.credentials: {
            # credential object(s)... TODO: find a standard vocab for that
        },
    },
    # authorization for checksum-archive:
    'https://addons.osf.example/authorized/aoeu': {
        RDF.type: {ADDONS.AuthorizedStorage},
        DCTERMS.creator: {'https://osf.io/blarg'},
        DCAT.accessService: {'https://addons.osf.example/addon/checksum'},
        ADDONS.authorizedInterface: {  # can auth less than is supported (but not more)
            ADDONS.read_by_key,
            ADDONS.write_by_key,
            ADDONS.static_key,
        },
        ADDONS.credentials: {
            # credential object(s)... TODO: find a standard vocab for that
        },
    },
    # connecting osf:storage to a project:
    'https://addons.osf.example/connected/my-osfstorage': {
        RDF.type: {ADDONS.ConnectedStorage},
        ADDONS.authorizedStorage: {'https://addons.osf.example/authorized/my-osfstorage'},
        ADDONS.connectedResource: {'https://osf.io/prjct'},
        ADDONS.connectedInterface: {  # can connect less than is auth'd (but not more)
            ADDONS.read_by_key,
            ADDONS.write_by_key,
            ADDONS.path_key,
        },
    },
    # connecting checksum-archive to a project:
    'https://addons.osf.example/connected/snth': {
        RDF.type: {ADDONS.ConnectedStorage},
        ADDONS.authorizedStorage: {'https://addons.osf.example/authorized/aoeu'},
        ADDONS.connectedResource: {'https://osf.io/prjct'},
        ADDONS.connectedInterface: {
            ADDONS.read_by_key,  # read-only connection
        },
    },
}

ADDONS_VOCAB = {
    ADDONS.ExternalAccount: {
        RDF.type: {RDFS.Class}
    },
    ADDONS.supportedInterface: {
        RDF.type: {RDF.Property}
    },
    ADDONS.authorizedInterface: {
        RDF.type: {RDF.Property}
    },
    ADDONS.connectedInterface: {
        RDF.type: {RDF.Property}
    },
    ADDONS.StorageProvider: {
        RDF.type: {RDFS.Class, ADDONS.Category},
    },
    ADDONS.authorizedStorage: {
        RDF.type: {RDF.Property}
    },
    ADDONS.connectedResource: {
        RDF.type: {RDF.Property}
    },
    ADDONS.authorizedStorage: {
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
    # ...
}
