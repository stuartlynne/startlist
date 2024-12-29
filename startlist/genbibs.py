
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

class GenBibs:
    def __init__(self, racedb_host, date, competition_id, competition_name, ranges, bibs, ):
        print('GenBibs:', racedb_host, date, competition_id, competition_name, file=sys.stderr)
        self.racedb_host = racedb_host
        self.date = date
        self.competition_id = competition_id
        self.competition_name = competition_name
        self.events = []
        self.ranges = ranges
        self.bibs = bibs
        
    def parse_ranges(self, range_string):
        """Parses a range string like '100-199,400-410' into a list of ranges."""
        ranges = []
        for part in range_string.split(','):
            start, end = map(int, part.split('-'))
            ranges.append((start, end))
        return ranges

    def is_in_ranges(self, number, ranges):
        """Checks if a number falls within any of the given ranges."""
        return any(start <= number <= end for start, end in ranges)

    def count_bibs(self, categories, bib_numbers):
        """Counts bibs and lost bibs by category."""
        category_ranges = {cat: self.parse_ranges(ranges) for cat, ranges in categories}
        category_counts = defaultdict(lambda: {'inuse': 0, 'lost': 0, 'available': 0, 'total': 0, 'warning': ''})

        for category, ranges in category_ranges.items():
            # Calculate total possible bibs in each category
            total_possible = sum(end - start + 1 for start, end in ranges)
            category_counts[category]['available'] = total_possible
            category_counts[category]['total'] = total_possible


        for bib, lost_date in bib_numbers:
            for category, ranges in category_ranges.items():
                if self.is_in_ranges(bib, ranges):
                    category_counts[category]['inuse'] += 1
                    if lost_date is not None:
                        category_counts[category]['lost'] += 1
                    category_counts[category]['available'] -= 1
                    if category_counts[category]['available'] < category_counts[category]['total'] * 0.2:
                        category_counts[category]['warning'] = 'Low'

        return category_counts

    def get_primary_range_start(self, ranges):
        """Gets the starting number of the first range."""
        return ranges[0][0] if ranges else float('inf')


    def add_event(self, event_id, event_name, event_start_time):
        self.events.append(event_id)

    def add_wave(self, event_id, wave_id, wave_name, start_offset, distance, laps, minutes, categories, ):
        pass

    def add_participant(self, event_id, wave_id, wave_name, participant, ):
        pass

    def save(self, ):

        #print('Ranges:', self.ranges, file=sys.stderr)
        # Process the data
        categories = [(r[1], r[4]) for r in self.ranges]
        counts = self.count_bibs(categories, self.bibs)

        # Sort the categories by the first range start
        sorted_categories = sorted(categories, key=lambda cat: self.get_primary_range_start(self.parse_ranges(cat[1])))

        def print_bib_data(category, numbers, total, inuse, lost, available, warning):
            print("%-20s | %-20s | %5s | %5s | %5s | %5s | %s" % (category, numbers, total, inuse, lost, available, warning))

        # Output the results
        print_bib_data('Category', 'Range', 'Total', 'InUse', 'Lost', 'Avail', '')
        print_bib_data('-' * 20, '-' * 20, '-' * 5, '-' * 5, '-' * 5, '-' * 5, '')
        for category, range_string in sorted_categories:
            data = counts[category]
            print_bib_data(category, range_string, str(data['total']), str(data['inuse']), str(data['lost']), 
                           str(data['available']), str(data['warning']),)
        print()
