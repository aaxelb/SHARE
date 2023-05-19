import json
import logging
import typing

import elasticsearch8
import rdflib

from share import models as db
from share.search import exceptions
from share.search import messages
from share.search.index_strategy.elastic8 import Elastic8IndexStrategy
from share.search import search_params
# from share.search.search_response import ApiSearchResponse
from share.util import IDObfuscator
from share.util.checksum_iris import ChecksumIri


logger = logging.getLogger(__name__)


# TODO: use the actual terms referenced by OSFMAP (DCTERMS, etc.)
OSFMAP = rdflib.Namespace('https://osf.io/vocab/2023/')

TEXT_FIELDS = (  # TODO: is this all?
    'title',
    'description',
    'tags',
)
KEYWORD_FIELDS_BY_OSFMAP = {
    OSFMAP.identifier: 'identifiers',
    OSFMAP.creator: 'lists.contributors.identifiers',  # note: contributor types lumped together
    OSFMAP.publisher: 'lists.publishers.identifiers',
    OSFMAP.subject: 'subjects',  # note: |-delimited taxonomic path
    OSFMAP.language: 'language',
    OSFMAP.resourceType: 'types',  # TODO: map type hierarchy
    OSFMAP.resourceTypeGeneral: 'types',
    OSFMAP.affiliatedInstitution: 'lists.affiliations.identifiers',
    OSFMAP.funder: 'lists.funders.identifiers',
    OSFMAP.keyword: 'tags.exact',
}
DATE_FIELDS_BY_OSFMAP = {
    # missing: OSFMAP.embargoEndDate, OSFMAP.dateOfCopyright
    OSFMAP.date: 'date',
    OSFMAP.created: 'date_published',  # note: NOT 'date_created'
    OSFMAP.modified: 'date_updated',  # note: NOT 'date_modified'
}


