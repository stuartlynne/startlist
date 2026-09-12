import sys
import os
import psycopg2
import re
from psycopg2.extras import DictCursor
import traceback
from datetime import datetime, timedelta

from autopage import argparse
import autopage
from openpyxl import load_workbook

from libs.autopageex import AutoPagerEx
from libs.getranges import get_ranges

from libs.findsql import find_competition, cur_execute, log_debug
from startlist.genxlsx import GenXLSX
from startlist.genhtml import GenHTML
from startlist.gencm import GenCM
from startlist.genaudit import GenAudit
from startlist.genbibs import GenBibs
from startlist.geninfo import GenInfo
from startlist.genpdf import GenPDF
from startlist.genttpdf import GenTTPDF
from startlist.genttxlsx import GenTTXLSX

__version__ = "0.5.22"


def format_date(input_date):
    if len(input_date) == 8 and input_date.isdigit():
        return f"{input_date[:4]}-{input_date[4:6]}-{input_date[6:]}"
    return input_date

def remove_tzinfo(dt):
    """Removes timezone info from datetime objects."""
    if isinstance(dt, datetime) and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt

def normalize_event_time(event_name, event_start_time):
    """If event_name contains a time (e.g., '10:30AM'), align event_start_time to it."""
    if not isinstance(event_start_time, datetime):
        return event_start_time
    m = re.search(r"\b(\d{1,2}):(\d{2})\s*([AP]M)\b", event_name, re.IGNORECASE)
    if not m:
        return event_start_time
    hour = int(m.group(1)) % 12
    minute = int(m.group(2))
    ampm = m.group(3).upper()
    if ampm == "PM":
        hour += 12
    candidate = event_start_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
    delta_minutes = int((candidate - event_start_time).total_seconds() / 60)
    if delta_minutes != 0:
        print(
            f"Adjusting event_start_time from {event_start_time!r} to {candidate!r} "
            f"based on event_name '{event_name}' (delta {delta_minutes}m)",
            file=sys.stderr,
        )
        return candidate
    print(
        f"Event name time matches event_start_time: {event_name} -> {event_start_time!r}",
        file=sys.stderr,
    )
    return event_start_time


