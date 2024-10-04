import sys
from yattag import Doc, indent
from datetime import datetime
from collections import Counter
#from .js import js, css


class GenRight:

    def __init__(self, parent, doc, tag, text):
        self.parent = parent
        self.doc = doc
        self.tag = tag
        self.text = text

    def _generate_wave_header(self, event, header1=None, header2=None):
        #if header1:
        #    self.text(header1)
        if header1:
            with self.tag('tr', klass='participant-tr-15',):
                with self.tag('th', klass='thtd fs-m', style="text-align: left;", colspan=3 if event else 3, ):
                    self.text(header1)
                if header2:
                    with self.tag('th', klass='thtd fs-s', style="text-align: left;", colspan=2 if event else 1, ):
                        self.text(header2)

        with self.tag('tr', klass="participant-tr-15", ):
            #if event:
            #    with self.tag('th', klass='thtd', style="text-align: right; width:.m", ):
            #        self.text('')

            with self.tag('th', klass='thtd', colspan=3 if event else 2, ):
                self.text('Bib')

            with self.tag('th', klass='thtd', 
                            style="text-align: left; vertical-align: middle; margin-left: %s; " % ('10px' if event else '1px'), ):
                self.text('Name')

            with self.tag('th', klass='thtd', style="text-align: left; vertical-align: middle;", ):
                self.text('Team')

            with self.tag('th', klass='thtd', style="text-align: left; ", ):
                self.text('Category')


    def _generate_wave_row(self, event, event_id, wave_name, participant):

        bib = str(participant['bib']) if participant['bib'] else ''
        all == bool(wave_name)

        wave_table_row_id = self.parent.wave_table_row_id(event_id, wave_name if event else '', bib)
        wave_table_note_id = self.parent.wave_table_note_id(event_id, wave_name if event else '', bib)

        wave_table_input_n_id = self.parent.wave_table_input_n_id(event_id, wave_name, bib)
        wave_table_input_all_id = self.parent.wave_table_input_all_id(event_id, bib)

        with self.tag('tr', klass='participant-tr fs-s', id=wave_table_row_id,
                onclick=f"TB('{bib}', '{wave_table_note_id}')", ):
            if event:
                with self.tag('td', klass='thtd-28 fs-xl', ):
                    self.doc.asis('<b>')
                    self.text(wave_name if wave_name else '_')

            with self.tag('td', klass='thtd-28 fs-xl', ):
                self.doc.asis('<b>')
                self.text(bib)
            with self.tag('td', klass='thtd-28 fs-xl', ):
                self.text(' ')

            with self.tag('td', klass='thtd-left', ):
                self.text(f"{str(participant['last_name']).upper()}, {str(participant['first_name'])}")

            with self.tag('td', klass='thtd-left', ):
                self.text(str(participant['team_name']) if participant['team_name'] else '')

            with self.tag('td', klass='thtd-left', ):
                self.text(str(participant['category_code']) if participant['category_code'] else '')

        # Note row (initially hidden)
        with self.tag('tr', klass='participant-note fs-s', id=f"{wave_table_note_id}", ):
            #with self.tag('td', klass='thtd fs-xl', colspan=6, style='text-center: left; padding: 1px;', ):
            with self.tag('td', klass='thtd fs-xl', colspan=6, ):
                with self.tag('div', klass='div-note', ):
                    inputFieldId = wave_table_input_all_id if event else wave_table_input_n_id
                    otherFieldId = wave_table_input_n_id if event else wave_table_input_all_id

                    with self.tag('input', type='text', klass='note-input', id=inputFieldId,
                                  onkeydown=f"HNKD(event, '{bib}', '{otherFieldId}', )",): pass 

    def generate_right(self):
        # Right container for event and wave tables
        with self.tag('div', klass='right'):
            # Generate the Event Wave tables
            for event_id, event_info in self.parent.data.items():
                wave_table_all_id = self.parent.wave_table_all_id(event_id)
                print(f"Generating event table with ID: {event_id} {wave_table_all_id}")
                
                print(f"Generating all waves table with ID: {wave_table_all_id}")
                # Event Table all waves participants
                event_name = event_id.replace("event-", "").replace("_", " ").title()
                waves = [(wave_name.replace('Wave ','').upper(), wave_data['start_offset']) 
                         for wave_name, wave_data in event_info['waves'].items()]
                waves = ', '.join([f"{wave[0]}:{wave[1]}" for wave in waves])

                with self.tag('table', klass="table tablesorter participant-table", id=wave_table_all_id, 
                              style="display:none; padding: 1px;",):
                    # Event Wave Header
                    with self.tag('thead', klass='participant-thead', 
                                  style='width:100%;'):
                        self._generate_wave_header(True,)
                    # Add participants for all waves in the event
                    with self.tag('tbody', klass='participant-tbody', 
                                  style='width:100%;' ):
                        for wave_name, wave_data in event_info['waves'].items():
                            for participant in wave_data['participants']:
                                self._generate_wave_row(True, event_id, wave_name.replace("Wave", '').upper(), participant)

            # Generate Wave Participant tables
            for event_id, event_info in self.parent.data.items():
                event_name = event_id.replace("event-", "").replace("_", " ").replace('Race ','').title()
                for i, (wave_name, wave_data) in enumerate(event_info['waves'].items()):

                    wave_table_id = self.parent.wave_table_id(event_id, wave_name)
                    wave_table_all_id = self.parent.wave_table_all_id(event_id)
                    print(f"Generating wave table with ID: {event_id} {wave_table_id} {wave_table_all_id}")

                    categories = set([participant['category_code'] for participant in wave_data['participants']])

                    # Wave Table Participants
                    with self.tag('table', klass="table tablesorter participant-table", id=wave_table_id, 
                                  style="display:none; padding: 1px;"):
                        with self.tag('thead', klass='participant-thead',
                                      style='width:100%;'):
                            self._generate_wave_header(False, )
                                                       # f"Wave {event_name}{wave_name.replace('Wave ','').upper()} {event_info['start_time'].strftime('%H:%M')} + {wave_data['start_offset']} seconds", 
                                                       #f"{','.join(categories)}", )
                        # Add participants for this wave
                        with self.tag('tbody', klass='participant-tbody',
                                      style='width:100%;'):
                            for participant in wave_data['participants']:
                                self._generate_wave_row(None, event_id, wave_name.replace("Wave", '').upper(), participant)
                                #self._generate_wave_row(None, event_id, None, participant)