class Sharev2Elastic8IndexStrategy(Elastic8IndexStrategy):
    CURRENT_STRATEGY_CHECKSUM = ChecksumIri(
        checksumalgorithm_name='sha-256',
        salt='Sharev2Elastic8IndexStrategy',
        hexdigest='bcaa90e8fa8a772580040a8edbedb5f727202d1fca20866948bc0eb0e935e51f',
    )

    # abstract method from IndexStrategy
    @property
    def supported_message_types(self):
        return {
            messages.MessageType.INDEX_SUID,
            messages.MessageType.BACKFILL_SUID,
        }

    # abstract method from Elastic8IndexStrategy
    def index_settings(self):
        return {
            'analysis': {
                'analyzer': {
                    'default': {
                        # same as 'standard' analyzer, plus html_strip
                        'type': 'custom',
                        'tokenizer': 'standard',
                        'filter': ['lowercase', 'stop'],
                        'char_filter': ['html_strip']
                    },
                    'subject_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'subject_tokenizer',
                        'filter': [
                            'lowercase',
                        ]
                    },
                    'subject_search_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'keyword',
                        'filter': [
                            'lowercase',
                        ]
                    },
                },
                'tokenizer': {
                    'subject_tokenizer': {
                        'type': 'path_hierarchy',
                        'delimiter': '|',
                    }
                }
            }
        }

    # abstract method from Elastic8IndexStrategy
    def index_mappings(self):
        exact_field = {
            'exact': {
                'type': 'keyword',
                # From Elasticsearch documentation:
                # The value for ignore_above is the character count, but Lucene counts bytes.
                # If you use UTF-8 text with many non-ASCII characters, you may want to set the limit to 32766 / 3 = 10922 since UTF-8 characters may occupy at most 3 bytes
                'ignore_above': 10922
            }
        }
        return {
            'dynamic': False,
            'properties': {
                'affiliations': {'type': 'text', 'fields': exact_field},
                'contributors': {'type': 'text', 'fields': exact_field},
                'date': {'type': 'date', 'format': 'strict_date_optional_time'},
                'date_created': {'type': 'date', 'format': 'strict_date_optional_time'},
                'date_modified': {'type': 'date', 'format': 'strict_date_optional_time'},
                'date_published': {'type': 'date', 'format': 'strict_date_optional_time'},
                'date_updated': {'type': 'date', 'format': 'strict_date_optional_time'},
                'description': {'type': 'text'},
                'funders': {'type': 'text', 'fields': exact_field},
                'hosts': {'type': 'text', 'fields': exact_field},
                'id': {'type': 'keyword'},
                'identifiers': {'type': 'text', 'fields': exact_field},
                'justification': {'type': 'text'},
                'language': {'type': 'keyword'},
                'publishers': {'type': 'text', 'fields': exact_field},
                'registration_type': {'type': 'keyword'},
                'retracted': {'type': 'boolean'},
                'source_config': {'type': 'keyword'},
                'source_unique_id': {'type': 'keyword'},
                'sources': {'type': 'keyword'},
                'subjects': {'type': 'text', 'analyzer': 'subject_analyzer', 'search_analyzer': 'subject_search_analyzer'},
                'subject_synonyms': {'type': 'text', 'analyzer': 'subject_analyzer', 'search_analyzer': 'subject_search_analyzer', 'copy_to': 'subjects'},
                'tags': {'type': 'text', 'fields': exact_field},
                'title': {'type': 'text', 'fields': exact_field},
                'type': {'type': 'keyword'},
                'types': {'type': 'keyword'},
                'withdrawn': {'type': 'boolean'},
                'osf_related_resource_types': {'type': 'object', 'dynamic': True},
                'lists': {'type': 'object', 'dynamic': True},
            },
            'dynamic_templates': [
                {'exact_field_on_lists_strings': {'path_match': 'lists.*', 'match_mapping_type': 'string', 'mapping': {'type': 'text', 'fields': exact_field}}},
            ]
        }

    # abstract method from Elastic8IndexStrategy
    def build_elastic_actions(self, messages_chunk: messages.MessagesChunk):
        suid_ids = set(messages_chunk.target_ids_chunk)
        record_qs = db.FormattedMetadataRecord.objects.filter(
            suid_id__in=suid_ids,
            record_format='sharev2_elastic',
        )
        for record in record_qs:
            suid_ids.discard(record.suid_id)
            source_doc = json.loads(record.formatted_metadata)
            if source_doc.pop('is_deleted', False):
                yield self._build_delete_action(record.suid_id)
            else:
                yield self._build_index_action(record.suid_id, source_doc)
        # delete any that don't have the expected FormattedMetadataRecord
        for leftover_suid_id in suid_ids:
            yield self._build_delete_action(leftover_suid_id)

    # override Elastic8IndexStrategy
    def get_doc_id(self, message_target_id):
        return IDObfuscator.encode_id(message_target_id, db.SourceUniqueIdentifier)

    # override Elastic8IndexStrategy
    def get_message_target_id(self, doc_id):
        return IDObfuscator.decode_id(doc_id)

    def _build_index_action(self, target_id, source_doc):
        return {
            '_op_type': 'index',
            '_id': self.get_doc_id(target_id),
            '_source': source_doc,
        }

    def _build_delete_action(self, target_id):
        return {
            '_op_type': 'delete',
            '_id': self.get_doc_id(target_id),
        }

    class SpecificIndex(Elastic8IndexStrategy.SpecificIndex):
        # optional method from IndexStrategy.SpecificIndex
        def pls_handle_search__sharev2_backcompat(self, request_body=None, request_queryparams=None) -> dict:
            try:
                json_response = self.index_strategy.es8_client.search(
                    index=self.indexname,
                    body={
                        **request_body,
                        'track_total_hits': True,
                    },
                    params=(request_queryparams or {}),
                )
            except elasticsearch8.TransportError as error:
                raise exceptions.IndexStrategyError() from error  # TODO: error messaging
            try:  # mangle response for some limited backcompat with elasticsearch5
                es8_total = json_response['hits']['total']
                json_response['hits']['total'] = es8_total['value']
                json_response['hits']['_total'] = es8_total
            except KeyError:
                pass
            return json_response

        def pls_handle_cardsearch(
            self,
            cardsearch_params: search_params.CardsearchParams,
        ):  # -> ApiSearchResponse:
            es8_query = {
                'bool': self._cardsearch_bool_query(cardsearch_params),
            }

            logger.critical(json.dumps(es8_query, indent=2))
            try:
                json_response = self.index_strategy.es8_client.search(
                    index=self.indexname,
                    query=es8_query,
                    highlight={
                        'fields': {
                            fieldname: {
                                'highlight_query': {
                                    'match': cardsearch_params.cardsearch_text,
                                }
                            }
                            for fieldname in TEXT_FIELDS
                        },
                    },
                )
            except elasticsearch8.TransportError as error:
                raise exceptions.IndexStrategyError() from error  # TODO: error messaging
            return json_response.body  # TODO: return shaclbasket

        def _filter_path_to_fieldname(self, filter_path: tuple[str]):
            try:
                # TODO: better
                return KEYWORD_FIELDS_BY_OSFMAP[OSFMAP[filter_path[0]]]
            except KeyError:
                raise NotImplementedError('TODO')

        def _cardsearch_bool_query(self, search_params) -> dict:
            bool_query = {
                'filter': list(self._cardsearch_filter(search_params)),
                'must': [],
                'must_not': [],
                'should': [],
            }
            for textsegment in search_params.cardsearch_textsegment_list:
                if textsegment.is_negated:
                    bool_query['must_not'].append(
                        self._excluded_text_query(textsegment)
                    )
                else:
                    bool_query['should'].extend(
                        self._fuzzy_text_query_iter(textsegment)
                    )
                    if not textsegment.is_fuzzy:
                        bool_query['must'].append(
                            self._exact_text_query(textsegment)
                        )
            return bool_query

        def _cardsearch_filter(self, search_params) -> typing.Iterable[dict]:
            for search_filter in search_params.cardsearch_filter_set:
                fieldname = self._filter_path_to_fieldname(search_filter.property_path)
                yield {'terms': {
                    fieldname: list(search_filter.value_set),
                }}

        def _excluded_text_query(self, textsegment: search_params.Textsegment):
            return {'multi_match': {
                'type': 'phrase',
                'query': textsegment.text,
                'fields': TEXT_FIELDS,
            }}

        def _exact_text_query(self, textsegment: search_params.Textsegment):
            assert not textsegment.is_fuzzy
            if textsegment.is_openended:
                return {'multi_match': {
                    'type': 'phrase_prefix',
                    'query': textsegment.text,
                    'fields': TEXT_FIELDS,
                }}
            return {'multi_match': {
                'type': 'phrase',
                'query': textsegment.text,
                'fields': TEXT_FIELDS,
            }}

        def _fuzzy_text_query_iter(self, textsegment: search_params.Textsegment):
            wordcount = len(textsegment.text.split())

            def _fuzzy_text_query(field_name: str):
                yield {'match': {
                    field_name: {
                        'query': textsegment.text,
                        'fuzziness': 'AUTO',
                    },
                }}
                if wordcount > 1:
                    yield {(
                        'match_phrase_prefix'
                        if textsegment.is_openended
                        else 'match_phrase'
                    ): {
                        field_name: {
                            'query': textsegment.text,
                            'slop': wordcount,
                        },
                    }}

            for field_name in TEXT_FIELDS:
                yield from _fuzzy_text_query(field_name)
