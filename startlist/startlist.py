import sys
import argparse
import psycopg2
from datetime import datetime
from .genxlsx import GenXLSX
from .genhtml import GenHTML
from .gencm import GenCM

__version__ = "0.2.0"


def format_date(input_date):
    if len(input_date) == 8 and input_date.isdigit():
        return f"{input_date[:4]}-{input_date[4:6]}-{input_date[6:]}"
    return input_date

def remove_tzinfo(dt):
    """Removes timezone info from datetime objects."""
    if isinstance(dt, datetime) and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt

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

full_competition_query = """
SELECT 
    c.id AS competition_id, 
    c.name AS competition_name, 
    c.long_name AS competition_long_name, 
    e.id AS event_id, 
    e.name AS event_name, 
    e.date_time AS event_start_time,
    w.id AS wave_id, 
    w.name AS wave_name, 
    w.start_offset, 
    w.distance, 
    w.laps, 
    w.minutes
FROM 
    core_competition c
JOIN 
    core_eventmassstart e ON e.competition_id = c.id
LEFT JOIN 
    core_wave w ON w.event_id = e.id
WHERE 
    c.%s = '%s';
        """

def export_startlists(host='localhost', date=None, name=None, output_formats=None, racedb_host=None):
    generators = []

    debug = False
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(
            dbname="racedb",
            user="postgres",
            password="5wHYUQ9qmttpq58EV4EG",
            host=host,
            port="5432"
        )
        cur = conn.cursor()

        if name:
            competition_query = "SELECT id, name, long_name FROM core_competition WHERE name = %s;"
            cur_execute(f'Find competition by name {name}', cur, competition_query,  (name,), debug=False)
        else:
            competition_query = "SELECT id, name, long_name FROM core_competition WHERE start_date = %s;"
            cur_execute(f'Find competition by date {date}', cur, competition_query, (date,), debug=False)
        
        competition = cur.fetchone()
        if not competition:
             print(f"No competition found for {name or date}.", file=sys.stderr)
             return
        competition_id, competition_name, competition_long_name = competition
        print(f"Competition found: {competition}", file=sys.stderr)


        if 'xlsx' in output_formats:
            generators.append(GenXLSX(competition_name))
        if 'html' in output_formats:
            generators.append(GenHTML(host, competition_name, date))
        if 'cm' in output_formats:
            generators.append(GenCM(racedb_host, date, competition_id, competition_long_name, ))
        if generators == []:
            print(f"Invalid output format: {output_formats}", file=sys.stderr)
            exit(1)



        # Query to find the competition based on date or name
        if name:
            cur_execute(f'Find competition by name {name}', cur, full_competition_query % ('name', name,), None, debug=False)
        else:
            cur_execute(f'Find competition by date {date}', cur, full_competition_query % ('start_date', date,), None, debug=False)
        
        #competition = cur.fetchone()
        competitions = cur.fetchall()
        if not competitions:
            print(f"No competition found for {name or date}.", file=sys.stderr)
            return
        #print(f"Competition found: {competition}", file=sys.stderr)

        last_event_id = None
        for competition in competitions:
            if not competition:
                print(f"No competition found for {name or date}.", file=sys.stderr)
                return
            #print(f"Competition found: {competition}", file=sys.stderr)
            (competition_id, competition_name, competition_long_name, event_id, event_name, 
                event_start_time, wave_id, wave_name, start_offset, distance, laps, minutes) = competition

            event_start_time = remove_tzinfo(event_start_time)  # Strip timezone info

            print(f"Competition found: {competition_id, competition_name, competition_long_name, event_id, event_name, event_start_time, wave_id, wave_name, start_offset, distance, laps, minutes}", file=sys.stderr)


            if not last_event_id or last_event_id != event_id:
                for generator in generators:
                    generator.add_event(event_id, event_name, event_start_time)
                last_event_id = event_id

            #for generator in generators:
                generator.add_wave(wave_name, start_offset, distance, laps, minutes, [])

            cur_execute(f'Get wave categories {wave_id}', cur, """
                SELECT c.id, c.code, c.gender, c.description
                FROM core_wave_categories wcat
                JOIN core_category c ON wcat.category_id = c.id
                WHERE wcat.wave_id = %s;
            """, (wave_id,), debug=debug)
            categories = cur.fetchall()
            for generator in generators:
                generator.add_wave(wave_name, start_offset, distance, laps, minutes, categories)
            #log_debug(f"Categories found for wave {wave_name}: {categories}")

            # Now, find participants for each category within the wave
            for category_id, category_code, category_gender, category_description in categories:
                #log_debug(f"Processing category {category_code} for wave {wave_name}")
                cur_execute(f'Get participants for each wave {competition_id, category_id}', cur,"""
                    SELECT lh.first_name, lh.last_name, lh.license_code, p.bib, lh.uci_id, t.name as team_name
                    FROM core_participant p
                    LEFT JOIN core_licenseholder lh ON p.license_holder_id = lh.id
                    LEFT JOIN core_team t ON p.team_id = t.id
                    WHERE p.competition_id = %s AND p.category_id = %s
                    ORDER BY p.bib ASC;
                    """,
                    (competition_id, category_id), debug=debug)

                participants = cur.fetchall()
                #log_debug(f"Participants found for wave {wave_name} and category {category_code}: {participants}")

                #for participant in participants:
                #    log_debug(f"Adding participant: {participant}")
        
                for participant in participants:
                    #print('Participant:', participant, file=sys.stderr)
                    first_name, last_name, license_code, bib, uci_id, team_name = participant  

                    #generator.add_participant(event_section_id, wave_name, participant)
                    formatted_participant = {
                      'bib': bib,
                      'first_name': first_name,
                      'last_name': last_name,
                      'team_name': team_name,
                      'wave_name': wave_name,
                      'category_code': category_code,
                      'uci_id': uci_id
                    }
                    #print(f"Adding participant: {formatted_participant}", file=sys.stderr)
                    for generator in generators:
                        generator.add_participant(None, wave_name, formatted_participant)




        # Save the generated file
        for generator in generators:
            output_filename = generator.save()
        #print(f"File generated: {output_filename}", file=sys.stderr)

    except psycopg2.DatabaseError as error:
        print(f"Database error: {error}", file=sys.stderr)
    finally:
        cur.close()
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Export start lists for a RaceDB competition.")
    parser.add_argument('--host', type=str, default='localhost', help='database host')
    parser.add_argument('--date', type=str, help='Start date of the competition in YYYY-MM-DD format.')
    parser.add_argument('--name', type=str, help='Name of the competition.')
    parser.add_argument('--xlsx', action='store_true', help='Generate XLSX output')
    parser.add_argument('--html', action='store_true', help='Generate HTML output')
    parser.add_argument("--crossmgr", required=False, help="The RaceDB host for downloading files.")

    args = parser.parse_args()

    formatted_date = format_date(args.date) if args.date else None

    output_formats = []
    if args.xlsx:
        output_formats.append('xlsx')

    if args.html:
        output_formats.append('html')

    if args.crossmgr:
        output_formats.append('cm')

    export_startlists(args.host, date=formatted_date, name=args.name, output_formats=output_formats, racedb_host=args.crossmgr)

if __name__ == "__main__":
    main()
