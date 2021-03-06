import re
import uuid
import logging
from functools import reduce

from django.core.exceptions import FieldDoesNotExist

from share.schema import ShareV2Schema
from share.schema.shapes import RelationShape
from share.transform.chain.exceptions import ChainError
from share.transform.chain.links import Context
from share.transform.chain.links import AbstractLink


# NOTE: Context is a thread local singleton
# It is asigned to ctx here just to keep a family interface
ctx = Context()
logger = logging.getLogger(__name__)


class ParserMeta(type):

    def __new__(cls, name, bases, attrs):
        # Enabled inheritance in parsers.
        parsers = reduce(lambda acc, val: {**acc, **getattr(val, 'parsers', {})}, bases[::-1], {})
        for key, value in tuple(attrs.items()):
            if isinstance(value, AbstractLink) and key != 'schema':
                parsers[key] = attrs.pop(key).chain()[0]
        attrs['parsers'] = parsers

        attrs['_extra'] = reduce(lambda acc, val: {**acc, **getattr(val, '_extra', {})}, bases[::-1], {})
        attrs['_extra'].update({
            key: value.chain()[0]
            for key, value
            in attrs.pop('Extra', object).__dict__.items()
            if isinstance(value, AbstractLink)
        })

        return super(ParserMeta, cls).__new__(cls, name, bases, attrs)


class Parser(metaclass=ParserMeta):

    @classmethod
    def using(cls, **overrides):
        if not all(isinstance(x, AbstractLink) for x in overrides.values()):
            raise Exception('Found non-link values in {}. Maybe you need to wrap something in Delegate?'.format(overrides))
        return type(
            cls.__name__ + 'Overridden',
            (cls, ), {
                'schema': cls.schema if isinstance(cls.schema, (str, AbstractLink)) else cls.__name__.lower(),
                **overrides
            }
        )

    @property
    def schema(self):
        return self.__class__.__name__.lower()

    def __init__(self, context, config=None):
        self.config = config or ctx._config
        self.context = context
        self.id = '_:' + uuid.uuid4().hex

    def validate(self, field, value):
        if field.is_relation:
            if field.relation_shape in (RelationShape.ONE_TO_MANY, RelationShape.MANY_TO_MANY):
                assert isinstance(value, (list, tuple)), 'Values for field {} must be lists. Found {}'.format(field, value)
            else:
                assert isinstance(value, dict) and '@id' in value and '@type' in value, 'Values for field {} must be a dictionary with keys @id and @type. Found {}'.format(field, value)
        else:
            assert not isinstance(value, dict), 'Value for non-relational field {} must be a primitive type. Found {}'.format(field, value)

    def parse(self):
        Context().parsers.append(self)
        try:
            return self._do_parse()
        except ChainError as e:
            e.push(repr(self.__class__))
            raise e
        finally:
            Context().parsers.pop(-1)

    def _do_parse(self):
        if isinstance(self.schema, AbstractLink):
            schema = self.schema.chain()[0].run(self.context).lower()
        else:
            schema = self.schema

        schema_type = ShareV2Schema().get_type(schema)
        self.ref = {'@id': self.id, '@type': schema}

        inst = {**self.ref}  # Shorthand for copying ref

        for key, chain in self.parsers.items():
            try:
                field = ShareV2Schema().get_field(schema_type.name, key)
            except FieldDoesNotExist:
                raise Exception('Tried to parse value {} which does not exist on {}'.format(key, schema_type))

            try:
                value = chain.run(self.context)
            except ChainError as e:
                e.push('{}.{}'.format(self.__class__.__name__, key))
                raise e

            if (
                value
                and field.is_relation
                and field.relation_shape in (RelationShape.ONE_TO_MANY, RelationShape.MANY_TO_MANY)
            ):
                if field.relation_shape == RelationShape.ONE_TO_MANY:
                    field_to_set = field.inverse_relation
                else:
                    field_to_set = field.incoming_through_relation

                for v in tuple(value):  # Freeze list so we can modify it will iterating
                    # Allow filling out either side of recursive relations
                    if schema_type.concrete_type == field.related_concrete_type and field.name in ctx.pool[v]:
                        ctx.pool[v][field_to_set] = self.ref
                        value.remove(v)  # Prevent CyclicalDependency error. Only "subjects" should have related_works
                    else:
                        ctx.pool[v][field_to_set] = self.ref

            if value is not None:
                self.validate(field, value)
                inst[key] = self._normalize_white_space(value)

        inst['extra'] = {}
        for key, chain in self._extra.items():
            val = chain.run(self.context)
            if val:
                inst['extra'][key] = val
        if not inst['extra']:
            del inst['extra']

        ctx.pool[self.ref] = inst
        ctx.graph.append(inst)

        # Return only a reference to the parsed object to avoid circular data structures
        return self.ref

    def _normalize_white_space(self, value):
        if not isinstance(value, str):
            return value
        return re.sub(r'\s+', ' ', value.strip())