def normalize_callup_value(value):
    """Normalize workbook/startlist values for robust matching."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip()).upper()


def normalize_callup_sheet_name(sheet_name):
    """Use the sheet prefix before the optional gender suffix: 'Wave Name (Open)'."""
    return normalize_callup_value(re.sub(r"\s+\((MEN|WOMEN|OPEN)\)\s*$", "", sheet_name, flags=re.IGNORECASE))


def compact_callup_wave_key(value):
    """Compact wave/category names for fallback matching across RaceDB/series labels."""
    normalized = normalize_callup_sheet_name(value)
    normalized = re.sub(r"\b(MEN|WOMEN|OPEN|WAVE)\b", "", normalized)
    return re.sub(r"[^A-Z0-9]+", "", normalized)


def callup_match_keys(first_name=None, last_name=None, license_code=None, uci_id=None):
    keys = []
    normalized_uci = normalize_callup_value(uci_id)
    if normalized_uci:
        keys.append(("uci", normalized_uci))

    normalized_license = normalize_callup_value(license_code)
    if normalized_license and normalized_license not in {"TEMP", "N/A", "NA"}:
        keys.append(("license", normalized_license))

    normalized_name = normalize_callup_value(f"{last_name or ''}, {first_name or ''}")
    if normalized_name != ",":
        keys.append(("name", normalized_name))

    return keys


def load_callups(callups_filename):
    """Load series callup order keyed by wave-sheet prefix and rider identity."""
    if not callups_filename:
        return {}

    wb = load_workbook(callups_filename, read_only=True, data_only=True)
    callups = {}

    for ws in wb.worksheets:
        wave_key = normalize_callup_sheet_name(ws.title)
        if not wave_key:
            continue

        header = None
        header_row_num = None
        for row_num, row in enumerate(ws.iter_rows(values_only=True), start=1):
            normalized = [normalize_callup_value(cell) for cell in row]
            if "POS" in normalized and "NAME" in normalized:
                header = normalized
                header_row_num = row_num
                break

        if not header:
            print(f"Callups: no header row found in sheet {ws.title!r}; skipping", file=sys.stderr)
            continue

        col = {name: idx for idx, name in enumerate(header) if name}
        sheet_callups = {}
        order = 0

        for row in ws.iter_rows(min_row=header_row_num + 1, values_only=True):
            name = row[col["NAME"]] if "NAME" in col and col["NAME"] < len(row) else None
            if not name:
                continue

            order += 1
            license_code = row[col["LICENSE"]] if "LICENSE" in col and col["LICENSE"] < len(row) else None
            uci_id = row[col["UCI ID"]] if "UCI ID" in col and col["UCI ID"] < len(row) else None

            first_name = ""
            last_name = ""
            if "," in str(name):
                last_name, first_name = [part.strip() for part in str(name).split(",", 1)]
            else:
                last_name = str(name).strip()

            for key in callup_match_keys(first_name, last_name, license_code, uci_id):
                sheet_callups.setdefault(key, order)

        callups[wave_key] = sheet_callups
        print(f"Callups: loaded {order} rows for {ws.title!r}", file=sys.stderr)

    return callups


def find_callups_for_wave(callups, wave_name):
    """Find callups using exact, prefix, then compact fallback matching."""
    wave_key = normalize_callup_sheet_name(wave_name)
    if wave_key in callups:
        return callups[wave_key]

    prefix_matches = [
        sheet_callups
        for sheet_key, sheet_callups in callups.items()
        if sheet_key.startswith(wave_key) or wave_key.startswith(sheet_key)
    ]
    if len(prefix_matches) == 1:
        return prefix_matches[0]

    compact_wave_key = compact_callup_wave_key(wave_name)
    compact_matches = [
        sheet_callups
        for sheet_key, sheet_callups in callups.items()
        if compact_callup_wave_key(sheet_key) == compact_wave_key
    ]
    if len(compact_matches) == 1:
        return compact_matches[0]

    return None


def apply_callup_position(participant, wave_name, callups):
    """Annotate a participant with a callup position if their wave has one."""
    participant['callup_position'] = None
    if not callups:
        return

    wave_callups = find_callups_for_wave(callups, wave_name)
    if not wave_callups:
        return

    for key in callup_match_keys(
        participant.get('first_name'),
        participant.get('last_name'),
        participant.get('license_code'),
        participant.get('uci_id'),
    ):
        if key in wave_callups:
            participant['callup_position'] = wave_callups[key]
            return


def log_sql(query, params, debug=True):
    """Logs the fully expanded SQL query with parameters."""
    expanded_query = query % tuple(map(lambda x: f"'{x}'" if isinstance(x, str) else str(x), params)) if params else query
    if debug:
        log_debug(f"Executing SQL: {expanded_query}")

#def cur_execute(msg, cur, query, params, debug=True):
#    """Executes a query with parameters and logs the expanded query."""
#    log_debug(msg)
#    log_sql(query, params, debug=debug)
#    cur.execute(query, params)

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

tt_competition_query = """
SELECT
    c.id AS competition_id,
    c.name AS competition_name,
    c.long_name AS competition_long_name,
    e.id AS event_id,
    e.name AS event_name,
    e.date_time AS event_start_time,
    w.id AS wave_id,
    w.name AS wave_name,
    w.gap_before_wave AS start_offset,
    w.distance,
    w.laps,
    NULL::smallint AS minutes
FROM
    core_competition c
JOIN
    core_eventtt e ON e.competition_id = c.id
LEFT JOIN
    core_wavett w ON w.event_id = e.id
WHERE
    c.%s = '%s'
