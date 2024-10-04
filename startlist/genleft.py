import sys
from yattag import Doc, indent
from datetime import datetime
from collections import Counter
#from .js import js, css


class GenLeft:

    def __init__(self, parent, doc, tag, text):
        self.parent = parent
        self.doc = doc
        self.tag = tag
        self.text = text

    def _generate_event_info_header(self, race=None, start_time=None):
        #if header1:
        #    self.text(header1)
        with self.tag('tr', klass="part-tr", style="line-height: 1.5; width:100%",):
            #with self.tag('th', klass='thtd', style="", ):
            #    #self.text('Wave')
            #    self.text(race)

            #for header in ['Laps', 'Minutes', 'Distance']:  
            #    with self.tag('th', klass='thtd', style="text-align: center; vertical-align: middle", ):
            #        self.text(header)
            with self.tag('th', klass='thtd', colspan=3, ):
                self.text(start_time)
            with self.tag('th', klass='thtd', ):
                self.text('Details')

            with self.tag('th', klass='thtd', style="padding-left: 10px; ", ):
                self.text('Categories')

            with self.tag('th', klass='thtd',  ):
                self.text('Starters')

    def _generate_event_info_row(self, count, event_id, wave_name, start_offset, laps, minutes, distance, categories, participant_counts):

        #event_info_cell_id, event_info_id, wave_table_all_id = self.parent.info_table_ids(event_id)
        wave_selection_tr_id = self.parent.wave_selection_tr_id(event_id, wave_name, )
        wave_table_id = self.parent.wave_table_id(event_id, wave_name)
        with self.tag('tr', klass='part-tr fs-s', id=wave_selection_tr_id,
                      onclick=f"TWT(['{wave_selection_tr_id}', null, '{wave_table_id}'])", ):

            with self.tag('td', klass='thtd-28', ):
                self.doc.asis('<b>')
                self.text(wave_name.replace('Wave ','').upper())

            with self.tag('td', klass='thtd-28', ):
                start_mmss = "%d:%02d" % (start_offset // 60,start_offset % 60)
                self.text(start_mmss)

            with self.tag('td', klass='thtd', style="text-align:left; ;  ", ):
                self.text('')

            if laps:
                distance = f"{distance*laps} km" if distance else None
            else:
                distance = f"{distance} km loop" if distance else None
            details = [ d for d in [ 
                  f"{str(distance)}" if distance else None,
                  f"{str(laps)} lap" if laps == 1 else f"{str(laps)} laps" if laps else None,
                  f"{str(minutes)} min" if minutes else None,
              ] if d is not None ] 

            details = ', '.join(details)

            #for detail in [laps, minutes, distance]:
            #    with self.tag('td', klass='thtd', style="text-align: left;padding-left: 20px; ", ):
            #        self.text(str(detail) if detail else '')
            with self.tag('td', klass='thtd-left', ):
                self.text(details)

            with self.tag('td', klass='thtd', style="text-align:left; ;  ", ):
                self.text(', '.join(categories) if categories else '')
            
            with self.tag('td', klass='thtd', style="text-align:left;", ):
                self.text(participant_counts)

    def generate_left(self):
        max_waves = max([len(event['waves']) for event in self.parent.data.values()])

        # Left container for event/wave selection, and event/wave information
        with self.tag('div', klass='left'):
            # Top level information title etc
            with self.tag('table', klass='table selection-table ', id='selection-table', style='margin-bottom: 0px; background-color: white; '):
                with self.tag('tr', style='width: 100%; '):
                    with self.tag('td', klass='fs-l', style='text-align: left; padding: 2px; background-color: white; '):
                        self.doc.asis('<b>')
                        self.doc.text(f'{self.parent.competition_name}')

                    with self.tag('td', klass='fs-l', style='text-align: right; padding: 2px; background-color: white; '):
                        self.doc.text('')

                    with self.tag('td', klass='fs-m', rowspan=2, style='text-align: right; position: relative;'):
                        with self.tag('div', style='position: relative; display: inline-block; width: 80px;'):
                            with self.doc.tag('input', 
                                              style='width: 100%; padding: 2px; text-align: center; background-color: white;',
                                              inputmode="numeric", 
                                              klass='fs-20px', 
                                              type='text',  # Changed 'search' to 'text'
                                              id='bibInput', 
                                              maxlength='5', 
                                              placeholder='Bib #', 
                                              onkeypress='return isNumber(event)', 
                                              onkeydown='handleKeyDown(event)', 
                                              onblur="searchBibNumber(false)"):
                                pass
                    with self.tag('td', klass='fs-m', rowspan=2, 
                                  style='text-align: right; position: relative;max-width: 20px; padding: 2px; '):
                            # Adjust the clear button's position for smaller screens
                            with self.doc.tag('span', klass='clear-button', 
                                              style='position: absolute; right: 5px; top: 50%; transform: translateY(-50%); cursor: pointer; z-index: 10;', 
                                              onclick='clearInput()'):
                                self.text('X')


                with self.tag('tr', ):
                    with self.tag('td', klass='thtd fs-6m', style='text-align: left; padding: 2px; '):
                        self.text(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                    with self.tag('td', klass='thtd fs-6m', style='text-align: right; padding: 2px; '):
                        with self.tag('span', klass='fs-m', style='cursor: pointer; ', 
                                      onclick=f"downloadNotes('{self.parent.competition_name}', '2024-09-23')"):
                            self.text('Share')

            # XXX
            # We need to generate and tag the event and wave information lines, they
            # will live in the left container and must be invisible by default,
            # we make them visible when the associated table which is in the right container is
            # made visible.

            # Generate the event selection table (static)
            with self.tag('table', klass="table table-striped selection-table fs-s",):
                if False:
                    with self.tag('thead', klass='part-thead', ):
                        with self.tag('tr', klass="select-tr", style="width:100%;", ):
                            with self.tag('th', klass="select-thtd", style="text-align:center",):
                                self.text('Start Time')
                            for i in range(max_waves):
                                with self.tag('th', klass="select-thtd", style="text-align:left",):
                                    self.text(f'Wave {chr(65 + i)}')  # Add "Wave A", "Wave B", etc. to header

                with self.tag('tbody', klass='part-tbody', ):
                    with self.tag('tr', klass="select-tr", style="width:100%;", ):
                        for event_id, event_info in self.parent.data.items():
                            #print(f"Generating event row for {event_id} info {event_info}", file=sys.stderr)
                            event_name = event_info['name'].replace("#", "")+'.'
                            #XXevent_info_cell_id, XXevent_info_id, XXwave_table_all_id = self.parent.info_table_ids(event_id)

                            event_info_cell_id = self.parent.event_info_cell_id(event_id)
                            event_info_id = self.parent.event_info_id(event_id)
                            wave_table_all_id = self.parent.wave_table_all_id(event_id)
                            print(f"Generating event row for {event_id} info {event_info} {event_info_cell_id} {event_info_id} {wave_table_all_id}", 
                                  file=sys.stderr)
                            #with self.tag('td', klass="select-thtd", style="text-align:left",):
                            #    self.text(event)
                            with self.tag('td', klass="select-thtd", id=event_info_cell_id,
                                          onclick=f"TET(['{event_info_cell_id}', '{event_info_id}', '{wave_table_all_id}'])", ):
                                self.text(f"{event_name} {event_info['start_time'].strftime('%H:%M')}")
            # Generate the Event Information table 
            for event_id, event_info in self.parent.data.items():

                #event_info_cell_id, event_info_id, wave_table_all_id = self.parent.info_table_ids(event_id)
                event_info_cell_id = self.parent.event_info_cell_id(event_id)
                event_info_id = self.parent.event_info_id(event_id)
                wave_table_all_id = self.parent.wave_table_all_id(event_id)

                # Event table with all waves
                with self.tag('table', klass="table table-striped tablesorter part-table", style="display:none; padding: 1px; width:100%;",
                              id=event_info_id, ):
                    event_name = event_id.replace("event-", "").replace("_", " ").title()
                    with self.tag('thead', klass='part-thead', 
                                  style='width:100%;'):
                        self._generate_event_info_header(event_name, event_info['start_time'].strftime('%H:%M'), )

                    with self.tag('tbody', klass='part-tbody', style='width:100%;' ):
                        for i, (wave_name, wave_data) in enumerate(event_info['waves'].items()):
                            participant_counts = ', '.join([str(v) for v in Counter([participant['category_code']
                                                                        for participant in wave_data['participants']]).values()])

                            print('wavedata', wave_data, file=sys.stderr)

                            categories = [f"{code} {['M', 'W', 'O'][gender] if gender in [0,1,2] else ''}" for
                                          id, code, gender, description in wave_data['categories']]

                            self._generate_event_info_row(i, event_id, wave_name, wave_data['start_offset'], wave_data.get('laps',None), wave_data.get('minutes', None), 
                                          wave_data.get('distance', None), 
                                          categories,
                                          participant_counts)

                    start_offset = wave_data['start_offset']
                    start_mmss = f"{start_offset // 60}:{start_offset % 60}"
                    waves = [(wave_name.replace('Wave ','').upper(), start_mmss,
                              wave_data['distance'], wave_data['laps'], wave_data['minutes']) 
                             for wave_name, wave_data in event_info['waves'].items()]
                    print(f"Generating event info table with ID: {event_info_id} {waves}", file=sys.stderr)

