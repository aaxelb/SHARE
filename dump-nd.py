import argparse
import os
import psycopg2
import re

# connect to db
# get a cursor on share_normalizeddata
# for each jsonld datum:
#   strip out email addresses (e.g. `"uri": "mailto:foo@example.com"`)
#   write to a file in the given directory

# create one file per source
# write one json per line, allowing fewer, larger files
# start with one file per source -- might get real big for e.g. crossref, datacite

EMAIL_RE = re.compile(r'"uri":\s*"mailto:[^"]*"', flags=re.IGNORECASE)


def get_cleaned_json_string(json_string):
    return re.sub(EMAIL_RE, '"uri": "mailto:(email redacted)"', json_string)


def write_datums_to_files(output_directory, datums_iterator):
    """clean and write datums according to their source

    @output_directory: string/path-like
    @datums_iterator: iterator of (datum_id, source_name, datum_jsonld) tuples
    """
    for datum_id, source_name, datum_jsonld in datums_iterator:
        print(f'writing datum {datum_id} ...')
        cleaned_datum = get_cleaned_json_string(datum_jsonld)

        file_name = f'{source_name}.json-list'
        file_path = os.path.join(output_directory, file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'a') as open_file:
            open_file.write(cleaned_datum)
            open_file.write('\n')


NORMALIZED_DATA_QUERY = '''
SELECT nd.id,
    u.username,
    nd.data
FROM share_normalizeddata nd
JOIN share_shareuser u ON nd.source_id = u.id
WHERE nd.id >= %(start_id)s
ORDER BY nd.id ASC
LIMIT %(num_records)s
'''


def dump_normalized_data(connection, output_directory, start_id, num_records):
    with connection:
        setup_jsonb_parser(connection)  # don't parse json strings into python objects

        # giving the cursor a name makes it a server-side cursor, will automatically chunk the results (chunk size 2000)
        with connection.cursor('dump_normalized_data') as cursor:
            cursor.execute(NORMALIZED_DATA_QUERY, {
                'start_id': start_id,
                'num_records': num_records,
            })
            write_datums_to_files(output_directory, cursor)


def jsonb_passthrough(value, cursor):
    """parser function for jsonb values that doesn't parse anything, just passes the string value untouched
    """
    return value


def setup_jsonb_parser(connection):
    """disable parsing json to dict for the given connection
    """
    jsonb_type_oid = get_jsonb_type_oid(connection)
    jsonb_passthrough_type = psycopg2.extensions.new_type((jsonb_type_oid,), 'JSONB', jsonb_passthrough)
    psycopg2.extensions.register_type(jsonb_passthrough_type, connection)


def get_jsonb_type_oid(connection):
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT pg_type.oid
            FROM pg_type JOIN pg_namespace ON pg_type.typnamespace = pg_namespace.oid
            WHERE pg_type.typname = %(typname)s AND pg_namespace.nspname = %(namespace)s
        ''', {'typname': 'jsonb', 'namespace': 'pg_catalog'})
        oids = cursor.fetchall()
        return oids[0][0]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dump all normalized data')
    parser.add_argument('output_directory', type=str)
    parser.add_argument('-s', '--start-id', type=int, default=0)
    parser.add_argument('-n', '--num-records', type=int, default=50000)
    parser.add_argument('--db-host', type=str, default='localhost')
    parser.add_argument('--db-name', type=str, default='share')
    parser.add_argument('--db-user', type=str, default='postgres')
    parser.add_argument('--db-port', type=str, default='5432')
    parser.add_argument('--db-password', type=str, default='')
    args = parser.parse_args()

    connection = psycopg2.connect(
        host=args.db_host,
        port=args.db_port,
        dbname=args.db_name,
        user=args.db_user,
        password=args.db_password,
    )
    dump_normalized_data(connection, args.output_directory, args.start_id, args.num_records)
