
import sys
import os
import requests


import openpyxl
from datetime import datetime
from urllib.parse import urljoin

class GenCM:
    def __init__(self, racedb_host, date, competition_id, competition_name):
        self.racedb_host = racedb_host
        self.date = date
        self.competition_id = competition_id
        self.competition_name = competition_name
        self.events = []

    def add_event(self, event_id, event_name, event_start_time):
        self.events.append(event_id)

    def add_wave(self, wave_name, start_offset, distance, laps, minutes, categories, ):
        pass

    def add_participant(self, dummy, wave_name, participant_data):
        pass

    def save(self, ):
        for i, event_id in enumerate(self.events, 1):
            url = urljoin(f"https://{self.racedb_host}/RaceDB/Competitions/CompetitionDashboard/{self.competition_id}/EventMassStartCrossMgr/", 
                          str(event_id))
            print('Download URL:', url, file=sys.stderr)
            response = requests.get(url)
            if response.status_code == 200:
                file_name = f"{self.date}-{self.competition_name.replace(' ', '_')}_{i}.xlsx"
                with open(file_name, "wb") as file:
                    file.write(response.content)
                print(f"Downloaded event {event_id} as {file_name}", file=sys.stderr)
            else:
                print(f"Failed to download event {self.event_id} from {url}", file=sys.stderr)


