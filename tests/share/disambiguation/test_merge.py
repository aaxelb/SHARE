import pytest

from share.change import ChangeGraph
from share.disambiguation import GraphDisambiguator
from tests.share.normalize.factories import *


class TestMergeChangeGraph:
    @pytest.mark.parametrize('inputs, output', [
        ([
            [
                Preprint(0, identifiers=[
                    WorkIdentifier(id='id1', uri='http://osf.io/blahblah')
                ], related_works=[
                    CreativeWork(id='article_blah', sparse=True, identifiers=[WorkIdentifier(uri='http://osf.io/guidguid')])
                ]),
            ], [
                Article(1, id='article', identifiers=[WorkIdentifier(id='id2', uri='http://osf.io/guidguid')])
            ]
        ], [
            Preprint(0, identifiers=[
                WorkIdentifier(id='id1', uri='http://osf.io/blahblah')
            ], related_works=[
                Article(1, id='article', identifiers=[WorkIdentifier(id='id2', uri='http://osf.io/guidguid')])
            ])
        ]),
        ([
            [
                Preprint(0, identifiers=[
                    WorkIdentifier(id='id1', uri='http://osf.io/blahblah')
                ], related_works=[
                    CreativeWork(id='secret_article', sparse=True, identifiers=[WorkIdentifier(uri='http://osf.io/guidguid')])
                ]),
            ], [
                Article(1, id='article', identifiers=[
                    WorkIdentifier(id='id2', uri='http://osf.io/guidguid')
                ], related_agents=[
                    Person(2)
                ])
            ]
        ], [
            Preprint(0, identifiers=[
                WorkIdentifier(id='id1', uri='http://osf.io/blahblah')
            ], related_works=[
                Article(1, id='article', identifiers=[
                    WorkIdentifier(id='id2', uri='http://osf.io/guidguid')
                ], related_agents=[
                    Person(2)
                ])
            ])
        ]),
    ])
    def test_merge_change_graphs(self, Graph, inputs, output):
        first, *graphs = [ChangeGraph(Graph(*input)) for input in inputs]
        for g in graphs:
            first.merge(g)
        result = [n.serialize() for n in sorted(first.nodes, key=lambda x: x.type + str(x.id))]
        assert result == Graph(*output)
