import contextlib

from django.db.models import F
import gather

from share.search.index_strategy.elastic8 import Elastic8IndexStrategy
from share.search import messages
from share.search.search_request import (
    CardsearchParams,
    PropertysearchParams,
    ValuesearchParams,
)
from share.search.search_response import (
    CardsearchResponse,
    PropertysearchResponse,
    ValuesearchResponse,
)
from share.util.checksum_iri import ChecksumIri
from trove import models as trove_db


PROPERTYPATH_DELIMITER = '||'


class TroveIrisIndexStrategy(Elastic8IndexStrategy):
    CURRENT_STRATEGY_CHECKSUM = ChecksumIri(
        checksumalgorithm_name='sha-256',
        salt='TroveIrisIndexStrategy',
        hexdigest='6ab4a7e1b060aedc2f218c6800f16886da1364c5768d881d1337cd3ee8af5351',
    )

    @property
    def supported_message_types(self):
        return {
            messages.MessageType.INDEX_SUID,
            messages.MessageType.BACKFILL_SUID,
        }

    def index_settings(self):
        return {}

    def index_mappings(self):
        return {
            'dynamic': 'false',
            'properties': {
                'focus_iri': {
                    'type': 'keyword',
                },
                'focustype_iri': {
                    'type': 'keyword',
                },
                # 'included_predicate_iri': {
                #     'type': 'keyword',
                # },
                # 'included_resource_iri': {
                #     'type': 'keyword',
                # },
                # 'included_vocab_iri': {
                #     'type': 'keyword',
                # },
                'iri_property_value': {
                    'type': 'nested',
                    'dynamic': 'strict',
                    'properties': {
                        'property_path': {
                            'type': 'keyword',
                        },
                        'iri_value_set': {
                            'type': 'keyword',
                        },
                    },
                },
                'text_property_value': {
                    'type': 'nested',
                    'dynamic': 'strict',
                    'properties': {
                        'property_path': {
                            'type': 'keyword',
                        },
                        'language_iri': {
                            'type': 'keyword',
                        },
                        'text_value': {
                            'type': 'text',
                            'index_options': 'offsets',  # for faster highlighting
                            'index_prefixes': {
                                'min_chars': 3,
                                'max_chars': 10,
                            },
                        },
                    },
                },
            }
        }

    def _build_sourcedoc(self, indexcard):
        _tripledict = indexcard.as_rdf_tripledict()
        _iri_propertypath_values = {}
        _text_propertypath_values = {}
        for _property_path, _obj in _PropertyPathWalker(_tripledict).from_focus(indexcard.focus_iri):
            if isinstance(_obj, str):
                _iri_propertypath_values.setdefault(_property_path, set()).add(_obj)
            elif isinstance(_obj, gather.Text):
                _text_propertypath_values.setdefault(_property_path, set()).add(_obj)
        return {
            'focus_iri': [
                _piri.as_iri()
                for _piri in indexcard.focus_piri_set.all()
            ],
            'focustype_iri': [
                _piri.as_iri()
                for _piri in indexcard.focustype_piri_set.all()
            ],
            'iri_property_value': [
                {
                    'property_path': _propertypath,
                    'iri_value': list(_value_set),
                }
                for _propertypath, _value_set in _iri_propertypath_values.items()
            ],
            'text_property_value': [
                {
                    'property_path': _propertypath,
                    'language_iri': _value.language_iri,
                    'text_value': _value.unicode_text,
                }
                for _propertypath, _value_set in _text_propertypath_values.items()
                for _value in _value_set
            ],
        }

    def build_elastic_actions(self, messages_chunk: messages.MessagesChunk):
        _indexcard_qs = (
            trove_db.RdfIndexcard.objects
            .filter(from_raw_datum__suid_id__in=messages_chunk.target_ids_chunk)
            .annotate(_suid_id=F('from_raw_datum__suid_id'))
        )
        _remaining_suid_ids = set(messages_chunk.target_ids_chunk)
        for _indexcard in _indexcard_qs:
            _remaining_suid_ids.pop(_indexcard._suid_id)
            yield self.build_index_action(_indexcard._suid_id, self._build_sourcedoc(_indexcard))
        # delete any that don't have the expected card
        for _leftover_suid_id in _remaining_suid_ids:
            yield self.build_delete_action(_leftover_suid_id)

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
            raise NotImplementedError

        def pls_handle_propertysearch(self, propertysearch_params: PropertysearchParams) -> PropertysearchResponse:
            raise NotImplementedError

        def pls_handle_valuesearch(self, valuesearch_params: ValuesearchParams) -> ValuesearchResponse:
            raise NotImplementedError


###
# local utils

def _property_path_as_keyword(property_path) -> str:
    return PROPERTYPATH_DELIMITER.join(property_path)


class _PropertyPathWalker:
    def __init__(self, tripledict: gather.RdfTripleDictionary):
        self.tripledict = tripledict
        self._visiting = set()
        self._path_so_far = []

    def from_focus(self, focus_iri: str):
        with self._visit(focus_iri):
            _focus_twopledict = self.tripledict.get(focus_iri, {})
            yield from self._walk_twopledict(_focus_twopledict)

    @contextlib.contextmanager
    def _pathstep(self, predicate_iri):
        self._path_so_far.append(predicate_iri)
        yield _property_path_as_keyword(self._path_so_far)
        self._path_so_far.pop(predicate_iri)

    @contextlib.contextmanager
    def _visit(self, focus_obj):
        assert focus_obj not in self._visiting
        self._visiting.add(focus_obj)
        yield
        self._visiting.discard(focus_obj)

    def _walk_twopledict(self, focus_twopledict: gather.RdfTwopleDictionary):
        for _predicate_iri, _obj_set in focus_twopledict.items():
            with self._pathstep(_predicate_iri) as _pathkey:
                for _obj in _obj_set:
                    if isinstance(_obj, gather.Text):
                        yield (_pathkey, _obj)
                        _next_twopledict = None
                    elif isinstance(_obj, str):  # IRI
                        yield (_pathkey, _obj)
                        _next_twopledict = (
                            None
                            if _obj in self._visiting
                            else self.tripledict.get(_obj)
                        )
                    elif isinstance(_obj, frozenset):
                        _next_twopledict = gather.twopleset_as_twopledict(_obj)
                    else:
                        continue
                    if _next_twopledict and (_obj not in self._visiting):
                        with self._visit(_obj):
                            yield from self._walk_twopledict(_next_twopledict)
