import contextlib
import dataclasses
import datetime
import json
import logging
import uuid
from typing import Iterable

import elasticsearch8
from gather import primitive_rdf

from share.search.index_strategy.elastic8 import Elastic8IndexStrategy
from share.search import exceptions
from share.search import messages
from share.search.search_request import (
    CardsearchParams,
    PropertysearchParams,
    ValuesearchParams,
    SearchFilter,
    Textsegment,
)
from share.search.search_response import (
    CardsearchResponse,
    PropertysearchResponse,
    ValuesearchResponse,
    TextMatchEvidence,
    SearchResult,
)
from share.util.checksum_iri import ChecksumIri
from trove import models as trove_db
from trove.vocab.namespaces import TROVE, OSFMAP, DCTERMS


logger = logging.getLogger(__name__)


class TroveIdentifierIndexStrategy(Elastic8IndexStrategy):
    CURRENT_STRATEGY_CHECKSUM = ChecksumIri(
        checksumalgorithm_name='sha-256',
        salt='TroveIdentifierIndexStrategy',
        hexdigest='cb4234da3354de21ff840a6740e8768e82a1e4ea6fb519660a51cb5720bef96d',
    )

    @property
    def supported_message_types(self):
        return {
            messages.MessageType.IDENTIFIER_INDEXED,
            messages.MessageType.BACKFILL_IDENTIFIER,
        }

    def index_settings(self):
        return {}

    def index_mappings(self):
        return {
            'dynamic': 'false',
            'properties': {
                'iri': {'type': 'keyword'},
                'namespace_iri': {'type': 'keyword'},
                'is_value_for_property': {'type': 'keyword'},
                'is_value_for_propertypath': {'type': 'keyword'},
                'namelike_text': {
                    'type': 'text',
                    'fields': {
                        'keyword': {'type': 'keyword'},
                    },
                },
                'related_text': {
                    'type': 'text',
                },
            },
        }

    def _build_sourcedoc(self, identifier: trove_db.ResourceIdentifier):
        _indexcard_agg = {  # TODO: run on TroveIndexcardIndexStrategy
            'for_nested_iri': {'nested': {
                'path': 'nested_iri',
                'aggs': {  # TODO: filter to correct nested
                    'for_property': {'terms': {
                        'field': 'nested_iri.property_iri',
                    }},
                    'for_path_from_focus': {'terms': {
                        'field': 'nested_iri.path_from_focus',
                    }},
                    'for_path_from_subject': {'terms': {
                        'field': 'nested_iri.path_from_nearest_subject',
                    }},
                },
            }},
        }
        return {
            'iri': identifier.iris_list(),
            # TODO:
            'namespace_iri': [],
            'is_value_for_property': [],
            'is_value_for_propertypath': [],
            'namelike_text': [],
            'related_text': [],
        }

    def build_elastic_actions(self, messages_chunk: messages.MessagesChunk):
        _identifier_qs = (
            trove_db.ResourceIdentifier.objects
            .filter(id__in=messages_chunk.target_ids_chunk)
            .prefetch_related('indexcard_set')
        )
        _remaining_identifier_ids = set(messages_chunk.target_ids_chunk)
        for _identifier in _identifier_qs:
            _remaining_identifier_ids.discard(_identifier.id)
            _index_action = self.build_index_action(
                doc_id=_identifier.sufficiently_unique_iri,
                doc_source=self._build_sourcedoc(_identifier),
            )
            yield _identifier.id, _index_action
        # delete any that don't have any of the expected card
        _leftovers = (
            trove_db.ResourceIdentifier.objects
            .filter(id__in=_remaining_identifier_ids)
            .values_list('id', 'sufficiently_unique_iri')
        )
        for _id, _doc_id in _leftovers:
            yield _id, self.build_delete_action(_doc_id)

    class SpecificIndex(Elastic8IndexStrategy.SpecificIndex):
        def pls_handle_search__sharev2_backcompat(self, request_body=None, request_queryparams=None) -> dict:
            return self.index_strategy.es8_client.search(
                index=self.indexname,
                body={
                    **(request_body or {}),
                    'track_total_hits': True,
                },
                params=(request_queryparams or {}),
            )

        def pls_handle_cardsearch(self, cardsearch_params: CardsearchParams) -> CardsearchResponse:
            try:
                _es8_response = self.index_strategy.es8_client.search(
                    index=self.indexname,
                    query=_cardsearch_query(
                        cardsearch_params.cardsearch_filter_set,
                        cardsearch_params.cardsearch_textsegment_set,
                    ),
                    source=False,  # no need to get _source; _id is enough
                )
            except elasticsearch8.TransportError as error:
                raise exceptions.IndexStrategyError() from error  # TODO: error messaging
            return _cardsearch_response(cardsearch_params, _es8_response)

        def pls_handle_valuesearch(self, valuesearch_params: ValuesearchParams) -> ValuesearchResponse:
            try:
                _es8_response = self.index_strategy.es8_client.search(
                    index=self.indexname,
                    query=_valuesearch_outer_cardquery(valuesearch_params),
                    size=0,  # ignore cardsearch hits; just want the aggs
                    aggs=_valuesearch_aggs(valuesearch_params),
                )
                return dict(_es8_response)  # <<< DEBUG
            except elasticsearch8.TransportError as error:
                raise exceptions.IndexStrategyError() from error  # TODO: error messaging
            return _valuesearch_response(valuesearch_params, _es8_response)

        def pls_handle_propertysearch(self, propertysearch_params: PropertysearchParams) -> PropertysearchResponse:
            # _propertycard_filter = SearchFilter(
            #     property_path=(RDF.type,),
            #     value_set=frozenset([RDF.Property]),
            #     operator=SearchFilter.FilterOperator.ANY_OF,
            # )
            raise NotImplementedError('TODO: just static PropertysearchResponse somewhere')


