import sys
from datetime import time
import pandas as pd

from .filename import sanitize_filename_part


def exact_ranges(bib_list):
    if not bib_list:
        return None

    bibs = sorted(set(bib_list))
    ranges = []
    start = bibs[0]
    end = start

    for bib in bibs[1:]:
        if bib == end + 1:
            end = bib
        else:
            ranges.append(f"{start}" if start == end else f"{start}-{end}")
            start = end = bib

    ranges.append(f"{start}" if start == end else f"{start}-{end}")
    return ",".join(ranges)


def seconds_to_time(value):
    total_seconds = int(round(value or 0))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return time(hour=hours % 24, minute=minutes, second=seconds)


class GenTTXLSX:
    def __init__(self, date, competition_name, competition_long_name, organizer="", city="", state_prov="", country=""):
        print('GenTTXLSX:', date, competition_name, competition_long_name, file=sys.stderr)
        self.date = date
        self.competition_name = competition_name
        self.competition_long_name = competition_long_name
        self.organizer = organizer
        self.city = city
        self.state_prov = state_prov
        self.country = country
        self.events = {}

    def add_event(self, event_id, event_name, event_start_time):
        self.events[event_id] = {
            'event_name': event_name,
            'event_start_time': event_start_time,
            'waves': {},
            'participants': [],
        }
        self.event_id = event_id

    def add_wave(self, event_id, wave_id, wave_name, start_offset, distance, laps, minutes, categories):
        self.events[event_id]['waves'][wave_id] = {
            'wave_name': wave_name,
            'start_offset': start_offset,
            'distance': distance,
            'laps': laps,
            'minutes': minutes,
            'categories': categories,
        }

    def add_participant(self, event_id, wave_id, wave_name, participant_data):
        participant_data["wave_id"] = wave_id
        participant_data["wave_name"] = wave_name
        self.events[self.event_id]['participants'].append(participant_data)

    def save(self, category_bib_ranges=None):
        for event_id, event in self.events.items():
            event_name = sanitize_filename_part(event["event_name"])
            event_start_time = event["event_start_time"].strftime("%H%M")
            competition_slug = sanitize_filename_part(self.competition_name, compact=True)
            # filename = f"{self.date}-{competition_slug}-{event_name}.xlsx"
            filename = f"{self.date}-{competition_slug}-{event_start_time}.xlsx"
            writer = pd.ExcelWriter(filename, engine='xlsxwriter')
            workbook = writer.book

            header_format = workbook.add_format({'bold': True})
            time_format = workbook.add_format({'num_format': 'hh:mm:ss'})

            registration_rows = []
            for participant in sorted(event['participants'], key=lambda p: (p.get('start_sequence', 999999), p.get('bib') or 0)):
                dob = participant.get('date_of_birth')
                registration_rows.append({
                    "StartTime": seconds_to_time(participant.get('start_time')),
                    "Bib#": participant.get("bib"),
                    "LastName": participant.get("last_name", ""),
                    "FirstName": participant.get("first_name", ""),
                    "Team": participant.get("team_name", ""),
                    "City": participant.get("city", ""),
                    "StateProv": participant.get("state_prov", ""),
                    "Category": participant.get("category_code", ""),
                    "Age": "",
                    "Gender": participant.get("gender", ""),
                    "License": participant.get("license_code", ""),
                    "NatCode": participant.get("nation_code", ""),
                    "UCI ID": participant.get("uci_id", ""),
                    "Tag": participant.get("tag", ""),
                    "Tag2": participant.get("tag2", ""),
                })
                if dob and event['event_start_time']:
                    age = event['event_start_time'].year - dob.year
                    registration_rows[-1]["Age"] = age

            registration_df = pd.DataFrame(registration_rows)
            registration_df.to_excel(writer, sheet_name='Registration', index=False)
            registration_ws = writer.sheets['Registration']
            for col_num, value in enumerate(registration_df.columns.values):
                registration_ws.write(0, col_num, value, header_format)
            registration_ws.set_column(0, 0, 12, time_format)
            registration_ws.set_column(1, 1, 8)
            registration_ws.set_column(2, 3, 18)
            registration_ws.set_column(4, 4, 28)
            registration_ws.set_column(5, 6, 18)
            registration_ws.set_column(7, 7, 20)
            registration_ws.set_column(8, 8, 8)
            registration_ws.set_column(9, 9, 10)
            registration_ws.set_column(10, 14, 18)

            category_rows = []
            for wave_id, wave in event['waves'].items():
                wave_participants = [
                    p for p in event['participants']
                    if p.get('wave_id') == wave_id
                ]
                category_groups = {}
                for participant in wave_participants:
                    key = (participant.get('category_code', ''), participant.get('gender', 'Open'))
                    category_groups.setdefault(key, []).append(participant.get('bib'))

                if not category_groups and not event['participants']:
                    for category in wave.get("categories", []):
                        if len(category) >= 3:
                            _, category_name, category_gender = category[:3]
                            gender = ['Men', 'Women', 'Open'][category_gender]
                        elif len(category) >= 2:
                            _, category_name = category[:2]
                            gender = 'Open'
                        else:
                            continue
                        category_groups.setdefault((category_name, gender), [])

                for (category_name, gender), bibs in sorted(category_groups.items()):
                    clean_bibs = [b for b in bibs if isinstance(b, int)]
                    category_rows.append({
                        "Category Type": "Wave",
                        "Name": category_name,
                        "Gender": gender,
                        "Numbers": exact_ranges(clean_bibs),
                        "Start Offset": None,
                        "Race Laps": wave["laps"],
                        "Race Distance": wave["distance"],
                        "Race Minutes": None,
                        "Publish": True,
                        "Upload": True,
                        "Series": True,
                    })

            categories_df = pd.DataFrame(category_rows, columns=[
                "Category Type", "Name", "Gender", "Numbers", "Start Offset", "Race Laps",
                "Race Distance", "Race Minutes", "Publish", "Upload", "Series"
            ])
            categories_df.to_excel(writer, sheet_name='--CrossMgr-Categories', index=False)
            categories_ws = writer.sheets['--CrossMgr-Categories']
            for col_num, value in enumerate(categories_df.columns.values):
                categories_ws.write(0, col_num, value, header_format)
            categories_ws.set_column(0, 10, 18)

            properties_df = pd.DataFrame([{
                "Event Name": f"{self.competition_name}-{event_name}",
                "Event Organizer": self.organizer,
                "Event City": self.city,
                "Event StateProv": self.state_prov,
                "Event Country": self.country,
                "Event Date": self.date,
                "Scheduled Start": event["event_start_time"].strftime("%H:%M"),
                "TimeZone": "America/Vancouver",
                "Race Number": 2,
                "Race Discipline": "Road",
                "Enable RFID": True,
                "Distance Unit": "km",
                "Time Trial": True,
                "RFID Option": 1,
                "Use SFTP": False,
                "FTP Host": None,
                "FTP User": None,
                "FTP Password": None,
                "FTP Path": None,
                "FTP Upload During Race": True,
                "GATrackingID": None,
                "Road Race Finish Times": False,
                "No Data DNS": True,
                "Win and Out": False,
                "Event Long Name": f"{self.competition_name}-{event_name}",
                "Email": None,
                "Google Maps API Key": None,
            }])
            properties_df.to_excel(writer, sheet_name='--CrossMgr-Properties', index=False)
            properties_ws = writer.sheets['--CrossMgr-Properties']
            for col_num, value in enumerate(properties_df.columns.values):
                properties_ws.write(0, col_num, value, header_format)
            properties_ws.set_column(0, len(properties_df.columns) - 1, 18)

            writer.close()
            print(f"Generated TT XLSX: {filename}")

        return "TT XLSX files generated."
