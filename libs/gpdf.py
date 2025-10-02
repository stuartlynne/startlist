import sys
import pandas as pd
from pandas import isna
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

def page1_table(c, width, height, df, landScape=False, category_bib_ranges=None ):
    styles = [
        # **Header Row**
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("ALIGN", (2, 0), (2, 0), "LEFT"),
        ("ALIGN", (3, 0), (3, 0), "LEFT"),
        ("ALIGN", (4, 0), (4, 0), "RIGHT"),

        # **Data Rows**
        ("ALIGN", (0, 1), (0, -1), "RIGHT"),
        ("ALIGN", (1, 1), (1, -1), "CENTER"),
        ("ALIGN", (2, 1), (2, -1), "LEFT"),
        ("ALIGN", (3, 1), (3, -1), "LEFT"),
        ("ALIGN", (4, 1), (4, -1), "RIGHT"),

        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 14),  # **Larger Font for Header**
        #("ROWHEIGHTS", (0, 0), (-1, 0), 1000),  # **Increase header row height**
        ("VALIGN", (0, 0), (-1, 0), "TOP"),
        ("FONTSIZE", (0, 1), (-1, -1), 14),
        ("VALIGN", (0, 1), (-1, -1), "TOP"),
    ]
    offset_style = ParagraphStyle(name="WrapOffset", fontName="Helvetica-Bold",
                                  fontSize=14, leading=18, alignment=TA_CENTER)
    table_data = [["Wave", Paragraph("Start Offset", offset_style), "Details", "Categories", "Starters"]]
    total_starters = 0
    for i, (wave, wave_df) in enumerate(df.groupby("Wave")):
        print(f'Wave row[{i}] {wave}', file=sys.stderr)
        print(f"Wave {wave}: {len(wave_df)} starters")
        print(f"Wave  wave_df: {wave_df}", file=sys.stderr)
        print(f"Wave  wave_df: Distance {wave_df['Distance'].iloc[0]}", file=sys.stderr)
        print(f"Wave  wave_df: Laps {wave_df['Laps'].iloc[0]}", file=sys.stderr)
        print(f"Wave  wave_df: Minutes {wave_df['Minutes'].iloc[0]}", file=sys.stderr)

        print(f'Wave row[{i}] Extra', file=sys.stderr)
        styles.append(("LINEBELOW", (0, 2*i + 1), (-1, 2*i + 1), 2, colors.whitesmoke))
        table_data.append(["", "", "", "", ""])  # **Empty row for spacing**

        # **Extract formatted categories (already includes gender)**
        category_counts = wave_df.groupby("Category").size().reset_index(name="Starters")
        formatted_categories = wave_df["Categories"].iloc[0]  
        print(f"Formatted Categories: {formatted_categories}", file=sys.stderr)
        #formatted_categories = ",".join(f"{row['Category']} {row['Starters']} [{category_bib_ranges.get(row['Category'], '')}]" for _, row in category_counts.iterrows())
        formatted_categories = ",\n".join(f"{row['Category']} {category_bib_ranges.get(row['Category'], '')}" for _, row in category_counts.iterrows())
        category_starters = "+".join(f"{row['Starters']}" for _, row in category_counts.iterrows())
        print(f"Formatted Categories: {formatted_categories}", file=sys.stderr)
        print(f"Category Starters: {category_starters}", file=sys.stderr)
        print(f"Number of Categories: {len(category_counts)}", file=sys.stderr)

        wave_starters = f"{len(wave_df)}"
        if len(category_counts) > 1:
            wave_starters += f"\n{category_starters}"

        total_starters += len(wave_df)

        # **Use HTML `<br/>` for line breaks + `<b>` for bold, and add `leading=22` for extra spacing**
        #details_style = ParagraphStyle(name="BoldDetails", fontSize=14, leading=14)  # **Increase line spacing**
        #if wave_df["Distance"].iloc[0]:
        #    distance = round(wave_df["Distance"].iloc[0]*wave_df["Laps"].iloc[0]) 
        #    details_text = f"{distance} <b>km</b><br/>{wave_df['Laps'].iloc[0]} <b>laps</b>"
        #else:
        #    # XXX minutes
        #    minutes = wave_df["Minutes"].iloc[0]
        #    details_text = f"{minutes} <b>m</b><br/>"

        details_style = ParagraphStyle(name="BoldDetails", fontSize=14, leading=14)

        # Extract fields
        d = wave_df["Distance"].iloc[0] if "Distance" in wave_df else None
        l = wave_df["Laps"].iloc[0] if "Laps" in wave_df else None
        m = wave_df["Minutes"].iloc[0] if "Minutes" in wave_df else None

        # check if Minutes is available
        if m is not None and not isna(m):
            details_text = f"{int(m)} <b>m</b><br/>"
        # Check if Distance and Laps are both present and not NaN
        elif d is not None and l is not None and not (isna(d) or isna(l)):
            distance = round(d * l)
            details_text = f"{distance} <b>km</b><br/>{int(l)} <b>laps</b>"
        else:
            details_text = "–"

        details_paragraph = Paragraph(details_text, details_style)
        wave_paragraph = Paragraph(wave, details_style)
        categories_paragraph = Paragraph(formatted_categories, details_style)
        start_offset = round(wave_df['Start Offset'].iloc[0]//60)
        print(f"Start Offset: {start_offset} AAAAAAAA", file=sys.stderr)
        #start_offset = round(wave_df['Start Offset']//60)
        #print(f"Start Offset: {start_offset} BBBBBBBB", file=sys.stdout)

        table_data.append([
            wave_paragraph,  # Wave
            f"{wave_df['Start Offset'].iloc[0]//60:.0f}:00",  # Start Offset formatted as "0:00"
            details_paragraph,  # **Bold "km" and "laps" with stacking + extra spacing**
            categories_paragraph,  # **Categories stacked vertically**
            wave_starters  # Number of starters
        ])

    colWidths = [50, 80, 100, 320, 80] if landScape else [50, 80, 70, 240, 70] 
    table = Table(table_data, colWidths=colWidths)  # **Wider column for spacing**
    styles.append(("ROWHEIGHTS", (0, 1), (-1, -1), [100] * (len(table_data) - 1)))
    table.setStyle(TableStyle(styles))

    # **Draw Table Without Borders**
    table.wrapOn(c, width, height)
    table_width, table_height = table.wrap(width, height)
    table.drawOn(c, 50, height - 190 - table_height)  # **Ensures extra space below header**

    return total_starters

def truncate_text(text, max_length):
    """Truncate text to fit within max_length, adding '...' if necessary."""
    return text if len(text) <= max_length else text[:max_length-3] + "..."

def generate_pdf(self, event_id, pdf_filename, landScape=False, category_bib_ranges=None):
    """ Generates a PDF report formatted like Thunderbird PDF. """
    print("Category Bib Ranges:", category_bib_ranges, file=sys.stderr)
    # Filter data only for the selected event_id
    event = self.events.get(event_id)
    if not event:
        print(f"Error: Event {event_id} not found.", file=sys.stderr)
        return

    df = self.to_dataframe(category_bib_ranges=category_bib_ranges)  # Convert to DataFrame

    # **Ensure "Event ID" exists before filtering**
    if "Event ID" not in df.columns:
        print("Error: 'Event ID' column missing from DataFrame!", file=sys.stderr)
        return

    df = df[df["Event ID"] == event_id]  # **Filter only the selected event**

    if df.empty:
        print(f"Warning: No participants found for event {event_id}.", file=sys.stderr)
        return


    # **Calculate total pages (account for large waves)**
    #first_page_rows = 24  # **Limit participants on first page**
    #remaining_page_rows = 25
    #total_pages = sum([1 + -(-len(wave_df) // remaining_page_rows) for _, wave_df in df.groupby("Wave")]) + 1  # +1 for title page
    # **Calculate total pages (account for large waves)**

    if landScape:
        width, height = landscape(letter)
        first_page_rows = 24  # **Limit participants on first page**
        remaining_page_rows = 28  # **Subsequent pages hold 25 participants each**
    else:
        width, height = letter
        first_page_rows = 34  # **Limit participants on first page**
        remaining_page_rows = 38  # **Subsequent pages hold 25 participants each**

    c = canvas.Canvas(pdf_filename, pagesize=landscape(letter) if landScape else letter)

    #wrap_style = ParagraphStyle(name="WrapStyle", wordWrap="CJK", fontSize=14, leading=16)  # **Increase line spacing**
    #wrap_style = ParagraphStyle(name="WrapStyle", wordWrap="CJK", leading=16)  # **Increase line spacing**
    wrap_style = ParagraphStyle(name="WrapStyle", leading=16)  # **Increase line spacing**

    # **Fix: Properly account for the first-page participants**
    total_pages = sum([
        1 + max(0, -(-(len(wave_df) - first_page_rows) // remaining_page_rows))  # **Fix for additional pages**
        for _, wave_df in df.groupby("Wave")
    ]) + 1  # **+1 for title page**

    # **Title Page**
    self.draw_preliminary_watermark(c, width, height)
    self.draw_header_footer(c, width, height, 1, total_pages)

    # **Generated Timestamp (at top)**
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 30, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # **Event Name - Larger and on Two Lines**
    c.setFont("Helvetica-Bold", 32)
    event_title = self.competition_long_name  # **Use Full Event Name**
    c.drawString(50, height - 100, self.competition_long_name)  # **Left-aligned**

    c.setFont("Helvetica", 28)  # **Smaller Font for Time**
    c.drawString(50, height - 140, event["event_start_time"].strftime("%Y-%m-%d %I:%M %p"))

    total_starters = len(df)
    print('Total Starters:', total_starters, file=sys.stderr)

    # **Wave Summary Table (Formatted)**
    total_starts = page1_table(c, width, height, df, landScape=landScape, category_bib_ranges=category_bib_ranges )
    print('Total Starters:', total_starters, file=sys.stderr)
    c.setFont("Helvetica", 20)
    c.drawString(50, height - 180, f"Total Starters: {total_starts}")

    c.showPage()


    # **Process Riders (Grouped by Wave)**
    page_num = 2
    for wave, wave_df in df.groupby("Wave"):
        self.draw_preliminary_watermark(c, width, height)
        self.draw_header_footer(c, width, height, page_num, total_pages)

        c.setFont("Helvetica", 16)
        c.drawString(50, height - 60, f"{self.competition_long_name} {event['event_start_time'].strftime('%Y-%m-%d %I:%M %p')}")

        c.setFont("Helvetica", 40)

        wave_starters = len(wave_df)
        print(f"Wave {wave}: {wave_starters} starters", file=sys.stderr)

        # **Wave Summary**
        #c.setFont("Helvetica-Bold", 14)
        #if wave_df["Distance"].iloc[0]:
        #    distance = round(wave_df["Distance"].iloc[0] * wave_df["Laps"].iloc[0])
        #    c.drawString(50, height - 80, f"{wave}: Offset {wave_df['Start Offset'].iloc[0]:.0f}:00, {distance} km, {wave_df['Laps'].iloc[0]} laps, Starters: {wave_starters}")
        #else:
        #    # XXX minutes
        #    minutes = wave_df["Minutes"].iloc[0]
        #    c.drawString(50, height - 80, f"{wave}: Offset {wave_df['Start Offset'].iloc[0]:.0f}:00, {minutes} m, Starters: {wave_starters}")
        # Extract fields
        d = wave_df["Distance"].iloc[0] if "Distance" in wave_df else None
        l = wave_df["Laps"].iloc[0] if "Laps" in wave_df else None
        m = wave_df["Minutes"].iloc[0] if "Minutes" in wave_df else None
        offset = wave_df["Start Offset"].iloc[0] if "Start Offset" in wave_df else 0

        c.setFont("Helvetica-Bold", 14)
        if m is not None and not isna(m):
            c.drawString(50, height - 80,
                f"{wave}: Offset {offset:.0f}:00, {int(m)} m, Starters: {wave_starters}")
        elif d is not None and l is not None and not (isna(d) or isna(l)):
            distance = round(d * l)
            c.drawString(50, height - 80,
                f"{wave}: Offset {offset:.0f}:00, {distance} km, {int(l)} laps, Starters: {wave_starters}")
        else:
            c.drawString(50, height - 80,
                f"{wave}: Offset {offset:.0f}:00, Starters: {wave_starters}")


        # **First Page of Wave - Display the First 10 Participants**
        #y_position = height - 360  # **Using your y_position offset**
        y_position = 60  # **Using your y_position offset**

        table_data = [["Bib", "Name", "Team", "Category", "UCI ID", ""]]
        init_styles = [
            ("ROWHEIGHTS", (0, 0), (-1, -1), 40),  # **Increase header row height**
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),  # **Smaller Font for Header**
            ("FONTNAME", (0, 1), (1, -1), "Helvetica-Bold"),
            #("FONTSIZE", (0, 1), (1, -1), 10),  # **Larger Font for Header**
            ("WORDWRAP", (0, 0), (-1, -1), None),  # 
            ("TRUNCATE", (0, 0), (-1, -1), True),  #
            ]
        styles = init_styles.copy()
        index = 1
        for i, (_, row) in enumerate(wave_df.iloc[:first_page_rows].iterrows()):
            if not self.preliminary and i % 2 == 0:
                row_idx = i + 1  # +1 to skip header row
                styles.append(("BACKGROUND", (0, row_idx), (-1, row_idx), colors.whitesmoke))
            lc = ""
            if row["License Checked"]:
                lc = "l"
            if row["Confirmed"]:
                lc += "c"
            name = f"{row['Last Name'].upper()}, {row['First Name'].capitalize()}"
            team = row.get("Team", "")
            if not team:
                team = ""
            team = truncate_text(team, 24)
            print('Team:', team, file=sys.stderr)
            category = row["Category"]
            category = truncate_text(category, 28)
            table_data.append( [ row["Bib"], name, team, category, row["UCI ID"], lc])
            index += 1

        colWidths = [50, 200, 220, 120, 80, 10] if landScape else [30, 140, 150, 130, 70, 20]
        table = Table(table_data, colWidths=colWidths)  # **More space per column**

        table.setStyle(TableStyle(styles))
        table_width, table_height = table.wrap(width, height)
        table.wrapOn(c, width, height)
        table.drawOn(c, 50, height-100-table_height)

        c.showPage()
        page_num += 1

        # **Additional Pages (Remaining Participants, 25 per page)**
        remaining_participants = wave_df.iloc[first_page_rows:]
        while not remaining_participants.empty:
            self.draw_preliminary_watermark(c, width, height)
            self.draw_header_footer(c, width, height, page_num, total_pages)

            # Move table further DOWN on subsequent pages
            #y_position = height - 800  # **Start table at top of new page**
            y_position = 60  # **Start table at top of new page**

            table_data = [["Bib", "Name", "Team", "Category", "UCI ID"]]
            styles = init_styles.copy()
            # XXX Teams column is not getting truncated, a long team name gets printed overtop the Category column
            for i, (_, row) in enumerate(remaining_participants.iloc[:remaining_page_rows].iterrows()):
                if not self.preliminary and i % 2 == 0:
                    row_idx = i + 1  # +1 to skip header row
                    styles.append(("BACKGROUND", (0, row_idx), (-1, row_idx), colors.whitesmoke))
                lc = ""
                if row["License Checked"]:
                    lc = "l"
                if row["Confirmed"]:
                    lc += "c"
                name = f"{row['Last Name'].upper()}, {row['First Name'].capitalize()}"
                team = row.get("Team", "")
                if not team:
                    team = ""

                #print(f'Table[{index}]: {row["Bib"]} {name} {team} {row["Category"]} {row["UCI ID"]} {lc}', file=sys.stderr)
                table_data.append( [ row["Bib"], name, team, row["Category"], row["UCI ID"], lc])
                index += 1

            table = Table(table_data, colWidths=colWidths)  # **More space per column**

            table.setStyle(TableStyle(styles))
            table_width, table_height = table.wrap(width, height)
            table.wrapOn(c, width, height)
            table.drawOn(c, 50, height-40-table_height)

            # Move to the next set of participants
            remaining_participants = remaining_participants.iloc[remaining_page_rows:]
            c.showPage()
            page_num += 1

    c.save()
