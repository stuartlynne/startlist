import sys
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from libs.gpdf import generate_pdf


class GenPDF:
    def __init__(self, date, competition_name, competition_long_name, landscape=False):
        print('GenPDF:', date, competition_name, competition_long_name, file=sys.stdout)
        self.date = date
        self.competition_name = competition_name
        self.competition_long_name = competition_long_name
        self.landscape = landscape
        self.events = {}

    def add_event(self, event_id, event_name, event_start_time):
        """ Add an event to the competition. """
        print("-------------------")
        print(f"GenPDF: Adding event {event_id} {event_name} to competition", file=sys.stdout)
        self.events[event_id] = {
            'event_name': event_name,
            'event_start_time': event_start_time,
            'waves': {},
        }
        self.event_id = event_id

    def add_wave(self, event_id, wave_id, wave_name, start_offset, distance, laps, minutes, categories):
        """ Add a wave to an event. """
        print(f"GenPDF: Adding wave: {event_id} {wave_id} {wave_name}, Start Offset: {start_offset} Distance: {distance} Laps: {laps} Categories: {categories}", file=sys.stderr)

        # **Store category list (prevent overwriting by using a list instead of a dictionary)**
        formatted_categories = []
        for cat in categories:
            print(f"Category: {cat}")
            #cat_name = f"{cat[1]} ({'Men' if cat[2] == 0 else 'Women'})"
            cat_name = f"{cat[1]} ({['Men', 'Women', 'Open'][cat[2]]})"
            formatted_categories.append((cat[0], cat_name))

        print(f"Formatted Categories[{event_id},{wave_id}] {formatted_categories}")
        #formatted_categories = [(cat[0], f"{cat[1]} ({'Men' if cat[2] == 0 else 'Women'})") for cat in categories]
        #print(f"Formatted Categories[{event_id},{wave_id}] {formatted_categories}")

        self.events[event_id]['waves'][wave_id] = {
            'wave_name': wave_name,
            'start_offset': start_offset,
            'distance': distance,
            'laps': laps,
            'minutes': minutes,
            'categories': formatted_categories,  # **List of tuples (category_code, "Category (Gender)")**
            'participants': [],
        }

    def add_participant(self, event_id, wave_id, wave_name, participant_data):
        """ Add a participant to a wave. """
        print(f"GenPDF: Adding participant: {event_id} {wave_id} participant_data: {participant_data}", file=sys.stdout)
        category_code = participant_data.get('category_code', 'Unknown')
        category_gender = participant_data.get('category_gender', 0)
        category_name = f"{category_code} ({['Men', 'Women', 'Open'][category_gender]})"
        participant_data['category_code'] = category_name
        print(f"adding participant to wave {wave_id} with category {category_name}")
        self.events[self.event_id]['waves'][wave_id]['participants'].append(participant_data)

    def to_dataframe(self):
        """ Convert event, wave, and participant data into a Pandas DataFrame. """
        data = []
        print("\n=== DEBUG: Processing to_dataframe() ===\n")

        for event_id, event in self.events.items():
            print(f"Processing Event ID: {event_id}, Name: {event.get('competition_long_name', 'Unknown')}")
            
            for wave_id, wave in event["waves"].items():
                # **Create a category mapping for this wave**
                category_map = {cat_code: formatted for cat_code, formatted in wave["categories"]}

                # **Generate wave summary categories list**
                wave_categories = ", ".join(formatted for _, formatted in wave["categories"])

                print(f"  Wave ID: {wave_id}, Name: {wave['wave_name']}, Categories: {wave_categories}")

                # **Sort participants by Bib Number (Handle missing values as "N/A")**
                sorted_participants = sorted(
                    wave["participants"],
                    key=lambda p: int(p["bib"]) if p["bib"] and p["bib"] != "N/A" else float("inf")  # Ensure "N/A" goes last
                )

                for participant in sorted_participants:
                    # **Find correct category for participant (Category + Gender)**
                    formatted_category = category_map.get(participant["category_code"], participant["category_code"])

                    print(f"    Participant: {participant.get('first_name', 'Unknown')} {participant.get('last_name', 'Unknown')}, Bib: {participant.get('bib', 'N/A')}, Category: {formatted_category}")

                    data.append([
                        event_id,  # **Ensure event ID is included for proper grouping**
                        event.get("competition_long_name", "Unknown"),  # **Include event name**
                        wave["wave_name"],
                        wave["start_offset"],
                        wave["distance"],
                        wave["laps"],
                        wave_categories,  # **Wave summary categories**
                        participant.get("bib", "N/A"),
                        participant["first_name"],
                        participant["last_name"],
                        participant.get("team_name", "Independent"),
                        formatted_category,  # **Participant’s correct category**
                        participant.get("uci_id", "N/A"),
                        participant.get("license_checked", "N/A"),
                        participant.get("confirmed", "N/A"),
                    ])

        columns = ["Event ID", "Event Name", "Wave", "Start Offset", "Distance", "Laps", "Categories", "Bib", 
                   "First Name", "Last Name", "Team", "Category", "UCI ID", "License Checked", "Confirmed", ]
        df = pd.DataFrame(data, columns=columns)

        print(f"\n=== DEBUG: DataFrame Created with {len(df)} rows ===\n")
        print(df.groupby('Event ID')['Wave'].nunique())  # Show number of waves per event
        print("\n=== END DEBUG ===\n")

        return df


    def draw_header_footer(self, c, width, height, page_num, total_pages):
        """ Draws header and footer on each page. """

        # **Set Font & Color for Header (Black)**
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.black)

        # **Header - Align to Right**
        header_text = f"{self.competition_long_name} - {self.date}"
        text_width = c.stringWidth(header_text, "Helvetica-Bold", 12)  # Measure text width
        c.drawString(width - text_width - 50, height - 30, header_text)  # Align right

        # **Footer - Black Color**
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)

        # **Left side footer (Generated Timestamp)**
        footer_text = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        c.drawString(50, 30, footer_text)

        # **Right side footer (Page Number)**
        page_text = f"Page {page_num} of {total_pages}"
        text_width = c.stringWidth(page_text, "Helvetica", 10)  # Measure text width
        c.drawString(width - text_width - 50, 30, page_text)  # Align right


    def xdraw_header_footer(self, c, doc_width, doc_height, page_num, total_pages):
        """ Draws header and footer on each page. """
        header_y = doc_height - 30
        footer_y = 30

        # HEADER
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.darkblue)
        c.drawString(50, header_y, f"{self.competition_long_name} - {self.date}")

        # FOOTER
        c.setFont("Helvetica", 10)
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.drawString(50, footer_y, f"Generated on: {current_date}")
        c.drawString(doc_width - 150, footer_y, f"Page {page_num} of {total_pages}")


    def save(self):
        """ Saves each event as a separate PDF file. """
        for event_id, event in self.events.items():
            # Extract event details
            event_name = event["event_name"].replace(" ", "_")
            event_start_time = event["event_start_time"].strftime("%H%M")  # Format HHMM

            # Generate filename: {date}-{competition_name}-{starttime}.pdf
            filename = f"{self.date}-{self.competition_name.replace(' ', '_')}-{event_start_time}-startlist.pdf"

            # Generate a PDF for this event
            print(f"Generating PDF: {filename}")
            self.generate_pdf(event_id, filename, self.landscape)

        return "PDFs generated for each event."


GenPDF.generate_pdf = generate_pdf