ORDER BY
    e.date_time,
    w.sequence NULLS LAST,
    w.id;
        """

tt_participants_query = """
SELECT
    e.id AS event_id,
    e.name AS event_name,
    e.date_time AS event_start_time,
    wc.wave_id,
    wc.wave_name,
    wc.wave_sequence,
    cat.id AS category_id,
    cat.code AS category_code,
    cat.gender AS category_gender,
    cat.description AS category_description,
    p.id AS participant_id,
    lh.first_name,
    lh.last_name,
    lh.date_of_birth,
    lh.city,
    lh.state_prov,
    lh.nation_code,
    lh.license_code,
    p.bib,
    p.tag,
    p.tag2,
    lh.uci_id,
    t.name AS team_name,
    p.preregistered,
    p.registration_timestamp,
    p.tag_checked,
    p.license_checked,
    p.paid,
    p.confirmed,
    ett.start_sequence,
    ett.start_time,
    e.date_time + (ett.start_time * interval '1 second') AS scheduled_start_time
FROM
    core_eventtt e
JOIN
    core_entrytt ett ON ett.event_id = e.id
JOIN
    core_participant p ON p.id = ett.participant_id
LEFT JOIN
    core_licenseholder lh ON lh.id = p.license_holder_id
LEFT JOIN
    core_team t ON t.id = p.team_id
LEFT JOIN
    core_category cat ON cat.id = p.category_id
LEFT JOIN
    (
        SELECT
            w.id AS wave_id,
            w.name AS wave_name,
            w.sequence AS wave_sequence,
            w.event_id,
            wtc.category_id
        FROM
            core_wavett w
        JOIN
            core_wavett_categories wtc ON wtc.wavett_id = w.id
    ) wc ON wc.event_id = e.id AND wc.category_id = p.category_id
WHERE
    e.id = %s
ORDER BY
    COALESCE(wc.wave_sequence, 9999),
    ett.start_sequence,
    ett.start_time,
    lh.last_name,
    lh.first_name;
        """

tt_fallback_participants_query = """
SELECT
    e.id AS event_id,
    e.name AS event_name,
    e.date_time AS event_start_time,
    w.id AS wave_id,
    w.name AS wave_name,
    w.sequence AS wave_sequence,
    w.gap_before_wave,
    w.regular_start_gap,
    cat.id AS category_id,
    cat.code AS category_code,
    cat.gender AS category_gender,
    cat.description AS category_description,
    p.id AS participant_id,
    lh.first_name,
    lh.last_name,
    lh.date_of_birth,
    lh.city,
    lh.state_prov,
    lh.nation_code,
    lh.license_code,
    p.bib,
    p.tag,
    p.tag2,
    lh.uci_id,
    t.name AS team_name,
    p.preregistered,
    p.registration_timestamp,
    p.tag_checked,
    p.license_checked,
    p.paid,
    p.confirmed
FROM
    core_eventtt e
JOIN
    core_wavett w ON w.event_id = e.id
JOIN
    core_wavett_categories wtc ON wtc.wavett_id = w.id
JOIN
    core_category cat ON cat.id = wtc.category_id
JOIN
    core_participant p ON p.competition_id = e.competition_id AND p.category_id = cat.id
LEFT JOIN
    core_licenseholder lh ON lh.id = p.license_holder_id
LEFT JOIN
    core_team t ON t.id = p.team_id
WHERE
    e.id = %s
