
import sys
import argparse
import os
import psycopg2

def log_debug(message):
    print(message, file=sys.stderr)

def log_sql(query, params, debug=True):
    """Logs the fully expanded SQL query with parameters."""
    expanded_query = query % tuple(map(lambda x: f"'{x}'" if isinstance(x, str) else str(x), params)) if params else query
    if debug:
            log_debug(f"Executing SQL: {expanded_query}")


def cur_execute(msg, cur, query, params, debug=True):
    """Executes a query with parameters and logs the expanded query."""
    log_debug(msg)
    log_sql(query, params, debug=debug)
    cur.execute(query, params)

def connect_db(host):
    # Connect to PostgreSQL database
    conn = psycopg2.connect(
        dbname="racedb",
        user="postgres",
        password="5wHYUQ9qmttpq58EV4EG",
        host=host,
        port="5432"
    )
    cur = conn.cursor()
    tz = os.environ.get("TZ")
    if tz:
        try:
            cur.execute("SET TIME ZONE %s;", (tz,))
        except Exception as e:
            print(f"Warning: Failed to set TIME ZONE to {tz}: {e}", file=sys.stderr)
    return conn, cur

def find_numberset(host, numberset=None):
    try:
        # Connect to PostgreSQL database
        conn, cur = connect_db(host)
        numberset_query = "SELECT id, name, description, sponsor FROM core_numberset WHERE name = %s;"
        cur_execute(f'Find numberset by name {numberset}', cur, numberset_query, (numberset,), debug=True)
        numberset = cur.fetchone()
        if not numberset:
             print(f"No numberset found for {numberset}.", file=sys.stderr)
             return
        numberset_id, numberset_name, numberset_description, numberset_sponsor = numberset
        print(f"Numberset found: {numberset_id}", file=sys.stderr)
        

    except psycopg2.DatabaseError as error:
        print(f"Database error: {error}", file=sys.stderr)
    return conn, cur, numberset_id, numberset_name, numberset_description, numberset_sponsor

# Query to find the competition based on date or name

competition_query_by_category = """
SELECT cc.id, cc.name, cc.long_name, cc.start_date, cc.number_set_id, 
FROM core_competition cc
JOIN core_categoryformat cf ON cc.category_format_id = cf.id
WHERE 
    cf.name = %s
ORDER BY
    cc.start_date DESC
LIMIT 1; 
"""

def find_competition(host, name=None, date=None, category_format=None):
    try:
        # Connect to PostgreSQL database
        conn, cur = connect_db(host)

        if name or date:
            where_clauses = []
            params = []
            if name:
                where_clauses.append("name = %s")
                params.append(name)
            if date:
                where_clauses.append("start_date = %s")
                params.append(date)

            competition_query = (
                "SELECT id, name, long_name, start_date, number_set_id "
                "FROM core_competition "
                f"WHERE {' AND '.join(where_clauses)};"
            )
            query_desc = []
            if name:
                query_desc.append(f"name {name}")
            if date:
                query_desc.append(f"date {date}")
            cur_execute(
                f"Find competition by {' and '.join(query_desc)}",
                cur,
                competition_query,
                tuple(params),
                debug=bool(date),
            )
        elif category_format:
            cur_execute(f'Find competition by category format {category_format}', cur, competition_query_by_category, (category_format,), debug=True)
        else:
            print("No name, date or category format specified.", file=sys.stderr)
            return None, None, None, None, None, None
        
        competition = cur.fetchone()
        if not competition:
             filters = ", ".join(
                 part for part in [
                     f"name={name}" if name else "",
                     f"date={date}" if date else "",
                     f"category_format={category_format}" if category_format else "",
                 ] if part
             )
             print(f"No competition found for {filters}.", file=sys.stderr)
             return
        competition_id, competition_name, competition_long_name, competition_start_date, number_set_id = competition
        print(f"Competition found: {competition}", file=sys.stderr)

    except psycopg2.DatabaseError as error:
        print(f"Database error: {error}", file=sys.stderr)
    return conn, cur, competition_id, competition_name, competition_long_name, competition_start_date, number_set_id
