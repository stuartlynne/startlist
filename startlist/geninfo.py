
import sys
import os
import requests
from collections import defaultdict


import openpyxl
from datetime import datetime
import openpyxl
import csv
from operator import itemgetter
from urllib.parse import urljoin

class GenInfo:
    def __init__(self, racedb_host, date, competition_id, competition_name, ranges, bibs, ):
        #print('GenInfo:', racedb_host, date, competition_id, competition_name, file=sys.stderr)

        self.events = {}
        self.waves = {}

    def add_event(self, event_id, event_name, event_start_time):
        #print(f"Adding event {event_name} to competition", file=sys.stderr)
        self.events[event_id] = {
            'event_name': event_name,
            'event_start_time': event_start_time,
        }

    def add_wave(self, event_id, wave_id, wave_name, start_offset, distance, laps, minutes, categories, ):
        #print(f"Adding wave {wave_id} {wave_name} to event {self.events[event_id].get('event_name')}", file=sys.stderr)
        self.waves[wave_id] = {
            'event_id': event_id,
            'wave_name': wave_name,
            'start_offset': start_offset,
            'distance': distance,
            'laps': laps,
            'minutes': minutes,
            'categories': categories,
            'participants': 0,
        }
        #print(f"Waves {self.waves}", file=sys.stderr)
        pass

    def add_participant(self, event_id, wave_id, wave_name, participant, ):
        #print(f"wave_id: {wave_id}", file=sys.stderr)
        #print(f"Adding participant to wave {wave_id} {self.waves[wave_id].get('wave_name')}", file=sys.stderr)
        self.waves[wave_id]['participants'] += 1
        pass

    def save(self, category_bib_ranges=None):
        print("Events and Waves:")
        #def print_bib_data(category, numbers, total, inuse, lost, available, warning):
        #    print("%-20s | %-20s | %5s | %5s | %5s | %5s | %s" % (category, numbers, total, inuse, lost, available, warning))

        def print_wave_info(event_name, wave_name, start_offset, distance, laps, minutes, participants):
            print("%-12s | %-12s | %5s | %5s | %5s | %5s | %s" % (event_name, wave_name, start_offset, distance, laps, minutes, participants))
            
        print_wave_info("Event", "Wave Name", "Start", "Dist", "Laps", "(m)", "#")
        for event_id, event in self.events.items():
            print_wave_info('-' * 12, '-' * 12, '-' * 5, '-' * 5, '-' * 5, '-' * 5, '-' * 5, )
            print_wave_info(event['event_name'], '', '', '', '', '', '')
            for wave_id, wave in self.waves.items():
                if wave['event_id'] == event_id:
                    print_wave_info('', wave['wave_name'], wave['start_offset'], wave['distance'], wave['laps'], wave['minutes'], wave['participants'])
        print_wave_info('-' * 12, '-' * 12, '-' * 5, '-' * 5, '-' * 5, '-' * 5, '-' * 5, )
