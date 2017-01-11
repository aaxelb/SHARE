import logging
import pendulum

from django.db.models import Q, DateTimeField
from django.core.exceptions import ValidationError

from share.util import DictHashingDict, IDObfuscator, InvalidID

__all__ = ('GraphDisambiguator', )

logger = logging.getLogger(__name__)


class GraphDisambiguator:
    def prune(self, change_graph):
        # For each node in the graph, compare to each other node and remove duplicates.
        # Compare based on type (one is a subclass of the other), attrs (exact matches), and relations.
        self._disambiguate(change_graph, SelfPruningGraph(change_graph))
        return change_graph

    def merge(self, base_graph, change_graph):
        merging_graph = MergingGraph(base_graph)
        self._disambiguate(change_graph, merging_graph)
        merging_graph.finish()
        return base_graph

    def find_instances(self, change_graph):
        # For each node in the graph, look for a matching instance in the database.
        self._disambiguate(change_graph, CompareDatabaseGraph())
        return change_graph

    def _disambiguate(self, change_graph, compare_graph):
        changed = True
        while changed:
            changed = False
            # Sort by type and id as well to get consistent sorting
            nodes = sorted(change_graph.nodes, key=lambda x: (self._disambiguweight(x), x.type, x.id), reverse=True)
            compare_graph.reset()
            for n in tuple(nodes):
                if compare_graph.match(n):
                    changed = True

    def _disambiguweight(self, node):
        # Models with exactly 1 foreign key field (excluding those added by
        # ShareObjectMeta) are disambiguated first, because they might be used
        # to uniquely identify the object they point to. Then do the models with
        # 0 FKs, then 2, 3, etc.
        ignored = {'same_as', 'extra'}
        fk_count = sum(1 for f in node.model._meta.get_fields() if f.editable and (f.many_to_one or f.one_to_one) and f.name not in ignored)
        return fk_count if fk_count == 1 else -fk_count


class CompareChangeGraph:
    def __init__(self, change_graph):
        self._graph = change_graph
        self._index = self.NodeIndex()

    def reset(self):
        pass

    def match(self, node):
        matches = self._index[node]
        if not matches:
            return self._handle_miss(node)
        if len(matches) > 1:
            # TODO?
            raise NotImplementedError('Multiple matches while merging change graphs.\nNode: {}\nMatches: {}'.format(node, matches))
        return self._handle_hit(node, matches.pop())

    def _handle_hit(self, node, match):
        raise NotImplementedError()

    def _handle_miss(self, node):
        raise NotImplementedError()

    def _merge_nodes(self, source, replacement):
        assert source.graph is self._graph
        assert replacement.graph is self._graph

        for k, v in source.attrs.items():
            if k in replacement.attrs:
                old_val = replacement.attrs[k]
                if v == old_val:
                    continue
                field = replacement.model._meta.get_field(k)
                if isinstance(field, DateTimeField):
                    new_val = max(pendulum.parse(v), pendulum.parse(old_val)).isoformat()
                else:
                    # use the longer value, or the first alphabetically if they're the same length
                    new_val = sorted([v, old_val], key=lambda x: (-len(str(x)), x))[0]
            else:
                new_val = source.attrs[k]
            replacement.attrs[k] = new_val

        from share.models import Person
        if replacement.model == Person:
            replacement.attrs['name'] = ''
            Person.normalize(replacement, replacement.graph)

        self._graph.replace(source, replacement)

    class NodeIndex:
        def __init__(self, nodes=None):
            self._index = {}
            self._info_cache = {}
            if nodes:
                self.rebuild(nodes)

        def rebuild(self, nodes):
            self.clear()
            for n in nodes:
                self.add(n)

        def clear(self):
            self._index.clear()
            self._info_cache.clear()

        def add(self, node):
            info = self._get_info(node)
            by_model = self._index.setdefault(info.model._meta.concrete_model, DictHashingDict())
            if info.any:
                all_cache = by_model.setdefault(info.all, DictHashingDict())
                for item in info.any:
                    all_cache.setdefault(item, []).append(node)
            elif info.all:
                by_model.setdefault(info.all, []).append(node)
            else:
                logger.debug('Nothing to disambiguate on. Ignoring node {}'.format(node))

        def remove(self, node):
            info = self._get_info(node)
            try:
                all_cache = self._index[info.model._meta.concrete_model][info.all]
                if info.any:
                    for item in info.any:
                        all_cache[item].remove(node)
                else:
                    all_cache.remove(node)
                self._info_cache.pop(node)
            except (KeyError, ValueError) as ex:
                raise ValueError('Could not remove node from cache: Node {} not found!'.format(node)) from ex

        def __getitem__(self, node):
            info = self._get_info(node)
            matches = set()
            try:
                matches_all = self._index[info.model._meta.concrete_model][info.all]
                if info.any:
                    for item in info.any:
                        matches.update(matches_all.get(item, []))
                elif info.all:
                    matches.update(matches_all)
                # TODO use `info.tie_breaker` when there are multiple matches
                if info.matching_types:
                    return [m for m in matches if m != node and m.model._meta.label_lower in info.matching_types]
                else:
                    return [m for m in matches if m != node]
            except KeyError:
                return []

        def _get_info(self, node):
            try:
                return self._info_cache[node]
            except KeyError:
                info = DisambiguationInfo(node)
                self._info_cache[node] = info
                return info