###
# module-local functions

def _property_path_as_keyword(property_path) -> str:
    assert isinstance(property_path, (list, tuple))
    return json.dumps(property_path)


def _is_date_property(property_iri):
    # TODO: better inference (rdfs:range?)
    return property_iri in {
        DCTERMS.date,
        DCTERMS.available,
        DCTERMS.created,
        DCTERMS.modified,
        DCTERMS.dateCopyrighted,
        DCTERMS.dateSubmitted,
        DCTERMS.dateAccepted,
        OSFMAP.withdrawn,
    }


def _cardsearch_query(filter_set, textsegment_set, *, with_filters=None) -> dict:
    _bool_query = {
        'filter': with_filters or [],
        'must': [],
        'must_not': [],
        'should': [],
    }
    for _searchfilter in filter_set:
        if _searchfilter.operator == SearchFilter.FilterOperator.NONE_OF:
            _bool_query['must_not'].append(_iri_filter(_searchfilter))
        elif _searchfilter.operator == SearchFilter.FilterOperator.ANY_OF:
            _bool_query['filter'].append(_iri_filter(_searchfilter))
        elif _searchfilter.operator.is_date_operator():
            _bool_query['filter'].append(_date_filter(_searchfilter))
        else:
            raise ValueError(f'unknown filter operator {_searchfilter.operator}')
    _fuzzysegments = []
    for _textsegment in textsegment_set:
        if _textsegment.is_negated:
            _bool_query['must_not'].append(_excluded_text_query(_textsegment))
        elif _textsegment.is_fuzzy:
            _fuzzysegments.append(_textsegment)
        else:
            _bool_query['must'].append(_exact_text_query(_textsegment))
    if _fuzzysegments:
        _bool_query['must'].append(_fuzzy_text_must_query(_fuzzysegments))
        _bool_query['should'].extend(_fuzzy_text_should_queries(_fuzzysegments))
    return {'bool': _bool_query}


def _valuesearch_outer_cardquery(valuesearch_params: ValuesearchParams):
    _propertypath = _property_path_as_keyword(valuesearch_params.valuesearch_property_path)
    _filter_cards_with_propertypath = {'nested': {
        'path': 'nested_iri',
        'query': {'term': {
            'nested_iri.path_from_focus': _propertypath,
        }},
    }}
    return _cardsearch_query(
        valuesearch_params.cardsearch_filter_set,
        valuesearch_params.cardsearch_textsegment_set,
        with_filters=[_filter_cards_with_propertypath],
    )


