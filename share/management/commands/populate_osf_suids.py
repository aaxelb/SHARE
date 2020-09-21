import re

from share.management.commands import BaseShareCommand
from share.models import NormalizedData, RawDatum, ShareUser, SourceUniqueIdentifier
from share.util.graph import MutableGraph
from share.util.osf import osf_sources


OSF_GUID_RE = re.compile(r'^https?://(?:[^.]+.)?osf.io/(?P<guid>[^/]+)/?$')


def get_guid(uri):
    match = OSF_GUID_RE.match(uri)
    return match.group('guid') if match else None


def get_central_work(graph):
    work_nodes = graph.filter_by_concrete_type('abstractcreativework')
    if not work_nodes:
        return None

    # get the work node with the most attrs
    work_nodes.sort(key=lambda n: len(n.attrs()), reverse=True)
    return work_nodes[0]


def update_suid(normalized_datum, new_suid_identifier):
    raw_datum = normalized_datum.raw
    existing_suid = raw_datum.suid
    new_suid, created = SourceUniqueIdentifier.objects.get_or_create(
        identifier=new_suid_identifier,
        source_config=existing_suid.source_config,
    )

    if new_suid == existing_suid:
        print(f'skipping {normalized_datum}, already has correct suid {existing_suid}')
        return

    # RawDatum is unique on (suid, sha256), so there will be 0 or 1 duplicates
    duplicate_raw = RawDatum.objects.filter(suid=new_suid, sha256=raw_datum.sha256).first()

    if duplicate_raw:
        if duplicate_raw == raw_datum:
            raise Exception(f'wtf the duplicate is the same one ({raw_datum}, {duplicate_raw})')
        print(f'handling dupe! updating {normalized_datum} raw from {raw_datum} to {duplicate_raw}')
        normalized_datum.raw = duplicate_raw
        normalized_datum.save()
        raw_datum.delete()
    else:
        print(f'updating {raw_datum} suid from {existing_suid} to {new_suid}')
        raw_datum.suid = new_suid
        raw_datum.save()
    print(f'deleting {existing_suid}')
    existing_suid.delete()


class Command(BaseShareCommand):
    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true', help='Should the script actually commit?')

    def handle(self, *args, **options):
        nd_qs = NormalizedData.objects.filter(
            source__in=ShareUser.objects.filter(source__in=osf_sources())
        )[:50]

        # TODO chunk, or allow stopping partway through
        with self.rollback_unless_commit(commit=options.get('commit')):
            for nd in nd_qs:
                graph = MutableGraph.from_jsonld(nd.data)
                central_work = get_central_work(graph)
                osf_guids = list(filter(bool, (
                    get_guid(identifier['uri'])
                    for identifier in central_work['identifiers']
                )))
                # print(f'osf guids for {nd}: {osf_guids}')
                if len(osf_guids) == 1:
                    update_suid(nd, osf_guids[0])
