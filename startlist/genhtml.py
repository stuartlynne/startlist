import sys
from yattag import Doc, indent
from datetime import datetime
from collections import Counter

class GenHTML:

    js = """
    <script>
        
        $(document).ready(function () {
            $("table").tablesorter({
                theme: 'default',   // Default theme with sorting arrows
                widgets: ['zebra'], // Zebra striping effect for the rows
            });
        });
        

        // Ensure only numbers are inputted
        function isNumber(evt) {
            console.log('isNumber: %s', evt.which);
            var charCode = (evt.which) ? evt.which : evt.keyCode;
            if (charCode > 31 && (charCode < 48 || charCode > 57))
                return false;
            return true;
        }
        // handle keydown event
        function handleKeyDown(evt) {
            console.log('heandleKeyDown: %s', evt.which);
            if (evt.key === 'Enter') {
                console.log('heandleKeyDown: Enter');
                searchBibNumber(false);
            }
        }

        var lastClickedCell = null;
        function toggleTable(eventId, clickedCell, reset) {
            console.log('Toggling table for ID:', eventId, );

            var allTables = document.querySelectorAll('table[id^="wave-table-"]');
            allTables.forEach(function(table) {
                var rows = table.getElementsByTagName('tr');
                for (var i = 1; i < rows.length; i++) {  // Skip header row
                    rows[i].querySelectorAll('td').forEach(function(td) {
                        td.style.backgroundColor = "";
                    });
                }
            })

            // Reset the last clicked cell
            if (lastClickedCell) {
                lastClickedCell.style.backgroundColor = "";
            }

            // Highlight the clicked cell
            if (clickedCell) {
                lastClickedCell = clickedCell;
                clickedCell.style.backgroundColor = "yellow";  // Highlight color
            } 

            // reset previous highlights
            var selectedTable = document.getElementById(eventId);
            if (reset && selectedTable.style.display === 'table') {
                selectedTable.style.display = 'none';
            } else {
                var allTables = document.querySelectorAll('table[id^="event-table-"], table[id^="wave-table-"]');
                allTables.forEach(function(table) {
                table.style.display = 'none';
                });
                selectedTable.style.display = 'table';
            }
        }

        // Search for the bib number and make the corresponding table visible
        function searchBibNumber(reset) {
            var bibNumber = document.getElementById("bibInput").value;

            console.log('Searching for bib number:', bibNumber);

            if (bibNumber) {
                var found = false;
                var allTables = document.querySelectorAll('table[id^="wave-table-"]');
                
                allTables.forEach(function(table) {
                    var rows = table.getElementsByTagName('tr');
                    for (var i = 1; i < rows.length; i++) {  // Skip header row
                        var bibCell = rows[i].getElementsByTagName('td')[0];  // Assuming Bib is in the first column
                        if (bibCell && bibCell.innerText === bibNumber) {
                            found = true;
                            //table.style.display = 'table';  // Make the corresponding table visible
                            toggleTable(table.id, null, reset);
                            rows[i].querySelectorAll('td').forEach(function(td) {
                                td.style.backgroundColor = "yellow";
                            });
                            document.getElementById("bibInput").value = "";  // Clear the input field
                            break;
                        }
                    }
                });
                if (!found) {
                    customAlert("Bib number not found.");
                }
            } else {
                customAlert("Please enter a Bib number.");
            }
        }
        function customAlert(message, timeout = 1400) {
            const alertBox = document.createElement('div');
            alertBox.textContent = message;
            alertBox.style.cssText = `
                position: fixed;
                top: 20px;
                left: 50%;
                transform: translateX(-50%);
                background-color: #f8d7da;
                color: #721c24;
                padding: 10px;
                border: 1px solid #f5c6cb;
                border-radius: 5px;
                z-index: 9999;
            `;
            document.body.appendChild(alertBox);

            setTimeout(() => {
                alertBox.remove();
            }, timeout);
        }


    </script>
    """

    css = """
    html, body {
        width: 100%;
        height: 100%;
        margin: 0;
        padding: 0;
        box-sizing: border-box;
        overflow-x: hidden; /* Prevent any hidden overflow */
    }

    .container {
        display: flex;
        flex-direction: column;
        width: 100vw;
        height: 100vh; /* Ensure the container fills the entire viewport */
        padding: 0;
        margin: 0;
        max-width: none;
        max-height: none;
    }

    .left, {
        padding: 0;
        margin: 0;
    }

    .right {
        flex-grow: 1;
        padding: 0;
        margin: 0;
        overflow-y: auto;  /* Enable vertical scrolling */
    }


    thead {
      display: table-header-group;
    }

    .select-tr { padding: 1px !important; text-align: center; width: 100%; }
    .select-thtd { padding: 1px !important; text-align: center; }

    .participant-table {
        border-collapse: collapse;
        border: none !important;
        margin: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;

    }
    .participant-thead {
        align-items: start;
        position: sticky;  /* Make the header sticky */
        background-color: white;
        top: 0;
        border-spacing: 0;
    }
    .participant-tr { 
        align-items: end;
        margin: 0;
        padding: 0 !important; 
        text-align: center; 
        width: 100%; 
        border-spacing: 0;
        border: none !important;
    }
    .participant-thtd { 
        padding: 1px !important; 
        text-align: center; 
        border-spacing: 0;
        vertical-align: middle !important; 
    }

    @media screen and (orientation: landscape) {
        .container {
            flex-direction: row;
            width: 100vw;
            justify-content: stretch; /* Stretch the columns to fill the available space */
            gap: 20px
        }
        .left, .right {
            width: 50vw;
            height: 100vh; /* Ensure columns span the entire viewport height */
        }
    }


    @media screen and (min-width: 768px) and (max-width: 1024px) {
        /* Styles for tablets */
    }
    @media screen and (min-width: 1024px) {
        /* Styles for desktop browsers */
    }



"""

    def __init__(self, competition_name, competition_date):
        self.competition_name = competition_name
        self.competition_date = competition_date
        self.doc, self.tag, self.text = Doc().tagtext()
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

                    self.doc.asis(self.css)


                # Link to the external JavaScript file for sorting and table toggling
                #self.doc.asis('<script src="startlist.js"></script>')
                self.doc.asis(self.js)
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

    def add_wave(self, wave_name, start_offset):
        event_section_id = list(self.data.keys())[-1]  # Get the last added event
        if wave_name not in self.data[event_section_id]['waves']:
            self.data[event_section_id]['waves'][wave_name] = {
                'start_offset': int(start_offset),  # Convert float to int
                'participants': []
            }

    def add_participant(self, dummy, wave_name, participant_data):
        event_section_id = list(self.data.keys())[-1]  # Get the last added event
        if wave_name in self.data[event_section_id]['waves']:
            self.data[event_section_id]['waves'][wave_name]['participants'].append(participant_data)

    def _generate_participant_header(self, event, header1, header2):
        #if header1:
        #    self.text(header1)
        with self.tag('thead', klass='participant-thead', ):
            if header1:
                with self.tag('tr', klass='participant-tr', style="line-height: 1.5; ",):
                    with self.tag('th', klass='participant-thtd fs-m', style="text-align: left;", colspan=3 if event else 3, ):
                        self.text(header1)
                    if header2:
                        with self.tag('th', klass='participant-thtd fs-s', style="text-align: left;", colspan=2 if event else 1, ):
                            self.text(header2)
            with self.tag('tr', klass="participant-tr", style="line-height: 1.5;",):
                if event:
                    with self.tag('th', klass='participant-thtd', style="text-align: right; width:.m", ):
                        self.text('')

                with self.tag('th', klass='participant-thtd', style="text-align: center; vertical-align: middle", ):
                    self.text('Bib')

                with self.tag('th', klass='participant-thtd', style="text-align: left; vertical-align: middle; padding-left: %s; " % ('10px' if event else '1px'), ):
                    self.text('Name')

                with self.tag('th', klass='participant-thtd', style="text-align: left; vertical-align: middle;", ):
                    self.text('Team')

                with self.tag('th', klass='participant-thtd', style="text-align: left; ", ):
                    self.text('Category')


    def _generate_participant_row(self, event, wave_name, participant):

        with self.tag('tr', klass='participant-tr fs-s', style='; height=5px; '):
            if event:
                with self.tag('td', klass='participant-thtd fs-xl', style='text-align: center; width:24px;", '):
                    self.doc.asis('<b>')
                    self.text(wave_name if wave_name else '_')

            with self.tag('td', klass='participant-thtd fs-xl', style='text-align: center; width:28px;", '):
                self.doc.asis('<b>')
                self.text(str(participant['bib']) if participant['bib'] else '')

            with self.tag('td', klass='participant-thtd', style="text-align: left;padding-left: %s; " % ('20px' if event else '10px'), ):
                self.text(f"{str(participant['last_name']).upper()}, {str(participant['first_name'])}")

            with self.tag('td', klass='participant-thtd', style="text-align:left; ;  ", ):
                self.text(str(participant['team_name']) if participant['team_name'] else '')

            with self.tag('td', klass='participant-thtd', style="text-align:left;", ):
                self.text(str(participant['category_code']) if participant['category_code'] else '')

    def generate_left(self):
        max_waves = max([len(event['waves']) for event in self.data.values()])

        # Left container for event/wave selection, and event/wave information
        with self.tag('div', klass='left'):
            # Top level information title etc
            with self.tag('table', klass='table table-striped; '):
                with self.tag('tr', style='width: 100%; '):
                    with self.tag('td', klass='fs-l', style='text-align: left; padding: 2px; '):
                        self.doc.asis('<b>')
                        self.doc.text(f'{self.competition_name}')
                    with self.tag('td', klass='fs-m', rowspan=2, style='text-align: right; '):
                        # XXX
                        #with self.doc.tag('input', klass='fs-20px', type='number', id='bibInput', style='width: 80px; padding: 2px; text-align: center;', 
                        #with self.doc.tag('input', pattern="[0-9]", klass='fs-20px', type='text', id='bibInput', style='width: 80px; padding: 2px; text-align: center;', 
                        with self.doc.tag('input', inputmode="numeric", klass='fs-20px', type='text', id='bibInput', style='width: 80px; padding: 2px; text-align: center;', 
                                          maxlength='5', placeholder='Bib #', 
                                          onkeypress='return isNumber(event)', onkeydown='handleKeyDown(event)',
                                          onblur="searchBibNumber(false)"):
                            pass

                with self.tag('tr', ):
                    with self.tag('td', klass='fs-6m', style='text-align: left; padding: 2px; '):
                        self.text(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

            # XXX
            # We need to generate and tag the event and wave information lines, they
            # will live in the left container and must be invisible by default,
            # we make them visible when the associated table which is in the right container is
            # made visible.

            # Generate the event selection table (static)
            with self.tag('table', klass="table table-striped selection-table fs-s",):
                with self.tag('thead'):
                    with self.tag('tr', klass="select-tr", style="width:100%;", ):
                        with self.tag('th', klass="select-thtd", style="text-align:center",):
                            self.text('Start Time')
                        for i in range(max_waves):
                            with self.tag('th', klass="select-thtd", style="text-align:left",):
                                self.text(f'Wave {chr(65 + i)}')  # Add "Wave A", "Wave B", etc. to header

                with self.tag('tbody'):
                    for event_id, event_info in self.data.items():
                        #print(f"Generating event row for {event_id} info {event_info}", file=sys.stderr)
                        event_name = event_info['name'].replace("#", "")+'.'
                        print(f"Generating event row for {event_id} info {event_info['name']} name {event_name}", file=sys.stderr)
                        with self.tag('tr', klass="select-tr", style="width:100%;", ):

                            # Add onclick for Race and Start Time columns to open Event table
                            with self.tag('td', klass="select-thtd", onclick=f"toggleTable('event-table-{event_id}', this, true)", style="cursor: pointer;text-align:center"):
                                self.text(f"{event_name} {event_info['start_time'].strftime('%H:%M')}")

                            # Add onclick for Wave columns to open individual Wave tables
                            wave_names = list(event_info['waves'].keys())
                            for i, wave_name in enumerate(wave_names):
                                wave_data = event_info['waves'][wave_name]
                                num_participants = len(wave_data['participants'])
                                participant_counts = Counter([participant['category_code'] for participant in wave_data['participants']])
                                #print(f"Participant counts: {participant_counts}", file=sys.stderr)
                                #print(f"Participant counts: {participant_counts.values()}", file=sys.stderr)
                                wave_table_id = f"wave-table-{event_id}-{wave_name.replace(' ', '_')}"
                                with self.tag('td', klass="select-thtd", onclick=f"toggleTable('{wave_table_id}', this, true)", style="cursor: pointer; text-align:left"):
                                    self.text(f"{wave_data['start_offset']}s: {', '.join([str(v) for v in participant_counts.values()])}")
                            
                            # Fill any remaining cells for missing waves with empty <td>
                            for _ in range(len(wave_names), max_waves):
                                with self.tag('td', klass="select-thtd", ):
                                    self.text('')
    
    def generate_right(self):
        # Right container for event and wave tables
        with self.tag('div', klass='right'):
            # Generate each event table (all waves together)
            for event_id, event_info in self.data.items():
                event_table_id = f"event-table-{event_id}"
                print(f"Generating event table with ID: {event_table_id}")
                
                # Event table with all waves

                #self.doc.asis('<script> $(function() { $("#%s").tablesorter({"theme": "blue"}); </script> ' % (event_table_id))
                if False:
                    # XXX WIP
                    # period in the id is not allowed ???
                    with self.doc.tag('script'):
                        self.doc.asis("""
                            $("#%s").tablesorter({ theme : 'dropbox', cssIcon: 'tablesorter-icon',
                                initialized : function(table){
                                console.log('tablesorter initialized', table);
                                $(table).find('thead .tablesorter-header-inner').append('<i class="tablesorter-icon"></i>');
                              }
                            });
                        """ % (event_table_id))

                with self.tag('table', klass="table table-striped tablesorter participant-table", id=event_table_id, style="display:none; padding: 1px;"):
                    #with self.tag('thead'):
                    event_name = event_id.replace("event-", "").replace("_", " ").title()
                    waves = [(wave_name.replace('Wave ','').upper(), wave_data['start_offset']) 
                             for wave_name, wave_data in event_info['waves'].items()]
                    waves = ', '.join([f"{wave[0]}:{wave[1]}" for wave in waves])

                    self._generate_participant_header(True, 
                          f"Race {event_name} {event_info['start_time'].strftime('%H:%M')}", 
                          f"Start Offsets: {waves}")

                    # Add participants for all waves in the event
                    for wave_name, wave_data in event_info['waves'].items():
                        for participant in wave_data['participants']:
                            self._generate_participant_row(True, wave_name.replace("Wave", '').upper(), participant)

            # Generate individual wave tables
            for event_id, event_info in self.data.items():
                event_name = event_id.replace("event-", "").replace("_", " ").replace('Race ','').title()
                for wave_name, wave_data in event_info['waves'].items():
                    wave_table_id = f"wave-table-{event_id}-{wave_name.replace(' ', '_')}"
                    print(f"Generating wave table with ID: {wave_table_id}")

                    categories = set([participant['category_code'] for participant in wave_data['participants']])

                    # Individual wave table
                    with self.tag('table', klass="table table-striped tablesorter participant-table", id=wave_table_id, 
                                  style="display:none; padding: 1px;"):
                        self._generate_participant_header(False, 
                              f"Wave {event_name}{wave_name.replace('Wave ','').upper()} {event_info['start_time'].strftime('%H:%M')} + {wave_data['start_offset']} seconds", 
                              f"{','.join(categories)}", )
                        # Add participants for this wave
                        for participant in wave_data['participants']:
                            self._generate_participant_row(None, False, participant)


    def generate_html(self):
        with self.tag('div', klass='container'):
            self.generate_left()
            self.generate_right()

    def save(self):
        self.generate_html()
        html_output = indent(self.doc.getvalue())
        #output_filename = f'startlists_{self.competition_name.replace(" ", "_")}.html'
        with open(self.output_filename, 'w') as f:
            f.write(html_output)
        return self.output_filename