def _valuesearch_aggs(valuesearch_params: ValuesearchParams):
    raise NotImplementedError


def _valuesearch_response(valuesearch_params, es8_response):
    raise NotImplementedError


def _iri_filter(search_filter) -> dict:
    _propertypath_keyword = _property_path_as_keyword(search_filter.property_path)
    return {'nested': {
        'path': 'nested_iri',
        'query': {'bool': {
            'filter': [
                {'term': {'nested_iri.path_from_focus': _propertypath_keyword}},
                {'terms': {'nested_iri.iri_value': list(search_filter.value_set)}},
            ],
        }},
    }}


def _date_filter(search_filter) -> dict:
    if search_filter.operator == SearchFilter.FilterOperator.BEFORE:
        _range_op = 'lt'
        _value = min(search_filter.value_set)  # lean on that isoformat
    elif search_filter.operator == SearchFilter.FilterOperator.AFTER:
        _range_op = 'gte'
        _value = max(search_filter.value_set)  # lean on that isoformat
    else:
        raise ValueError(f'invalid date filter operator (got {search_filter.operator})')
    _date_value = datetime.datetime.fromisoformat(_value).date()
    _propertypath_keyword = _property_path_as_keyword(search_filter.property_path)
    return {'nested': {
        'path': 'nested_date',
        'query': {'bool': {
            'filter': [
                {'term': {'nested_date.path_from_focus': _propertypath_keyword}},
                {'range': {'nested_date.date_value': {
                    _range_op: f'{_date_value}||/d',  # round to the day
                }}},
            ],
        }},
    }}


def _excluded_text_query(textsegment: Textsegment) -> dict:
    return {'nested': {
        'path': 'nested_text',
        'query': {'match_phrase': {
            'nested_text.text_value': {
                'query': textsegment.text,
            },
        }},
    }}


def _exact_text_query(textsegment: Textsegment) -> dict:
    # TODO: textsegment.is_openended (prefix query)
    _query = {'match_phrase': {
        'nested_text.text_value': {
            'query': textsegment.text,
        },
    }}
    return {'nested': {
        'path': 'nested_text',
        'query': _query,
        'inner_hits': _text_inner_hits(),
    }}


def _fuzzy_text_must_query(textsegments: list[Textsegment]) -> dict:
    # TODO: textsegment.is_openended (prefix query)
    _query = {'match': {
        'nested_text.text_value': {
            'query': ' '.join(
                _textsegment.text
                for _textsegment in textsegments
            ),
            'fuzziness': 'AUTO',
        },
    }}
    return {'nested': {
        'path': 'nested_text',
        'query': _query,
        'inner_hits': _text_inner_hits()
    }}


def _fuzzy_text_should_queries(textsegments: list[Textsegment]) -> Iterable[dict]:
    for _textsegment in textsegments:
        yield {'nested': {
            'path': 'nested_text',
            'query': {'match_phrase': {
                'nested_text.text_value': {
                    'query': _textsegment.text,
                    'slop': len(_textsegment.words()),
                },
            }}
        }}


def _text_inner_hits(*, highlight_query=None) -> dict:
    _highlight = {
        'type': 'unified',
        'fields': {'nested_text.text_value': {}},
    }
    if highlight_query is not None:
        _highlight['highlight_query'] = highlight_query
    return {
        'name': str(uuid.uuid4()),  # avoid inner-hit name collisions
        'highlight': _highlight,
        '_source': False,  # _source is expensive for nested docs
        'docvalue_fields': [
            'nested_text.path_from_focus',
            'nested_text.language_iri',
        ],
    }


