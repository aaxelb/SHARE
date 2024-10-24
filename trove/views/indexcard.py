from django.views import View
from primitive_metadata import gather

from trove.render import get_renderer
from trove.trovesearch_gathering import trovesearch_by_indexstrategy
from trove.vocab.jsonapi import JSONAPI_MEDIATYPE
from trove.vocab.trove import TROVE, trove_indexcard_iri


class IndexcardView(View):
    def get(self, request, indexcard_uuid):
        _renderer = get_renderer(request)
        _search_gathering = trovesearch_by_indexstrategy.new_gathering({
            # TODO (gather): allow omitting kwargs that go unused
            'search_params': None,
            'specific_index': None,
            'use_osfmap_json': (_renderer.MEDIATYPE in {'application/json', JSONAPI_MEDIATYPE})
        })
        _indexcard_iri = trove_indexcard_iri(indexcard_uuid)
        _search_gathering.ask(
            {},  # TODO: build from `include`/`fields`
            focus=gather.focus(_indexcard_iri, TROVE.Indexcard),
        )
        _response_tripledict = _search_gathering.leaf_a_record()
        return _renderer.render_response(_response_tripledict, _indexcard_iri)