ORDER BY
    w.sequence NULLS LAST,
    p.registration_timestamp,
    p.bib,
    lh.last_name,
    lh.first_name;
        """


def synthesize_tt_entries(tt_rows):
    """Build synthetic TT entries when core_entrytt has not been populated yet."""
    if not tt_rows:
        return []

    grouped_rows = {}
    ordered_waves = []
    for row in tt_rows:
        wave_id = row[3]
        if wave_id not in grouped_rows:
            ordered_waves.append(
                {
                    'wave_id': wave_id,
                    'wave_name': row[4],
                    'wave_sequence': row[5],
                    'gap_before_wave': row[6] or 0,
                    'regular_start_gap': row[7] or 60,
                }
            )
            grouped_rows[wave_id] = []
        grouped_rows[wave_id].append(row)

    synthetic_rows = []
    start_sequence = 1
    current_start_time = None

    for wave in ordered_waves:
        wave_id = wave['wave_id']
        wave_rows = grouped_rows.get(wave_id, [])
        if current_start_time is None:
            current_start_time = wave['gap_before_wave']
        else:
            current_start_time += wave['gap_before_wave']

        for index, row in enumerate(wave_rows):
            if index:
                current_start_time += wave['regular_start_gap']

            event_start_time = row[2]
            scheduled_start_time = None
            if event_start_time is not None:
                scheduled_start_time = event_start_time + timedelta(seconds=current_start_time)

            synthetic_rows.append(
                (
                    row[0],   # event_id
                    row[1],   # event_name
                    row[2],   # event_start_time
                    row[3],   # wave_id
                    row[4],   # wave_name
                    row[5],   # wave_sequence
                    row[8],   # category_id
                    row[9],   # category_code
                    row[10],  # category_gender
                    row[11],  # category_description
                    row[12],  # participant_id
                    row[13],  # first_name
                    row[14],  # last_name
                    row[15],  # date_of_birth
                    row[16],  # city
                    row[17],  # state_prov
                    row[18],  # nation_code
                    row[19],  # license_code
                    row[20],  # bib
                    row[21],  # tag
                    row[22],  # tag2
                    row[23],  # uci_id
                    row[24],  # team_name
                    row[25],  # preregistered
                    row[26],  # registration_timestamp
                    row[27],  # tag_checked
                    row[28],  # license_checked
                    row[29],  # paid
                    row[30],  # confirmed
                    start_sequence,
                    float(current_start_time),
                    scheduled_start_time,
                )
            )
            start_sequence += 1

    return synthetic_rows

def export_startlists(
    host='localhost',
    date=None,
    name=None,
    output_formats=None,
    racedb_host=None,
    landscape=False,
    final=False,
    lap_abc=False,
    tt_detail_column=None,
    callups_filename=None,
    series_all=False,
):
    generators = []

    print('Output formats:', output_formats, file=sys.stderr)
    debug = False
    try:
        callups = load_callups(callups_filename) if callups_filename else {}

        # get competition id based on date or name
        conn, cur, competition_id, competition_name, competition_long_name, competition_start_date, number_set_id = find_competition(host, name, date) 
        print(f"Competition found: {competition_id, competition_name, competition_long_name, competition_start_date, number_set_id}", file=sys.stderr)
        cur_execute(
            f'Get competition details {competition_id}',
            cur,
            """
                SELECT organizer, city, "stateProv", country
                FROM core_competition
                WHERE id = %s;
            """,
            [competition_id],
            debug=debug,
        )
        competition_details = cur.fetchone() or ("", "", "", "")
        competition_organizer, competition_city, competition_state_prov, competition_country = competition_details

        if set(["html", "info", "bibs", "pdf", ]) & set(output_formats):
            # Query to find the bib ranges for each category in the wave
            # core_categorynumbers - range_str
            # core_categorynumbers_categories - categorynumbers_id, category_id

                
            cur_execute(f'Get bib ranges for category {competition_id}', cur, """
                SELECT cf.name AS format_name, cc.code, cc.gender, cc.description, cn.range_str
                FROM core_category cc
                JOIN core_categoryformat cf ON cc.format_id = cf.id
                JOIN core_categorynumbers_categories cnc ON cc.id = cnc.category_id
                JOIN core_categorynumbers cn ON cnc.categorynumbers_id = cn.id
                WHERE cn.competition_id = %s;
                """,
                [competition_id], debug=debug)

            ranges = cur.fetchall()
            #print(f"Ranges {ranges}", file=sys.stderr)

        if set(["info", "bibs"]) & set(output_formats):
            # Query to get bib usage info
            cur_execute(f'Get bib usage info {competition_id}', cur, "SELECT bib, date_lost FROM core_numbersetentry WHERE number_set_id = %s ORDER BY bib;",
                [number_set_id], debug=debug)
            bibs = cur.fetchall()
            #print(f"bibs {bibs}", file=sys.stderr)


        tt_generators = []

        if 'html' in output_formats:
            generators.append(GenHTML(host, competition_name, date, ranges, ))
        if 'cm' in output_formats:
            generators.append(GenCM(racedb_host, date, competition_id, competition_name, series_all=series_all))
        if 'audit' in output_formats:
            generators.append(GenAudit(racedb_host, date, competition_id, competition_long_name, ))
        if 'bibs' in output_formats:
            generators.append(GenBibs(racedb_host, date, competition_id, competition_long_name, ranges, bibs, ))
        if 'info' in output_formats:
            generators.append(GenInfo(racedb_host, date, competition_id, competition_long_name, ranges, bibs, ))
        if 'pdf' in output_formats:
            generators.append(GenPDF(date, competition_name, competition_long_name, landscape=landscape, final=final, lap_abc=lap_abc)) 
        if 'xlsx' in output_formats:
            generators.append(GenXLSX(date, competition_name, competition_long_name))
        if 'pdf' in output_formats:
            tt_generators.append(
                GenTTPDF(
                    date,
                    competition_name,
                    competition_long_name,
                    landscape=landscape,
                    final=final,
                    detail_column=tt_detail_column,
                )
            )
        if 'cm' in output_formats:
            tt_generators.append(
                GenTTXLSX(
                    date,
                    competition_name,
                    competition_long_name,
                    organizer=competition_organizer,
                    city=competition_city,
                    state_prov=competition_state_prov,
                    country=competition_country,
                )
            )
        if generators == []:
            print(f"Invalid output format: {output_formats}", file=sys.stderr)
            exit(1)

        # Dictionary to accumulate bib numbers per category
        category_bibs = {}
        has_mass_start_events = False
        has_tt_events = False

        if set(["pdf", "xlsx", "html", "audit", "info", "cm", ]) & set(output_formats):

            # Query to find the competition mass-start events and waves.
            cur_execute(
                f'Find competition events and waves by competition id {competition_id}',
                cur,
                full_competition_query % ('id', competition_id,),
                None,
                debug=True,
            )
            
            #competition = cur.fetchone()
            waves = cur.fetchall()
            if not waves:
                print(f"No mass-start competition events and waves found for competition {competition_id}.", file=sys.stderr)
            else:
                has_mass_start_events = True

            last_event_id = None
            tz_env = os.environ.get("TZ", "")
            if tz_env:
                print(f"TZ env: {tz_env}", file=sys.stderr)
            for wave in waves:
                if not wave:
                    print(f"No wave found for {name or date}.", file=sys.stderr)
                    return
                #print(f"wave found: {wave}", file=sys.stderr)
                (competition_id, competition_name, competition_long_name, event_id, event_name, 
                    event_start_time, wave_id, wave_name, start_offset, distance, laps, minutes) = wave

                print(f"Raw event_start_time: {event_start_time!r}, tzinfo={getattr(event_start_time, 'tzinfo', None)}",
                      file=sys.stderr)
                event_start_time = remove_tzinfo(event_start_time)  # Strip timezone info
                print(f"Normalized event_start_time: {event_start_time!r}", file=sys.stderr)
                event_start_time = normalize_event_time(event_name, event_start_time)

                print(f"wave found: {event_id, event_name, event_start_time, wave_id, wave_name, start_offset, distance, laps, minutes}", file=sys.stderr)


                if not last_event_id or last_event_id != event_id:
                    for generator in generators:
                        generator.add_event(event_id, event_name, event_start_time)
                    last_event_id = event_id

                #for generator in generators:
                    generator.add_wave(event_id, wave_id, wave_name, start_offset, distance, laps, minutes, [])


                # Query to find the categories for the wave id
                # 
                cur_execute(f'Get wave categories {wave_id}', cur, """
                    SELECT c.id, c.code, c.gender, c.description
                    FROM core_wave_categories wcat
                    JOIN core_category c ON wcat.category_id = c.id
                    WHERE wcat.wave_id = %s;
                """, (wave_id,), debug=debug)
                categories = cur.fetchall()
                for generator in generators:
                    generator.add_wave(last_event_id, wave_id, wave_name, start_offset, distance, laps, minutes, categories)
                log_debug(f"Categories found for wave {wave_name}: {categories}")



                # Now, find participants for each category within the wave
                for category_id, category_code, category_gender, category_description in categories:

                    # Query to find the bib ranges for each category in the wave
                    # core_categorynumbers - range_str
                    # core_categorynumbers_categories - categorynumbers_id, category_id


                    #log_debug(f"Processing category {category_id} {category_code} for wave {wave_name}")
                    cur_execute(f'Get participants for each wave {competition_id, category_id}', cur,"""
                        SELECT lh.first_name, lh.last_name, lh.license_code, p.bib, lh.uci_id, t.name as team_name,
                            p.preregistered, p.registration_timestamp, p.tag_checked, p.license_checked, p.paid, p.confirmed
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
                        first_name, last_name, license_code, bib, uci_id, team_name, preregistered, registration_timestamp, tag_checked, license_checked, paid, confirmed = participant

                        cat_name = f"{category_code} ({['Men', 'Women', 'Open'][category_gender]})"

                        if cat_name not in category_bibs:
                            category_bibs[cat_name] = []
                        category_bibs[cat_name].append(bib)

                        #generator.add_participant(event_section_id, wave_name, participant)
                        formatted_participant = {
                          'bib': bib,
                          'first_name': first_name,
                          'last_name': last_name,
                          'license_code': license_code,
                          'team_name': team_name,
                          'wave_name': wave_name,
                          'category_code': category_code,
                          'uci_id': uci_id,
                          'preregistered': preregistered,
                          'registration_timestamp': registration_timestamp,
                          'tag_checked': tag_checked,
                          'license_checked': license_checked,
                          'category_gender': category_gender,
                          'paid': paid,
                          'confirmed': confirmed,
                        }
                        apply_callup_position(formatted_participant, wave_name, callups)
                        #print(f"Adding participant: {formatted_participant}", file=sys.stderr)
                        for generator in generators:
                            generator.add_participant(None, wave_id, wave_name, formatted_participant)

            # Query to find time trial events and waves for the same competition.
            cur_execute(
                f'Find TT competition events and waves by competition id {competition_id}',
                cur,
                tt_competition_query % ('id', competition_id,),
                None,
                debug=True,
            )

            tt_waves = cur.fetchall()
            if tt_waves:
                has_tt_events = True
                print(f"TT events and waves found: {len(tt_waves)} rows", file=sys.stderr)
                tt_event_ids = []
                for tt_wave in tt_waves:
                    (
                        tt_competition_id,
                        tt_competition_name,
                        tt_competition_long_name,
                        tt_event_id,
                        tt_event_name,
                        tt_event_start_time,
                        tt_wave_id,
                        tt_wave_name,
                        tt_start_offset,
                        tt_distance,
                        tt_laps,
                        tt_minutes,
                    ) = tt_wave

                    tt_event_start_time = remove_tzinfo(tt_event_start_time)
                    tt_event_start_time = normalize_event_time(tt_event_name, tt_event_start_time)
                    print(
                        f"TT wave found: "
                        f"{(tt_event_id, tt_event_name, tt_event_start_time, tt_wave_id, tt_wave_name, tt_start_offset, tt_distance, tt_laps, tt_minutes)}",
                        file=sys.stderr,
                    )
                    if tt_event_id not in tt_event_ids:
                        tt_event_ids.append(tt_event_id)
                        for generator in tt_generators:
                            generator.add_event(tt_event_id, tt_event_name, tt_event_start_time)
                    cur_execute(f'Get TT wave categories {tt_wave_id}', cur, """
                        SELECT c.id, c.code, c.gender, c.description
                        FROM core_wavett_categories wcat
                        JOIN core_category c ON wcat.category_id = c.id
                        WHERE wcat.wavett_id = %s;
                    """, (tt_wave_id,), debug=debug)
                    tt_categories = cur.fetchall()
                    for generator in tt_generators:
                        generator.add_wave(tt_event_id, tt_wave_id, tt_wave_name, tt_start_offset, tt_distance, tt_laps, tt_minutes, tt_categories)

                for tt_event_id in tt_event_ids:
                    cur_execute(
                        f'Get TT participants for event {tt_event_id}',
                        cur,
                        tt_participants_query,
                        (tt_event_id,),
                        debug=debug,
                    )
                    tt_participants = cur.fetchall()
                    print(f"TT participants for event {tt_event_id}: {len(tt_participants)} rows", file=sys.stderr)
                    if not tt_participants:
                        cur_execute(
                            f'Get fallback TT participants for event {tt_event_id}',
                            cur,
                            tt_fallback_participants_query,
                            (tt_event_id,),
                            debug=debug,
                        )
                        fallback_tt_rows = cur.fetchall()
                        print(
                            f"Fallback TT participant rows for event {tt_event_id}: {len(fallback_tt_rows)} rows",
                            file=sys.stderr,
                        )
                        tt_participants = synthesize_tt_entries(fallback_tt_rows)
                        print(
                            f"Synthesized TT participants for event {tt_event_id}: {len(tt_participants)} rows",
                            file=sys.stderr,
                        )
                    for tt_participant in tt_participants:
                        (
                            _event_id,
                            _event_name,
                            _event_start_time,
                            _wave_id,
                            _wave_name,
                            _wave_sequence,
                            _category_id,
                            _category_code,
                            _category_gender,
                            _category_description,
                            _participant_id,
                            _first_name,
                            _last_name,
                            _date_of_birth,
                            _city,
                            _state_prov,
                            _nation_code,
                            _license_code,
                            _bib,
                            _tag,
                            _tag2,
                            _uci_id,
                            _team_name,
                            _preregistered,
                            _registration_timestamp,
                            _tag_checked,
                            _license_checked,
                            _paid,
                            _confirmed,
                            _start_sequence,
                            _start_time,
                            _scheduled_start_time,
                        ) = tt_participant

                        scheduled_start_time = remove_tzinfo(_scheduled_start_time)
                        print(
                            "TT participant: "
                            f"event={_event_name!r} wave={_wave_name!r} "
                            f"start_sequence={_start_sequence} start_time={_start_time} "
                            f"scheduled_start_time={scheduled_start_time!r} "
                            f"bib={_bib} name={_last_name!r}, {_first_name!r} "
                            f"category={_category_code!r} team={_team_name!r}",
                            file=sys.stderr,
                        )
                        formatted_tt_participant = {
                            'bib': _bib,
                            'first_name': _first_name,
                            'last_name': _last_name,
                            'team_name': _team_name,
                            'category_code': _category_code,
                            'category_gender': _category_gender,
                            'gender': ['Men', 'Women', 'Open'][_category_gender],
                            'date_of_birth': _date_of_birth,
                            'city': _city,
                            'state_prov': _state_prov,
                            'nation_code': _nation_code,
                            'license_code': _license_code,
                            'tag': _tag,
                            'tag2': _tag2,
                            'uci_id': _uci_id,
                            'preregistered': _preregistered,
                            'registration_timestamp': _registration_timestamp,
                            'tag_checked': _tag_checked,
                            'license_checked': _license_checked,
                            'paid': _paid,
                            'confirmed': _confirmed,
                            'start_sequence': _start_sequence,
                            'start_time': _start_time,
                            'scheduled_start_time': scheduled_start_time,
                            'wave_name': _wave_name,
                        }
                        for generator in tt_generators:
                            generator.add_participant(tt_event_id, _wave_id, _wave_name, formatted_tt_participant)
            else:
                print(f"No TT competition events and waves found for {name or date}.", file=sys.stderr)


        category_bib_ranges = {}
        # Convert bibs per category into summarized ranges
        for category, bibs in category_bibs.items():
            clean_bibs = [b for b in bibs if isinstance(b, int)]
            if clean_bibs:
                category_bib_ranges[category] = get_ranges(clean_bibs)
            else:
                category_bib_ranges[category] = "N/A"

        print("Category Bib Ranges:", category_bib_ranges, file=sys.stderr)


        # Save the generated file
        active_generators = generators if has_mass_start_events else []
        active_tt_generators = tt_generators if has_tt_events else []

        print(f"{len(active_generators)} active generators: {active_generators}", file=sys.stderr)
        for generator in active_generators:
            output_filename = generator.save(category_bib_ranges=category_bib_ranges)
        print(f"{len(active_tt_generators)} active TT generators: {active_tt_generators}", file=sys.stderr)
        for generator in active_tt_generators:
            output_filename = generator.save(category_bib_ranges=category_bib_ranges)
        #print(f"File generated: {output_filename}", file=sys.stderr)

    except psycopg2.DatabaseError as error:
        print(f"Database error: {error}", file=sys.stderr)
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
    #finally:
    #    cur.close()
    #    conn.close()


