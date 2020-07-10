import argparse
import json
import os
import psycopg2
import tarfile

# connect to db
# cursor on share_normalizeddata
# for each jsonld datum:
#   strip out nodes with `@type='agentidentifier'` and `scheme='mailto'`
#   write to a file
#   add filename to set
# tar all files in set


def is_email_node(jsonld_node):
    """filter function for nodes in NormalizedData.data

    @jsonld_node: dictionary like `{ '@id': '_:123', '@type': 'agentidentifier', ... }`

    returns boolean
    """
    node_type = jsonld_node.get('@type', '').lower()
    node_scheme = jsonld_node.get('scheme', '').lower()
    return (node_type == 'agentidentifier' and node_scheme == 'mailto')


def get_cleaned_datum(jsonld_graph):
    """remove emails so this can be better shared publicly.

    @jsonld_graph: dictionary like `{ '@graph': [ { ... }, { ... }, ... ] }`
        from NormalizedData.data field

    returns a similar dictionary, with a subset of jsonld nodes
    """
    nodes = jsonld_graph['@graph']
    filtered_nodes = [n for n in nodes if not is_email_node(n)]
    return {**jsonld_graph, '@graph': filtered_nodes}


def write_datums_to_files(output_directory, datums_iterator, stop_after=None):
    """clean and write datums according to their source

    @output_directory: string/path-like
    @datums_iterator: iterator of (datum_id, source_name, datum_jsonld) pairs
    @stop_after: integer or None, max number of datums to load/write
    """
    written_files = set()
    for datum_id, source_name, datum_jsonld, datum_created_at in datums_iterator:
        cleaned_datum = get_cleaned_datum(datum_jsonld)

        file_name = f'{datum_created_at.date().isoformat()}__{datum_id}.json'
        file_path = os.path.join(output_directory, source_name, file_name)
        print(f'writing datum {datum_id} to path {file_path}')

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as file:
            json.dump(cleaned_datum, file)
        written_files.add(file_path)
    return written_files


normalized_data_query = '''
SELECT nd.id,
    u.username,
    nd.data,
    nd.created_at
FROM share_normalizeddata nd
JOIN share_shareuser u ON nd.source_id = u.id
WHERE nd.id >= %(start_id)s
ORDER BY nd.id ASC
LIMIT %(num_records)s
'''


def dump_normalized_data(output_directory, start_id, num_records):
    connection = psycopg2.connect(host='localhost', dbname='share', user='postgres')  # TODO how work
    with connection:
        with connection.cursor('dump_normalized_data') as cursor:
            cursor.execute(normalized_data_query, {
                'start_id': start_id,
                'num_records': num_records,
            })
            write_datums_to_files(output_directory, cursor)


def make_directory_tarball(directory):
    tarfile_name = f'{directory}.tar'
    print(f'dumping all NormalizedData to {tarfile_name} ...')
    with tarfile.open(tarfile_name, 'w') as tf:  # TODO compression?
        tf.add(directory)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dump all normalized data')
    parser.add_argument('output_directory', type=str)
    parser.add_argument('-s', '--start-id', type=int, default=0)
    parser.add_argument('-n', '--num-records', type=int, default=50000)
    parser.add_argument('-t', '--tar', action='store_true')
    args = parser.parse_args()

    dump_normalized_data(args.output_directory, args.start_id, args.num_records)
    if args.tar:
        make_directory_tarball(args.output_directory)