def _cardsearch_response(cardsearch_params, es8_response) -> CardsearchResponse:
    _es8_total = es8_response['hits']['total']
    _total = (
        _es8_total['value']
        if _es8_total['relation'] == 'eq'
        else TROVE['ten-thousands-and-more']
    )
    _results = []
    for _es8_hit in es8_response['hits']['hits']:
        _card_iri = _es8_hit['_id']
        _results.append(SearchResult(
            card_iri=_card_iri,
            text_match_evidence=list(_gather_textmatch_evidence(_es8_hit)),
        ))
    return CardsearchResponse(
        total_result_count=_total,
        search_result_page=_results,
        related_propertysearch_set=(),
    )


def _gather_textmatch_evidence(es8_hit) -> Iterable[TextMatchEvidence]:
    for _innerhit_group in es8_hit['inner_hits'].values():
        for _innerhit in _innerhit_group['hits']['hits']:
            _property_path = tuple(
                json.loads(_innerhit['fields']['nested_text.path_from_focus'][0]),
            )
            try:
                _language_iri = _innerhit['fields']['nested_text.language_iri'][0]
            except KeyError:
                _language_iri = None
            for _highlight in _innerhit['highlight']['nested_text.text_value']:
                yield TextMatchEvidence(
                    property_path=_property_path,
                    matching_highlight=primitive_rdf.text(_highlight, language_iri=_language_iri),
                    card_iri=_innerhit['_id'],
                )


class _PredicatePathWalker:
    @dataclasses.dataclass(frozen=True)
    class PathKey:
        path_from_start: tuple[str]
        nearest_subject_iri: str
        path_from_nearest_subject: tuple[str]

        def step(self, subject_or_blanknode, predicate_iri):
            if isinstance(subject_or_blanknode, str):
                return self.__class__(
                    path_from_start=(*self.path_from_start, predicate_iri),
                    nearest_subject_iri=subject_or_blanknode,
                    path_from_nearest_subject=(predicate_iri,),
                )
            return self.__class__(
                path_from_start=(*self.path_from_start, predicate_iri),
                nearest_subject_iri=self.nearest_subject_iri,
                path_from_nearest_subject=(*self.path_from_nearest_subject, predicate_iri),
            )

        @property
        def last_predicate_iri(self):
            return self.path_from_start[-1]

        def as_nested_keywords(self):
            return {
                'path_from_focus': _property_path_as_keyword(self.path_from_start),
                'property_iri': self.last_predicate_iri,
                'nearest_subject_iri': self.nearest_subject_iri,
                'path_from_nearest_subject': _property_path_as_keyword(self.path_from_nearest_subject),
            }

    WalkYield = tuple[PathKey, primitive_rdf.RdfObject]

    def __init__(self, tripledict: primitive_rdf.RdfTripleDictionary):
        self.tripledict = tripledict
        self._visiting = set()

    def walk_from_subject(self, iri_or_blanknode, last_pathkey=None) -> Iterable[WalkYield]:
        '''walk the graph from the given subject, yielding (pathkey, obj) for every reachable object
        '''
        if last_pathkey is None:
            assert isinstance(iri_or_blanknode, str)
            last_pathkey = _PredicatePathWalker.PathKey(
                path_from_start=(),
                nearest_subject_iri=iri_or_blanknode,
                path_from_nearest_subject=(),
            )
        with self._visit(iri_or_blanknode):
            _twopledict = (
                primitive_rdf.twopleset_as_twopledict(iri_or_blanknode)
                if isinstance(iri_or_blanknode, frozenset)
                else self.tripledict.get(iri_or_blanknode, {})
            )
            for _predicate_iri, _obj_set in _twopledict.items():
                _pathkey = last_pathkey.step(iri_or_blanknode, _predicate_iri)
                for _obj in _obj_set:
                    if not isinstance(_obj, frozenset):  # omit the blanknode as a value
                        yield (_pathkey, _obj)
                    if isinstance(_obj, (str, frozenset)) and (_obj not in self._visiting):
                        # step further for iri or blanknode
                        yield from self.walk_from_subject(_obj, last_pathkey=_pathkey)

    @contextlib.contextmanager
    def _visit(self, focus_obj):
        assert focus_obj not in self._visiting
        self._visiting.add(focus_obj)
        yield
        self._visiting.discard(focus_obj)