epilog = """
The startlist script is used to connect to a RaceDB database and quickly 
generate the required files to run a race with CrossMgr.

E.g. startlist --host localhost --date 2022-01-01 --crossmgr --html

These are the same files that are generated by the RaceDB web interface for use
with CrossMgr:
    2024-10-27-Cyclo_Cross_1.xlsx
    2024-10-27-Cyclo_Cross_2.xlsx
    2024-10-27-Cyclo_Cross_3.xlsx
    2024-10-27-Cyclo_Cross_4.xlsx
    2024-10-27-Cyclo_Cross_5.xlsx

This is a static HTML page that can be put onto the results website for
the race officials to access with a smartphone:
    2024-10-27-Cyclo_Cross-startlist.html

The environment variables RACEDB_USERNAME and RACEDB_PASSWORD will be used
if set.


"""
def main():
    parser = argparse.ArgumentParser(
            description="Download CrossMgr and Start lists for a RaceDB competition.", 
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=epilog)
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('--host', type=str, default='localhost', help='database host')
    parser.add_argument('--date', type=str, help='Start date of the competition in YYYY-MM-DD format.')
    parser.add_argument('--name', type=str, help='Name of the competition.')
    parser.add_argument('--xlsx', action='store_true', help='Generate XLSX Start List')
    parser.add_argument('--html', action='store_true', help='Generate HTML Start List')
    parser.add_argument('--pdf', action='store_true', help='Generate PDF Start List')
    parser.add_argument('--audit', action='store_true', help='Generate audit xlsx, pre-reg vs day-of registration.')
    parser.add_argument('--info', action='store_true', help='Summary of Events/Waves/Categories')
    parser.add_argument('--bibs', action='store_true', help='Summary of Number Set Usage (aka bibs)')
    parser.add_argument('--lap_abc', action='store_true', help='Show A/B/C in lapboard.')
    tt_detail_group = parser.add_mutually_exclusive_group()
    tt_detail_group.add_argument('--laps', action='store_true', help='Add TT wave laps as a final PDF column.')
    tt_detail_group.add_argument('--km', action='store_true', help='Add rounded TT wave distance as a final PDF column.')
    parser.add_argument('--landscape', action='store_true', help='Generate landscape PDF.')
    parser.add_argument('--final', action='store_true',
                        help='Mark PDFs as final (disable preliminary watermark).')
    parser.add_argument('--callups', type=str, help='XLSX series results file for mass-start callup ordering.')
    parser.add_argument('--stderr', "--debug", action='store_true', help='Enable stderr output.')
    parser.add_argument("--stderrdup", action='store_true', help='Send stderr to stdout.')
    parser.add_argument("--crossmgr", "--cm", required=False, help="The RaceDB host for downloading files.")
    parser.add_argument('--series_all', action='store_true',
                        help='Force Series TRUE for every row in CrossMgr category worksheets.')

    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])

    formatted_date = format_date(args.date) if args.date else None

    output_formats = []
    if args.xlsx:
        output_formats.append('xlsx')
    if args.html:
        output_formats.append('html')
    if args.crossmgr:
        output_formats.append('cm')
    if args.audit:
        output_formats.append('audit')
    if args.info:
        output_formats.append('info')
    if args.bibs:
        output_formats.append('bibs')
    if args.pdf:
        output_formats.append('pdf')

    landscape = args.landscape
    final = args.final
    lap_abc = args.lap_abc
    tt_detail_column = "laps" if args.laps else "km" if args.km else None

    with AutoPagerEx(stderr=args.stderr, stderrdup=args.stderrdup, line_buffering=autopage.line_buffer_from_input()) as (sys.stdout, sys.stderr):
        try:
            export_startlists(args.host, date=formatted_date, name=args.name, output_formats=output_formats,
                              racedb_host=args.crossmgr, landscape=landscape, final=final, lap_abc=lap_abc,
                              tt_detail_column=tt_detail_column, callups_filename=args.callups,
                              series_all=args.series_all)
        except Exception as e:
            print(f"An error occurred: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)

if __name__ == "__main__":
    main()
