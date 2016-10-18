import re
import logging
from lxml import etree

from share.normalize import ctx, tools
from share.normalize.parsers import Parser
from share.normalize.normalizer import Normalizer


logger = logging.getLogger(__name__)

THE_REGEX = re.compile(r'(^the\s|\sthe\s)')


class OAIAgent(Parser):
    ORGANIZATION_KEYWORDS = (
        THE_REGEX,
        'council',
        'center',
        'foundation'
    )
    INSTITUTION_KEYWORDS = (
        'school',
        'university',
        'institution',
        'college',
        'institute'
    )

    schema = tools.RunPython('agent_type', ctx)

    name = ctx

    def agent_type(self, name):
        """
        Returns a guess at the type of an agent based on its name.
        """
        if self.list_in_string(name, self.INSTITUTION_KEYWORDS):
            return 'institution'
        if self.list_in_string(name, self.ORGANIZATION_KEYWORDS):
            return 'organization'
        return 'person'

    def list_in_string(self, string, list_):
        for word in list_:
            if isinstance(word, str):
                if word in string.lower():
                    return True
            else:
                if word.search(string):
                    return True
        return False


class OAIAgentIdentifier(Parser):
    schema = 'AgentIdentifier'

    uri = tools.IRI(ctx).IRI


class OAIWorkIdentifier(Parser):
    schema = 'WorkIdentifier'

    uri = tools.IRI(ctx).IRI


class OAISubject(Parser):
    schema = 'Subject'

    name = ctx


class OAIThroughSubjects(Parser):
    schema = 'ThroughSubjects'

    subject = tools.Delegate(OAISubject, ctx)


class OAIAgentWorkRelation(Parser):
    schema = 'AgentWorkRelation'

    agent = tools.Delegate(OAIAgent, ctx)
    cited_name = ctx
    order_cited = ctx('index')


class OAITag(Parser):
    schema = 'Tag'

    name = ctx


class OAIThroughTags(Parser):
    schema = 'ThroughTags'

    tag = tools.Delegate(OAITag, ctx)


class OAIRelatedWork(Parser):
    schema = 'CreativeWork'

    identifiers = tools.Map(OAIWorkIdentifier, ctx)


class OAIWorkRelation(Parser):
    schema = 'WorkRelation'

    related = tools.Delegate(OAIRelatedWork, ctx)


class OAIIsDerivedFrom(OAIWorkRelation):
    schema = 'IsDerivedFrom'


class OAIContribution(Parser):
    schema = 'Contribution'

    agent = tools.Delegate(OAIAgent, ctx)


class OAIPublishingContribution(OAIContribution):
    schema = 'PublishingContribution'

    bibliographic = tools.Static(False)