class MergingGraph(CompareChangeGraph):
    def __init__(self, change_graph):
        super().__init__(change_graph)
        self._index.rebuild(self._graph.nodes)
        self._merged = {}
        self._unmerged = set()

    def match(self, node):
        if node in self._merged:
            return False
        return super().match(node)

    def finish(self):
        for n in self._unmerged:
            merged = self._graph.create(n.id, n.type, n.attrs)
            self._merged[n] = merged

        # TODO allow removing relations, somehow
        for n, m in self._merged.items():
            for edge in n.related(backward=False):
                self._graph.relate(m, self._merged[edge.related], edge._hint)

    def _handle_hit(self, node, match):
        # TODO preserve node namespace... allow heterogeneous ChangeGraph
        merged_node = self._graph.create(node.id, node.type, node.attrs)
        # TODO attrs from more trusted sources should always win
        self._merge_nodes(match, merged_node)

        self._merged[node] = merged_node
        self._unmerged.discard(node)

        # TODO update only the affected parts of the index instead of rebuilding
        self._index.rebuild(self._graph.nodes)

    def _handle_miss(self, node):
        self._unmerged.add(node)
        return False


class SelfPruningGraph(CompareChangeGraph):
    def reset(self):
        self._index.clear()

    def _handle_hit(self, node, match):
        # remove duplicates within the graph
        if node.model != match.model and issubclass(node.model, match.model):
            # remove the node with the less-specific class
            logger.debug('Found duplicate! Keeping {}, pruning {}'.format(node, match))
            self._index.remove(match)
            self._merge_nodes(match, node)
            self._index.add(node)
        else:
            logger.debug('Found duplicate! Keeping {}, pruning {}'.format(match, node))
            self._merge_nodes(node, match)
        return True

    def _handle_miss(self, node):
        self._index.add(node)
        return False


