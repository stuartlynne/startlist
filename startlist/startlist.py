import sys
import argparse
import psycopg2
from datetime import datetime
from .genxlsx import GenXLSX
from .genhtml import GenHTML

__version__ = "0.1.0"

def remove_tzinfo(dt):
    """Removes timezone info from datetime objects."""
    if isinstance(dt, datetime) and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt

def log_debug(message):
    print(message, file=sys.stderr)

def log_sql(query, params):
    """Logs the fully expanded SQL query with parameters."""
    expanded_query = query % tuple(map(lambda x: f"'{x}'" if isinstance(x, str) else str(x), params))
    log_debug(f"Executing SQL: {expanded_query}")

def cur_execute(cur, query, params):
    """Executes a query with parameters and logs the expanded query."""
    log_sql(query, params)
    cur.execute(query, params)

def export_startlists(date=None, name=None, output_format='xlsx'):
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(
            dbname="racedb",
            user="postgres",
            password="5wHYUQ9qmttpq58EV4EG",
            host="localhost",
            port="5432"
        )
        cur = conn.cursor()

        # Query to find the competition based on date or name
        if name:
            competition_query = "SELECT id, name FROM core_competition WHERE name = %s;"
            cur_execute(cur, competition_query, (name,))
        else:
            competition_query = "SELECT id, name FROM core_competition WHERE start_date = %s;"
            cur_execute(cur, competition_query, (date,))
        
        competition = cur.fetchone()
        if not competition:
            print(f"No competition found for {name or date}.")
            return
        competition_id, competition_name = competition

        # Initialize either XLSX or HTML generator based on the flag
        if output_format == 'xlsx':
            generator = GenXLSX(competition_name)
        else:
            generator = GenHTML(competition_name, date)

        # Query for Mass Start Events for the competition
        cur_execute(cur, "SELECT id, name, date_time FROM core_eventmassstart WHERE competition_id = %s;", (competition_id,))
        events = cur.fetchall()

        for event_id, event_name, event_start_time in events:
            event_start_time = remove_tzinfo(event_start_time)  # Strip timezone info
            event_section_id = generator.add_event(event_name, event_start_time)

            # Query for all waves for the event
            #cur_execute(cur, "SELECT id, name, date_time FROM core_eventmassstart WHERE competition_id = %s;", (competition_id,))
            cur_execute(cur, "SELECT id, name, start_offset, distance, laps, minutes FROM core_wave WHERE event_id = %s;", (event_id,))
            waves = cur.fetchall()

            # Sort waves by start_offset
            waves_sorted = sorted(waves, key=lambda wave: wave[2])  # Sorting by start_offset
            log_debug(f"Waves found for event {event_name}: {waves}")

            # Query for Waves and their Categories
            # For each wave, fetch its categories and the participants in those categories
            for wave_id, wave_name, start_offset, distance, laps, minutes in waves_sorted:


                cur_execute(cur, """
                    SELECT c.id, c.code, c.gender, c.description
                    FROM core_wave_categories wcat
                    JOIN core_category c ON wcat.category_id = c.id
                    WHERE wcat.wave_id = %s;
                """, (wave_id,))
                categories = cur.fetchall()
                generator.add_wave(wave_name, start_offset, distance, laps, minutes, categories)
                log_debug(f"Categories found for wave {wave_name}: {categories}")

                # Now, find participants for each category within the wave
                for category_id, category_code, category_gender, category_description in categories:
                    log_debug(f"Processing category {category_code} for wave {wave_name}")
                    cur_execute(cur,"""
                        SELECT lh.first_name, lh.last_name, lh.license_code, p.bib, lh.uci_id, t.name as team_name
                        FROM core_participant p
                        LEFT JOIN core_licenseholder lh ON p.license_holder_id = lh.id
                        LEFT JOIN core_team t ON p.team_id = t.id
                        WHERE p.competition_id = %s AND p.category_id = %s;
                        """,
                        (competition_id, category_id))

                    participants = cur.fetchall()
                    log_debug(f"Participants found for wave {wave_name} and category {category_code}: {participants}")

                    for participant in participants:
                        log_debug(f"Adding participant: {participant}")
            
                    for participant in participants:
                        print('Participant:', participant, file=sys.stderr)
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
                        print(f"Adding participant: {formatted_participant}", file=sys.stderr)
                        generator.add_participant(None, wave_name, formatted_participant)


        # Save the generated file
        output_filename = generator.save()
        print(f"File generated: {output_filename}")

    except psycopg2.DatabaseError as error:
        print(f"Database error: {error}")
    finally:
        cur.close()
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Export start lists for a RaceDB competition.")
    parser.add_argument('--date', type=str, help='Start date of the competition in YYYY-MM-DD format.')
    parser.add_argument('--name', type=str, help='Name of the competition.')
    parser.add_argument('--xlsx', action='store_true', help='Generate XLSX output')
    parser.add_argument('--html', action='store_true', help='Generate HTML output')

    args = parser.parse_args()

    output_format = 'xlsx' if args.xlsx else 'html'
    export_startlists(date=args.date, name=args.name, output_format=output_format)

if __name__ == "__main__":
    main()
