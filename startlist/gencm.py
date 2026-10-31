
import sys
import os
import requests


import openpyxl
from datetime import datetime
from urllib.parse import urljoin
from .filename import sanitize_filename_part

class GenCM:
    def __init__(self, racedb_host, date, competition_id, competition_name, series_all=False):
        print('GenCM:', racedb_host, date, competition_id, competition_name, file=sys.stderr)
        self.racedb_host = racedb_host
        self.date = date
        self.competition_id = competition_id
        self.competition_name = competition_name
        self.series_all = series_all
        self.events = {}

    def add_event(self, event_id, event_name, event_start_time):
        print(f"Adding event {event_id} {event_name} to competition", file=sys.stderr)
        self.event_name = event_name
        self.events[event_name] = event_id

    def add_wave(self, event_id, wave_id, wave_name, start_offset, distance, laps, minutes, categories, ):
        pass

    def add_participant(self, event_id, wave_id, wave_name, participant_data):
        pass

    def repair_properties(self, file_name):
        """Repair RaceDB exports missing the new minimum-lap-time value."""
        # TEMPORARY: remove this workaround and its save() call when RaceDB
        # fixes the missing Min Possible Lap Time value in its XLSX export.
        workbook = openpyxl.load_workbook(file_name)
        try:
            if '--CrossMgr-Properties' not in workbook.sheetnames:
                return
            worksheet = workbook['--CrossMgr-Properties']
            headers = [cell.value for cell in worksheet[1]]
            values = [cell.value for cell in worksheet[2]]
            # openpyxl pads rows to the worksheet width. Trim trailing blanks
            # before comparing; legitimate optional blanks also shorten rows,
            # so a length mismatch alone must never trigger this repair.
            while headers and headers[-1] is None:
                headers.pop()
            while values and values[-1] is None:
                values.pop()
            if len(headers) == len(values):
                return
            if 'Min Possible Lap Time' not in headers or 'Win and Out' not in headers:
                return
            minimum_col = headers.index('Min Possible Lap Time') + 1
            win_col = headers.index('Win and Out') + 1
            # In the broken export, Use SFTP occupies the minimum-lap-time
            # cell, and the Win and Out boolean is one column too far left.
            if not (
                headers[minimum_col - 2] == 'RFID Option'
                and headers[minimum_col] == 'Use SFTP'
                and type(worksheet.cell(2, minimum_col).value) is bool
                and type(worksheet.cell(2, win_col - 1).value) is bool
                and isinstance(worksheet.cell(2, win_col).value, str)
                and worksheet.cell(2, win_col).value.strip().upper() not in {'', 'TRUE', 'FALSE'}
            ):
                return
            for col in range(len(headers), minimum_col, -1):
                worksheet.cell(2, col).value = worksheet.cell(2, col - 1).value
            worksheet.cell(2, minimum_col).value = None
            workbook.save(file_name)
            print(f'Repaired shifted CrossMgr properties in {file_name}', file=sys.stderr)
        finally:
            workbook.close()

    def force_series_all(self, file_name):
        workbook = openpyxl.load_workbook(file_name)
        sheet_name = '--CrossMgr-Categories'
        if sheet_name not in workbook.sheetnames:
            print(f"Series all requested but {sheet_name} not found in {file_name}", file=sys.stderr)
            return

        worksheet = workbook[sheet_name]
        series_col = None
        for cell in worksheet[1]:
            if cell.value == 'Series':
                series_col = cell.column
                break

        if series_col is None:
            print(f"Series all requested but Series column not found in {file_name}", file=sys.stderr)
            return

        for row in range(2, worksheet.max_row + 1):
            worksheet.cell(row=row, column=series_col, value=True)

        workbook.save(file_name)
        print(f"Forced Series TRUE in {file_name}", file=sys.stderr)

    def save(self, category_bib_ranges=None):
        #for i, event_id in enumerate(self.events, 1):
        for i, (event_name, event_id) in enumerate(self.events.items()):
            print(f"Downloading event {event_id}...", file=sys.stderr)
            url = urljoin(f"https://{self.racedb_host}/RaceDB/Competitions/CompetitionDashboard/{self.competition_id}/EventMassStartCrossMgr/", 
                          str(event_id))
            print('Download URL:', url, file=sys.stderr)
            response = requests.get(url)
            if response.status_code == 200:
                #file_name = f"{self.date}-{self.competition_name.replace(' ', '_')}_{i}.xlsx"
                #file_name = f"{self.date}-{event_name.replace(' ', '_')}.xlsx"
                #file_name = f"{self.date}-{self.competition_name.replace(' ', '_')}_{event_name.replace('/','_').replace(' ','_')}-r{i}.xlsx"
                competition_slug = sanitize_filename_part(self.competition_name, compact=True)
                event_slug = sanitize_filename_part(event_name)
                file_name = f"{self.date}-{competition_slug}-{event_slug}.xlsx"
                with open(file_name, "wb") as file:
                    file.write(response.content)
                self.repair_properties(file_name)
                if self.series_all:
                    self.force_series_all(file_name)
                print(f"Downloaded event {event_id} as {file_name}", file=sys.stdout)
            else:
                print(f"Failed to download event {self.event_id} from {url}", file=sys.stdout)