class CompareDatabaseGraph:
    def reset(self):
        pass

    def match(self, node):
        if node.instance:
            # Already matched, no change
            return False

        # look for matches in the database
        instance = self._instance_for_node(node)
        # if instance and isinstance(instance, list):
        #     same_type = [i for i in instance if isinstance(i, n.model)]
        #     if not same_type:
        #         logger.error('Found multiple matches for %s, and none were of type %s: %s', n, n.model, instance)
        #         raise NotImplementedError('Multiple matches found', n, instance)
        #     elif len(same_type) > 1:
        #         logger.error('Found multiple matches of type %s for %s: %s', n.model, n, same_type)
        #         raise NotImplementedError('Multiple matches found', n, same_type)
        #     logger.warning('Found multiple matches for %s, but only one of type %s, fortunately.', n, n.model)
        #     instance = same_type.pop()

        # TODO: what happens when two (apparently) non-duplicate nodes disambiguate to the same instance?
        if instance:
            node.instance = instance
            logger.debug('Disambiguated %s to %s', node, instance)
            return True
        if node.type == 'subject':
            raise ValidationError('Invalid subject: "{}"'.format(node.attrs.get('name')))
        return False

    def _instance_for_node(self, node):
        info = DisambiguationInfo(node)
        if not info.all and not info.any:
            return None

        all_query = Q()
        for k, v in info.all:
            k, v = self._query_pair(k, v, info)
            if k and v:
                all_query &= Q(**{k: v})
            else:
                return None

        queries = []
        for k, v in info.any:
            k, v = self._query_pair(k, v, info)
            if k and v:
                queries.append(all_query & Q(**{k: v}))

        if (info.all and not all_query.children) or (info.any and not queries):
            return None

        if info.matching_types:
            all_query &= Q(type__in=info.matching_types)

        constrain = [Q()]
        if hasattr(info.model, '_typedmodels_type'):
            constrain.append(Q(type__in=info.model.get_types()))
            constrain.append(Q(type=info.model._typedmodels_type))

        concrete_model = info.model._meta.concrete_model
        for q in constrain:
            sql, params = zip(*[concrete_model.objects.filter(all_query & query & q).query.sql_with_params() for query in queries or [Q()]])
            found = list(concrete_model.objects.raw(' UNION '.join('({})'.format(s) for s in sql) + ' LIMIT 2;', sum(params, ())))

            if not found:
                logger.debug('No %ss found for %s %s', concrete_model, all_query & q, queries)
                return None
            if len(found) == 1:
                return found[0]
            if all_query.children:
                logger.warning('Multiple %ss returned for %s (The main query) bailing', concrete_model, all_query)
                break
            if all('__' in str(query) for query in queries):
                logger.warning('Multiple %ss returned for %s (The any query) bailing', concrete_model, queries)
                break

        logger.error('Could not disambiguate %s. Too many results found from %s %s', info.model, all_query, queries)
        raise NotImplementedError('Multiple {0}s found'.format(info.model))

    def _query_pair(self, key, value, info):
        field = info._node.model._meta.get_field(key)
        if field.is_relation:
            try:
                return ('{}__id'.format(key), IDObfuscator.decode_id(value))
            except InvalidID:
                return (None, None)
        return (key, value)


class DisambiguationInfo:
    def __init__(self, node):
        self._node = node
        self.model = node.model
        self.all = self._all()
        self.any = self._any()
        self.matching_types = self._matching_types()

    def _all(self):
        try:
            all = self.model.Disambiguation.all
        except AttributeError:
            return ()
        values = tuple((f, v) for f in all for v in self._field_values(f))
        assert len(values) == len(all)
        return values

    def _any(self):
        try:
            any = self.model.Disambiguation.any
        except AttributeError:
            return ()
        return tuple((f, v) for f in any for v in self._field_values(f))

    def _matching_types(self):
        try:
            constrain_types = self.model.Disambiguation.constrain_types
        except AttributeError:
            constrain_types = False
        if not constrain_types:
            return None

        # list of all subclasses and superclasses of node.model that could be the type of a node
        concrete_model = self.model._meta.concrete_model
        if concrete_model is self.model:
            type_names = [self.model._meta.label_lower]
        else:
            subclasses = self.model.get_types()
            superclasses = [m._meta.label_lower for m in self.model.__mro__ if issubclass(m, concrete_model) and m._meta.proxy]
            type_names = subclasses + superclasses
        return set(type_names)

    def _field_values(self, field_name):
        field = self.model._meta.get_field(field_name)
        if field.is_relation:
            if field.one_to_many:
                for edge in self._node.related(name=field_name, forward=False):
                    yield edge.subject.id
            elif field.many_to_one:
                yield self._node.related(name=field_name, backward=False).related.id
            elif field.many_to_many:
                # TODO?
                raise NotImplementedError()
        else:
            if field_name in self._node.attrs:
                value = self._node.attrs[field.name]
                if value != '':
                    yield value
