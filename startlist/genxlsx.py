

import openpyxl
from datetime import datetime

class GenXLSX:
    def __init__(self, competition_name):
        self.competition_name = competition_name
        self.workbook = openpyxl.Workbook()
        self.current_sheet = self.workbook.active
        self.current_sheet.title = "Competition Summary"
        self.row = 1
        self.col = 1

    def add_event(self, event_id, event_name, event_start_time):
        self.current_sheet.append([f"{event_name} {event_start_time}"])
        self.row += 1

    def add_wave(self, wave_name, start_offset, distance, laps, minutes, categories, ):
        self.current_sheet.append([f"Wave: {wave_name}, Start Offset: {start_offset}"])
        self.row += 1

    def add_participant(self, dummy, wave_name, participant_data):
        # Convert tuple to list before concatenating
        participant_data = list(participant_data)
        self.current_sheet.append([wave_name] + participant_data)
        self.row += 1

    def save(self, filename="startlists.xlsx"):
        self.workbook.save(filename)
        return filename

