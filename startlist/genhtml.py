import sys
from yattag import Doc, indent
from datetime import datetime
from collections import Counter
from .genright import GenRight
from .genleft import GenLeft

from .js import js
from .bib import bib
from .cookies import cookies
from .notes import notes
from .reload import reload
from .toggle import toggle

from .css import css

class GenHTML:

    def clean_id(self, id):
        return id.replace('-','_').replace(' ', '_').replace('.','').replace('event_','').lower()

    #def event_selection_td_id(self, event_id):
    #    return self.clean_id(f"select_{event_id}_td")


    def event_info_cell_id(self, event_id):
        return self.clean_id(f"EWS_{event_id}")

    def wave_selection_tr_id(self, event_id, wave_name, ):
        return self.clean_id(f"WST_{event_id}_{wave_name}")

    def wave_table_id(self, event_id, wave_name):
        return self.clean_id(f"{event_id}_{wave_name}")

    def wave_table_all_id(self, event_id):
        return self.clean_id(f"{event_id}_wave_all")

    def event_info_id(self, event_id):
        return self.clean_id(f"{event_id}-info")

    def wave_table_row_id(self, event_id, wave_name, bib):
        return self.clean_id(f"wtr_{event_id}_{wave_name}_{bib}")

    def wave_table_note_id(self, event_id, wave_name, bib):
        return self.clean_id(f"wtn_{event_id}{wave_name}_{bib}")

    def wave_table_input_n_id(self, event_id, wave_name, bib):
        return self.clean_id(f"wti_{event_id}{wave_name}_{bib}")
         
    def wave_table_input_all_id(self, event_id, bib):
        return self.clean_id(f"wti_{event_id}_{bib}")
         

    def __init__(self, competition_name, competition_date):
        self.competition_name = competition_name
        self.competition_date = competition_date
        self.doc, self.tag, self.text = Doc().tagtext()
        
        self.left = GenLeft(self, self.doc, self.tag, self.text)
        self.right = GenRight(self, self.doc, self.tag, self.text)

        self.output_filename = f"{self.competition_date}-{self.competition_name.replace(' ', '_')}-startlist.html"

        # Store event, wave, and participant data
        self.data = {}

        # Initialize the HTML structure
        self.doc.asis('<!DOCTYPE html>')
        # Event information and search table
        with self.tag('html'):
            with self.tag('head'):
                with self.tag('link',
                       rel="stylesheet",
                       href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css",
                       integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh",
                       crossorigin="anonymous",
                       ): pass


                with self.doc.tag('link', 
                      rel="stylesheet", 
                      href="https://cdnjs.cloudflare.com/ajax/libs/jquery.tablesorter/2.31.3/css/theme.blue.min.css",
                                  ): pass

                self.doc.asis('<meta charset="utf-8">')
                self.doc.asis('<meta name="viewport" content="width=device-width, initial-scale=1">')
                
                self.doc.asis('<meta http-equiv="cache-control" content="no-cache, no-store, must-revalidate">')
                self.doc.asis('<meta http-equiv="pragma" content="no-cache">')
                self.doc.asis('<meta http-equiv="expires" content="0">')


                self.doc.asis('<title>Startlists</title>')

                with self.tag('script', src="https://code.jquery.com/jquery-3.6.0.min.js"): pass
                with self.tag('script', src="https://cdnjs.cloudflare.com/ajax/libs/jquery.tablesorter/2.32.0/js/jquery.tablesorter.min.js"): pass
                with self.tag('script', src="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/js/bootstrap.min.js"): pass


                with self.tag('style'):
                    self.doc.asis('.selection-table { padding: 2px; }')


                    if False:
                        self.doc.asis('.fs-s { font-size: .6em; }')
                        self.doc.asis('.fs-m { font-size: .8em; }')
                        self.doc.asis('.fs-l { font-size: 1.2em; }')
                        self.doc.asis('.fs-xl { font-size: 1.4em; }')
                        self.doc.asis('.fs-20px { font-size: 20px; }')
                    else:
                        self.doc.asis('.fs-s { font-size: .7em; }')
                        self.doc.asis('.fs-m { font-size: .9em; }')
                        self.doc.asis('.fs-l { font-size: 1.3em; }')
                        self.doc.asis('.fs-xl { font-size: 1.4em; }')
                        self.doc.asis('.fs-20px { font-size: 20px; }')

                    self.doc.asis('.left {width: 100%; background-color: white}')
                    self.doc.asis('.right {width: 100%; background-color: white}')

                    self.doc.asis(css)


                # Link to the external JavaScript file for sorting and table toggling
                #self.doc.asis('<script src="startlist.js"></script>')
                #self.doc.asis(js)
                with self.tag('script'):
                    self.doc.asis(js)
                    self.doc.asis(bib)
                    self.doc.asis(cookies)
                    self.doc.asis(notes)
                    self.doc.asis(reload)
                    self.doc.asis(toggle)

                #self.doc.asis('.tr.highlight { background-color: #f1f1f1; }')
                #self.doc.asis('.tr.highlight { background-color: yellow; }')



    def add_event(self, event_name, event_start_time):
        print(f"Adding event: {event_name}", file=sys.stderr)
        #event_section_id = f"event-{event_name.replace(' ', '_')}"
        event_section_id = f"event-{event_name.replace('Race #', '')}."
        self.data[event_section_id] = {
            'name': event_name.replace('Race ', ''),  # Remove "Race " from event name
            'start_time': event_start_time,
            'waves': {}
        }

    def add_wave(self, wave_name, start_offset, distance, laps, minutes, categories, ):
        event_section_id = list(self.data.keys())[-1]  # Get the last added event
        if wave_name not in self.data[event_section_id]['waves']:
            self.data[event_section_id]['waves'][wave_name] = {
                'start_offset': int(start_offset),  # Convert float to int
                'distance': int(distance) if distance else 0,
                'laps': int(laps) if laps else 0,
                'minutes': int(minutes) if minutes else 0,
                'categories': categories,
                'participants': [],
            }

    def add_participant(self, dummy, wave_name, participant_data):
        event_section_id = list(self.data.keys())[-1]  # Get the last added event
        if wave_name in self.data[event_section_id]['waves']:
            self.data[event_section_id]['waves'][wave_name]['participants'].append(participant_data)



    def generate_html(self):
        with self.tag('div', klass='container'):
            self.left.generate_left()
            self.right.generate_right()

    def save(self):
        self.generate_html()
        html_output = indent(self.doc.getvalue())
        #output_filename = f'startlists_{self.competition_name.replace(" ", "_")}.html'
        with open(self.output_filename, 'w') as f:
            f.write(html_output)
        return self.output_filename
