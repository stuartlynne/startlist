import sys
import pandas as pd
import os
import sys

class GenXLSX:
    def __init__(self, date, competition_name, competition_long_name):
        print('GenXLSX:', date, competition_name, competition_long_name, file=sys.stderr)
        self.date = date
        self.competition_name = competition_name
        self.competition_long_name = competition_long_name
        self.events = {}

    def add_event(self, event_id, event_name, event_start_time):
        """ Add an event to the competition. """
        print(f"GenXLSX: Adding event {event_id} {event_name} to competition", file=sys.stdout)
        self.events[event_id] = {
            'event_name': event_name,
            'event_start_time': event_start_time,
            'waves': {},
        }
        self.event_id = event_id

    def add_wave(self, event_id, wave_id, wave_name, start_offset, distance, laps, minutes, categories):
        """ Add a wave to an event. """
        print(f"GenXLSX: Adding wave: {event_id} {wave_id} {wave_name}", file=sys.stderr)
        self.events[event_id]['waves'][wave_id] = {
            'wave_name': wave_name,
            'start_offset': start_offset,
            'distance': distance,
            'laps': laps,
            'minutes': minutes,
            'categories': categories,
            'participants': [],
        }

    def add_participant(self, event_id, wave_id, wave_name, participant_data):
        """ Add a participant to a wave. """
        print(f"GenXLSX: Adding participant to wave {wave_id}, Bib: {participant_data.get('bib', 'N/A')}", file=sys.stderr)
        print(participant_data, file=sys.stderr)

        cat_gender = f"({['Men', 'Women', 'Open'][participant_data['category_gender']]})"
        mapped_participant = {
            "Category": f"{participant_data['category_code']} {cat_gender}",
            "Bib": participant_data.get("bib", "N/A"),
            "LastName": participant_data.get("last_name", "N/A"),
            "FirstName": participant_data.get("first_name", "N/A"),
            "Team": participant_data.get("team_name", "N/A"),
            #"License": participant_data.get("license_code", "N/A"),
            "UCI ID": participant_data.get("uci_id", "N/A"),
            "License Checked": 'Y' if participant_data.get("license_checked", False) else '',
            "Confirmed": 'Y' if participant_data.get("confirmed", False) else '',
            "Note": ""
        }
        self.events[self.event_id]['waves'][wave_id]['participants'].append(mapped_participant)

    def save(self):
        """ Saves each event as a separate XLSX file with column widths. """
        for event_id, event in self.events.items():
            event_name = event["event_name"].replace(" ", "_").replace(':','').replace('_AM','').replace('_PM','')
            filename = f"{self.date}-{self.competition_name.replace(' ','_')}-{event_name}-startlist.xlsx"
            writer = pd.ExcelWriter(filename, engine='xlsxwriter')
            header_format = writer.book.add_format({'text_wrap': True, 'bold': True, 'font_size': 12})
            team_format = writer.book.add_format({'text_wrap': True, 'font_size': 12})
            center_format = writer.book.add_format({'align': 'center', 'valign': 'vcenter', 'font_size': 12})
            print(f"GenPDF.save: filename: {filename}", file=sys.stderr)
            
            for wave_id, wave in event["waves"].items():
                print(f"Wave {wave['wave_name']} has {len(wave['participants'])} participants", file=sys.stderr)
                
                if not wave['participants']:
                    print(f"Warning: No participants found for wave {wave['wave_name']}", file=sys.stderr)
                    continue  # Skip empty sheets

                df = pd.DataFrame(wave['participants'], columns=[
                    "Category", "Bib", "LastName", "FirstName", "Team", #"License", 
                    "UCI ID", "License Checked", "Confirmed", 
                ])
                df.sort_values(by="Bib", inplace=True)
                df.to_excel(writer, sheet_name=wave["wave_name"], index=False)
                
                # Set column widths
                worksheet = writer.sheets[wave["wave_name"]]
                column_widths = {
                    "Category": 15,
                    "Bib": 10,
                    "LastName": 20,
                    "FirstName": 20,
                    "Team": 30,
                    #"License": 15,
                    #"NatCode": 10,
                    "UCI ID": 15,
                    "License Checked": 12,
                    "Confirmed": 12,
                    "Note": 25
                }
                for col_num, (col_name, width) in enumerate(column_widths.items()):
                    worksheet.set_column(col_num, col_num, width)

                # Apply header format with text wrap
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)

                # Apply text wrap to the "Team" column
                team_col_index = df.columns.get_loc("Team")
                worksheet.set_column(team_col_index, team_col_index, 30, team_format)  # Adjust width as needed

                # Apply center alignment to "License Checked" and "Confirmed"
                for col_name in ["Bib", "License Checked", "Confirmed"]:
                    col_index = df.columns.get_loc(col_name)
                    worksheet.set_column(col_index, col_index, 15, center_format)
            
            writer.close()
            print(f"Generated XLSX: {filename}")
        
        return "XLSX files generated for each event."