class OAICreativeWork(Parser):
    default_type = None
    type_map = None

    @property
    def schema(self):
        try:
            resource_type = self.context['record']['metadata']['dc']['dc:type']
            return self.type_map[resource_type]
        except (KeyError, ValueError):
            return self.default_type

    title = tools.Join(tools.RunPython('force_text', tools.Try(ctx['record']['metadata']['dc']['dc:title'])))
    description = tools.Join(tools.RunPython('force_text', tools.Try(ctx.record.metadata.dc['dc:description'])))

    related_works = tools.Concat(
        tools.Map(tools.Delegate(OAIIsDerivedFrom), tools.Try(ctx['record']['metadata']['dc']['dc:source'])),
        tools.Map(tools.Delegate(OAIWorkRelation), tools.RunPython('get_relation', ctx))
    )

    related_agents = tools.Concat(
        tools.Map(
            tools.Delegate(OAIContribution),
            tools.Try(ctx['record']['metadata']['dc']['dc:creator'])
        ),
        tools.Map(
            tools.Delegate(OAIContribution.using(bibliographic=tools.Static(False))),
            tools.Try(ctx['record']['metadata']['dc']['dc:contributor'])
        ),
        tools.Try(tools.Delegate(OAIPublishingContribution, tools.RunPython('force_text', ctx.record.metadata.dc['dc:publisher'])))

    )

    rights = tools.Join(tools.Maybe(tools.Maybe(ctx['record'], 'metadata')['dc'], 'dc:rights'))

    # Note: this is only taking the first language in the case of multiple languages
    language = tools.ParseLanguage(
        tools.Try(ctx['record']['metadata']['dc']['dc:language'][0]),
    )

    subjects = tools.Map(
        tools.Delegate(OAIThroughSubjects),
        tools.Subjects(
            tools.Map(
                tools.RunPython('tokenize'),
                tools.Try(ctx['record']['header']['setSpec']),
                tools.Try(ctx['record']['metadata']['dc']['dc:type']),
                tools.Try(ctx['record']['metadata']['dc']['dc:format']),
                tools.Try(ctx['record']['metadata']['dc']['dc:subject']),
            )
        )
    )

    tags = tools.Map(
        tools.Delegate(OAIThroughTags),
        tools.RunPython(
            'force_text',
            tools.Concat(
                tools.Try(ctx['record']['header']['setSpec']),
                tools.Try(ctx['record']['metadata']['dc']['dc:type']),
                tools.Try(ctx['record']['metadata']['dc']['dc:format']),
                tools.Try(ctx['record']['metadata']['dc']['dc:subject']),
            )
        )
    )

    date_updated = tools.ParseDate(ctx['record']['header']['datestamp'])

    class Extra:
        """
        Fields that are combined in the base parser are relisted as singular elements that match
        their original entry to preserve raw data structure.
        """
        # An agent responsible for making contributions to the resource.
        contributor = tools.Maybe(tools.Maybe(ctx['record'], 'metadata')['dc'], 'dc:contributor')

        # The spatial or temporal topic of the resource, the spatial applicability of the resource,
        # or the jurisdiction under which the resource is relevant.
        coverage = tools.Maybe(tools.Maybe(ctx['record'], 'metadata')['dc'], 'dc:coverage')

        # An agent primarily responsible for making the resource.
        creator = tools.Maybe(tools.Maybe(ctx['record'], 'metadata')['dc'], 'dc:creator')

        # A point or period of time associated with an event in the lifecycle of the resource.
        dates = tools.Maybe(tools.Maybe(ctx['record'], 'metadata')['dc'], 'dc:date')

        # The file format, physical medium, or dimensions of the resource.
        resource_format = tools.Maybe(tools.Maybe(ctx['record'], 'metadata')['dc'], 'dc:format')

        # An unambiguous reference to the resource within a given context.
        identifiers = tools.Concat(
            tools.Try(ctx['record']['metadata']['dc']['dc:identifier']),
            tools.Maybe(ctx['record']['header'], 'identifier')
        )

        # A related resource.
        relation = tools.RunPython('get_relation', ctx)

        # A related resource from which the described resource is derived.
        source = tools.Maybe(tools.Maybe(ctx['record'], 'metadata')['dc'], 'dc:source')

        # The nature or genre of the resource.
        resource_type = tools.Try(ctx.record.metadata.dc['dc:type'])

        set_spec = tools.Maybe(ctx.record.header, 'setSpec')

        # Language also stored in the Extra class in case the language reported cannot be parsed by ParseLanguage
        language = tools.Try(ctx.record.metadata.dc['dc:language'])

        # Status in the header, will exist if the resource is deleted
        status = tools.Maybe(ctx.record.header, '@status')

    def force_text(self, data):
        if isinstance(data, dict):
            return data['#text']

        if isinstance(data, str):
            return data

        fixed = []
        for datum in (data or []):
            if datum is None:
                continue
            if isinstance(datum, dict):
                if '#text' not in datum:
                    logger.warn('Skipping %s, no #text key exists', datum)
                    continue
                fixed.append(datum['#text'])
            elif isinstance(datum, str):
                fixed.append(datum)
            else:
                raise Exception(datum)
        return fixed

    def tokenize(self, data):
        tokens = []
        for item in data:
            tokens.extend([x.strip() for x in re.split('(?: - )|\.', data) if x])
        return tokens

    def get_relation(self, ctx):
        if not ctx['record'].get('metadata'):
            return []
        relation = ctx['record']['metadata']['dc'].get('dc:relation', [])
        if isinstance(relation, dict):
            return relation['#text']
        return relation


class OAINormalizer(Normalizer):

    @property
    def root_parser(self):
        parser = OAICreativeWork
        parser.default_type = self.config.emitted_type.lower()
        parser.type_map = self.config.type_map

        if self.config.property_list:
            logger.debug('Attaching addition properties %s to normalizer for %s'.format(self.config.property_list, self.config.label))
            for prop in self.config.property_list:
                if prop in parser._extra:
                    logger.warning('Skipping property %s, it already exists', prop)
                    continue
                parser._extra[prop] = tools.Try(ctx.record.metadata.dc['dc:' + prop]).chain()[0]

        return parser

    def do_normalize(self, data):
        if self.config.approved_sets is not None:
            specs = set(x.replace('publication:', '') for x in etree.fromstring(data).xpath(
                'ns0:header/ns0:setSpec/node()',
                namespaces={'ns0': 'http://www.openarchives.org/OAI/2.0/'}
            ))
            if not (specs & set(self.config.approved_sets)):
                logger.warning('Series %s not found in approved_sets for %s', specs, self.config.label)
                return None

        return super().do_normalize(data)
