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

def draw_lapboard(c, width, height, df, bottom_limit_y, landScape=False):
    """Draw a 16:9 lapboard at the bottom of the page.

    - The board is anchored above the page bottom with a small margin.
    - It is split into N vertical windows, where N = number of start waves.
    - Each window shows the wave label and its list of categories.

    bottom_limit_y: maximum Y the board's top edge may reach (to avoid overlapping content above).
    """
    left_margin = 50
    right_margin = 50
    bottom_margin = 40
    title_text = "Lap Board"
    title_font = "Helvetica-Bold"
    title_font_size = 12
    title_gap = 6  # space between title and board

    # Determine waves ordered by start offset if available to reflect race order
    if "Start Offset" in df.columns:
        wave_first_offsets = df.groupby("Wave")["Start Offset"].first()
        waves_order = wave_first_offsets.sort_values().index.tolist()
        start_offset_by_wave = wave_first_offsets.to_dict()
    else:
        waves_order = list(df.groupby("Wave").groups.keys())
        start_offset_by_wave = {}

    n_waves = max(1, len(waves_order))

    # Compute the maximum available height for the board (space below other content)
    # Leave room for the title above the board so it does not overlap content.
    available_h = max(0, bottom_limit_y - bottom_margin - (title_font_size + title_gap))
    if available_h <= 0:
        return  # No room; skip drawing

    # Target a 16:9 aspect; choose width first and fit height, then clamp to available height
    board_max_w = max(100, width - (left_margin + right_margin))
    ideal_h = board_max_w * 9.0 / 16.0
    board_h = min(ideal_h, available_h)
    board_w = board_h * 16.0 / 9.0

    # Shrink the lapboard by ~30%
    scale = 0.70
    board_w *= scale
    board_h *= scale

    # Anchor at bottom, horizontally aligned to left margin
    board_x = left_margin
    board_y = bottom_margin

    # Draw title above the board, left-justified
    c.setFont(title_font, title_font_size)
    c.setFillColor(colors.black)
    c.drawString(board_x, board_y + board_h + title_gap, title_text)

    # Draw outer rectangle
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.rect(board_x, board_y, board_w, board_h, stroke=1, fill=0)

    # Split into N vertical windows
    window_w = board_w / n_waves
    window_h = board_h

    # Vertical split lines
    for i in range(1, n_waves):
        x = board_x + i * window_w
        c.line(x, board_y, x, board_y + window_h)

    # Text styles
    title_font = "Helvetica-Bold"
    cat_font = "Helvetica"
    label_font = "Helvetica-Bold"
    label_font_size = 25  # increased ~250% for prominence

    # For each window, draw wave name and its categories
    def index_to_letters(i: int) -> str:
        # Excel-like column naming: 0->A, 25->Z, 26->AA, ...
        s = ""
        n = i
        while True:
            n, r = divmod(n, 26)
            s = chr(ord('A') + r) + s
            if n == 0:
                break
            n -= 1
        return s

    for idx, wave in enumerate(waves_order):
        wx = board_x + idx * window_w
        wy = board_y

        # Window padding
        pad_x = 6
        pad_top = 6
        pad_between = 4

        # Title (Wave name + start offset in m:ss if available)
        c.setFont(title_font, 12)
        minutes_sec = None
        if wave in start_offset_by_wave and start_offset_by_wave[wave] is not None:
            try:
                minutes = int(start_offset_by_wave[wave] // 60)
                minutes_sec = f"{minutes}:00"
            except Exception:
                minutes_sec = None
        title = f"{wave}"
        if minutes_sec is not None:
            title = f"{wave} : {minutes_sec}"
        # Truncate title to fit within window width
        max_title_chars = max(1, int((window_w - 2 * pad_x) / (0.6 * 12)))
        title_draw = title if len(title) <= max_title_chars else (title[:max_title_chars - 1] + "\u2026")
        c.drawString(wx + pad_x, wy + window_h - pad_top - 12, title_draw)

        # Collect categories for this wave
        cats = (
            df[df["Wave"] == wave]["Category"].dropna().astype(str).unique().tolist()
            if "Category" in df.columns else []
        )

        # Determine a font size that roughly fits all category lines
        max_lines = max(1, int((window_h - (pad_top + 16)) // 12))  # assuming 12pt baseline
        # Start with 11pt and reduce modestly for many categories
        base_cat_size = 11
        if len(cats) > max_lines:
            # scale down but clamp to readable 8pt minimum
            scale = max(8.0 / base_cat_size, min(1.0, max_lines / float(len(cats))))
            cat_size = max(8.0, base_cat_size * scale)
        else:
            cat_size = base_cat_size

        c.setFont(cat_font, cat_size)

        # Draw categories as simple lines, stop if we run out of space
        line_h = cat_size + pad_between
        y = wy + window_h - pad_top - 12 - pad_between - line_h
        for cat in cats:
            if y < wy + 6:
                break
            # Truncate category to fit window width (approx character width 0.5*pt)
            max_chars = max(1, int((window_w - 2 * pad_x) / (0.5 * cat_size)))
            text = cat if len(cat) <= max_chars else (cat[:max_chars - 1] + "\u2026")
            c.drawString(wx + pad_x, y, text)
            y -= line_h

        # Add window label (A, B, C, ...) at bottom-left of each window
        c.setFont(label_font, label_font_size)
        c.drawString(wx + pad_x, wy + 6, index_to_letters(idx))

        # Add time marker at bottom-right of each window (e.g., 0:00)
        time_font_size = max(8, int(label_font_size * 0.8))
        c.setFont(label_font, time_font_size)
        c.drawRightString(wx + window_w - pad_x, wy + 6, "0:00")
    # done


def page1_table(c, width, height, df, landScape=False, category_bib_ranges=None ):
    if category_bib_ranges is None:
        category_bib_ranges = {}
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
        participant_rows = wave_df
        if "Is Participant" in wave_df.columns:
            participant_rows = wave_df[wave_df["Is Participant"]]
        print(f"Wave {wave}: {len(participant_rows)} starters")
        print(f"Wave  wave_df: {wave_df}", file=sys.stderr)
        print(f"Wave  wave_df: Distance {wave_df['Distance'].iloc[0]}", file=sys.stderr)
        print(f"Wave  wave_df: Laps {wave_df['Laps'].iloc[0]}", file=sys.stderr)
        print(f"Wave  wave_df: Minutes {wave_df['Minutes'].iloc[0]}", file=sys.stderr)

        print(f'Wave row[{i}] Extra', file=sys.stderr)
        styles.append(("LINEBELOW", (0, 2*i + 1), (-1, 2*i + 1), 2, colors.whitesmoke))
        table_data.append(["", "", "", "", ""])  # **Empty row for spacing**

        # **Extract formatted categories (already includes gender)**
        formatted_categories = wave_df["Categories"].iloc[0]
        category_list = [c.strip() for c in formatted_categories.split(",") if c.strip()]
        category_counts = participant_rows.groupby("Category").size().to_dict()

        formatted_categories = ",\n".join(
            f"{category} {category_bib_ranges.get(category, '')}".strip()
            for category in category_list
        )
        category_starters = "+".join(str(category_counts.get(category, 0)) for category in category_list)
        print(f"Formatted Categories: {formatted_categories}", file=sys.stderr)
        print(f"Category Starters: {category_starters}", file=sys.stderr)
        print(f"Number of Categories: {len(category_list)}", file=sys.stderr)

        wave_starters = f"{len(participant_rows)}"
        if len(category_list) > 1:
            wave_starters += f"\n{category_starters}"

        total_starters += len(participant_rows)

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
    table_bottom_y = height - 190 - table_height
    table.drawOn(c, 50, table_bottom_y)  # **Ensures extra space below header**

    return total_starters, table_bottom_y

def truncate_text(text, max_length):
    """Truncate text to fit within max_length, adding '...' if necessary."""
    return text if len(text) <= max_length else text[:max_length-3] + "..."

def render_first_page(self, event_id, c, page_num, total_pages, landScape=False, category_bib_ranges=None):
    """Render only the first (title/summary) page for a given event onto an existing canvas.

    Draws header/footer, event title/time, wave summary table, total starters, and the lapboard graphic.
    Ends with a page break (showPage).
    """
    # Resolve page size for orientation
    width, height = (landscape(letter) if landScape else letter)

    # Validate event and build DataFrame filtered to this event
    event = self.events.get(event_id)
    if not event:
        print(f"Error: Event {event_id} not found (render_first_page).", file=sys.stderr)
        return False

    df = self.to_dataframe(category_bib_ranges=category_bib_ranges)
    if "Event ID" not in df.columns:
        print("Error: 'Event ID' column missing from DataFrame! (render_first_page)", file=sys.stderr)
        return False

    df = df[df["Event ID"] == event_id]
    if df.empty:
        print(f"Warning: No waves found for event {event_id}. Skipping page.", file=sys.stderr)
        return False

    # Header/footer + watermark
    watermark = self.should_watermark(event["event_start_time"])
    self.draw_preliminary_watermark(c, width, height, watermark)
    self.draw_header_footer(c, width, height, page_num, total_pages)

    # Generated timestamp (top-left)
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 30, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Event title and time
    c.setFont("Helvetica-Bold", 32)
    c.drawString(50, height - 100, self.competition_long_name)

    c.setFont("Helvetica", 28)
    c.drawString(50, height - 140, event["event_start_time"].strftime("%Y-%m-%d %I:%M %p"))

    # Wave summary table
    total_starts, table_bottom_y = page1_table(
        c, width, height, df, landScape=landScape, category_bib_ranges=category_bib_ranges
    )

    c.setFont("Helvetica", 20)
    c.drawString(50, height - 180, f"Total Starters: {total_starts}")

    # Lapboard graphic under the table
    try:
        draw_lapboard(c, width, height, df, bottom_limit_y=table_bottom_y - 10, landScape=landScape)
    except Exception as e:
        print(f"Lapboard draw error (render_first_page): {e}", file=sys.stderr)

    c.showPage()
    return True

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
        print(f"Warning: No waves found for event {event_id}.", file=sys.stderr)
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

    participant_df = df[df["Is Participant"]] if "Is Participant" in df.columns else df
    total_participants = len(participant_df)

    if total_participants == 0:
        total_pages = 1
    else:
        # **Fix: Properly account for the first-page participants**
        total_pages = sum([
            1 + max(0, -(-(len(wave_df) - first_page_rows) // remaining_page_rows))  # **Fix for additional pages**
            for _, wave_df in participant_df.groupby("Wave")
        ]) + 1  # **+1 for title page**

    # **Title Page**
    watermark = self.should_watermark(event["event_start_time"])
    self.draw_preliminary_watermark(c, width, height, watermark)
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

    total_starters = total_participants
    print('Total Starters:', total_starters, file=sys.stderr)

    # **Wave Summary Table (Formatted)**
    total_starts, table_bottom_y = page1_table(
        c, width, height, df, landScape=landScape, category_bib_ranges=category_bib_ranges
    )
    print('Total Starters:', total_starters, file=sys.stderr)
    c.setFont("Helvetica", 20)
    c.drawString(50, height - 180, f"Total Starters: {total_starts}")

    # **Lapboard graphic (16:9) below summary table**
    try:
        draw_lapboard(c, width, height, df, bottom_limit_y=table_bottom_y - 10, landScape=landScape)
    except Exception as e:
        print(f"Lapboard draw error: {e}", file=sys.stderr)

    c.showPage()


    if total_participants == 0:
        c.save()
        return

    # **Process Riders (Grouped by Wave)**
    page_num = 2
    for wave, wave_df in participant_df.groupby("Wave"):
        self.draw_preliminary_watermark(c, width, height, watermark)
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
            if not watermark and i % 2 == 0:
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
            self.draw_preliminary_watermark(c, width, height, watermark)
            self.draw_header_footer(c, width, height, page_num, total_pages)

            # Move table further DOWN on subsequent pages
            #y_position = height - 800  # **Start table at top of new page**
            y_position = 60  # **Start table at top of new page**

            table_data = [["Bib", "Name", "Team", "Category", "UCI ID"]]
            styles = init_styles.copy()
            # XXX Teams column is not getting truncated, a long team name gets printed overtop the Category column
            for i, (_, row) in enumerate(remaining_participants.iloc[:remaining_page_rows].iterrows()):
                if not watermark and i % 2 == 0:
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
