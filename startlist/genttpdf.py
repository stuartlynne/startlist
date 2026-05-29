from datetime import datetime, timedelta

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from .filename import sanitize_filename_part


def format_elapsed_time(value):
    total_seconds = int(round(value or 0))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def detect_interval_seconds(participants):
    start_times = sorted(
        int(round(p.get("start_time") or 0))
        for p in participants
        if p.get("start_time") is not None
    )
    deltas = [
        b - a for a, b in zip(start_times, start_times[1:])
        if b > a
    ]
    if not deltas:
        return 60
    return min(deltas)


def format_clock_time(value, include_seconds=True):
    return value.strftime("%H:%M:%S" if include_seconds else "%H:%M")


class GenTTPDF:
    def __init__(self, date, competition_name, competition_long_name, landscape=False, final=False, detail_column=None):
        self.date = date
        self.competition_name = competition_name
        self.competition_long_name = competition_long_name
        self.landscape = landscape
        self.final = final
        self.detail_column = detail_column
        self.events = {}

    def add_event(self, event_id, event_name, event_start_time):
        self.events[event_id] = {
            'event_name': event_name,
            'event_start_time': event_start_time,
            'waves': {},
            'participants': [],
        }
        self.event_id = event_id

    def add_wave(self, event_id, wave_id, wave_name, start_offset, distance, laps, minutes, categories):
        self.events[event_id]['waves'][wave_id] = {
            'wave_name': wave_name,
            'start_offset': start_offset,
            'distance': distance,
            'laps': laps,
            'minutes': minutes,
            'categories': categories,
        }

    def add_participant(self, event_id, wave_id, wave_name, participant_data):
        participant_data["wave_id"] = wave_id
        participant_data["wave_name"] = wave_name
        self.events[self.event_id]['participants'].append(participant_data)

    def should_watermark(self, event_start_time):
        if self.final:
            return False
        if not isinstance(event_start_time, datetime):
            return True
        cutoff = event_start_time - timedelta(minutes=30)
        return datetime.now() < cutoff

    def draw_preliminary_watermark(self, c, width, height, enabled):
        if not enabled:
            return
        c.saveState()
        c.translate(width / 2.0, height / 2.0)
        c.rotate(-45)
        c.setFont("Helvetica-Bold", 90 if width > height else 108)
        watermark_color = colors.Color(0.4, 0.4, 0.4, alpha=0.15)
        c.setFillColor(watermark_color)
        if hasattr(c, "setFillAlpha"):
            c.setFillAlpha(0.15)
        c.drawCentredString(0, 0, "NOT FINAL")
        c.restoreState()

    def rider_detail_value(self, event, participant):
        wave_id = participant.get("wave_id")
        wave_name = participant.get("wave_name")
        wave = event["waves"].get(wave_id)
        if not wave:
            wave = next(
                (wave for wave in event["waves"].values() if wave["wave_name"] == wave_name),
                None,
            )
        if not wave:
            return ""

        if self.detail_column == "laps":
            laps = wave.get("laps")
            return "" if laps is None else str(int(round(laps)))

        if self.detail_column == "km":
            distance = wave.get("distance")
            laps = wave.get("laps") or 1
            return "" if distance is None else str(int(round(distance)) * int(round(laps)))

        return ""

    def build_slots(self, event):
        participants = sorted(
            event['participants'],
            key=lambda p: (p.get('start_sequence', 999999), p.get('bib') or 0),
        )
        if not participants:
            return [], 60, True

        interval_seconds = detect_interval_seconds(participants)
        include_clock_seconds = any(
            int(round(p.get("start_time") or 0)) % 60 != 0
            for p in participants
            if p.get("start_time") is not None
        )
        max_start = max(int(round(p.get("start_time") or 0)) for p in participants)
        extra_slots = max(10, 600 // max(interval_seconds, 1))
        slot_times = list(range(0, max_start + interval_seconds * extra_slots + 1, interval_seconds))

        participant_by_start = {
            int(round(p.get("start_time") or 0)): p
            for p in participants
        }

        slots = []
        for start_time in slot_times:
            participant = participant_by_start.get(start_time)
            if participant:
                clock = participant.get("scheduled_start_time")
                clock_text = format_clock_time(clock, include_clock_seconds) if clock else ""
                slots.append({
                    "Stopwatch": format_elapsed_time(start_time),
                    "Bib": str(participant.get("bib") or ""),
                    "LastName": str(participant.get("last_name") or ""),
                    "FirstName": str(participant.get("first_name") or ""),
                    "Notes/Delay": "",
                    "Start Time": clock_text,
                    "Detail": self.rider_detail_value(event, participant),
                })
            else:
                event_start = event.get("event_start_time")
                clock_text = ""
                if event_start:
                    clock_text = format_clock_time(event_start + timedelta(seconds=start_time), include_clock_seconds)
                slots.append({
                    "Stopwatch": format_elapsed_time(start_time),
                    "Bib": "",
                    "LastName": "",
                    "FirstName": "",
                    "Notes/Delay": "",
                    "Start Time": clock_text,
                    "Detail": "",
                })
        return slots, interval_seconds, include_clock_seconds

    def pad_slots_for_pages(self, slots, interval_seconds, rows_per_page, event_start_time, include_clock_seconds=True):
        if not slots:
            return slots

        remainder = len(slots) % rows_per_page
        if remainder == 0:
            return slots

        extra_rows = rows_per_page - remainder
        last_elapsed_seconds = (len(slots) - 1) * interval_seconds

        for i in range(1, extra_rows + 1):
            elapsed_seconds = last_elapsed_seconds + i * interval_seconds
            clock_text = ""
            if event_start_time:
                clock_text = format_clock_time(
                    event_start_time + timedelta(seconds=elapsed_seconds),
                    include_clock_seconds,
                )
            slots.append({
                "Stopwatch": format_elapsed_time(elapsed_seconds),
                "Bib": "",
                "LastName": "",
                "FirstName": "",
                "Notes/Delay": "",
                "Start Time": clock_text,
                "Detail": "",
            })

        return slots

    def save(self, category_bib_ranges=None):
        for event_id, event in self.events.items():
            if not event['participants']:
                continue

            generated_at = datetime.now()
            event_start_time = event["event_start_time"].strftime("%H%M")
            competition_slug = sanitize_filename_part(self.competition_name)
            filename = f"{self.date}-{competition_slug}-{event_start_time}-tt-startlist.pdf"
            page_size = landscape(letter) if self.landscape else letter
            width, height = page_size
            c = canvas.Canvas(filename, pagesize=page_size)

            slots, interval_seconds, include_clock_seconds = self.build_slots(event)
            rows_per_page = 30
            slots = self.pad_slots_for_pages(
                slots,
                interval_seconds,
                rows_per_page,
                event["event_start_time"],
                include_clock_seconds=include_clock_seconds,
            )
            total_pages = (len(slots) + rows_per_page - 1) // rows_per_page
            watermark = self.should_watermark(event["event_start_time"])

            margin_left = 0.40 * inch
            top_y = height - 0.63 * inch
            bottom_y = 1.44 * inch
            row_height = (top_y - bottom_y) / (rows_per_page + 1)
            table_bottom_y = top_y - rows_per_page * row_height

            columns = [
                ("Stopwatch", 0.95 * inch),
                ("Bib", 0.60 * inch),
                ("LastName", 1.60 * inch),
                ("FirstName", 1.60 * inch),
                ("Notes/Delay", 1.65 * inch if not include_clock_seconds else 1.35 * inch),
                ("Start Time", 0.60 * inch if not include_clock_seconds else 0.90 * inch),
            ]
            if self.detail_column == "laps":
                columns.append(("Lap", 0.45 * inch))
            elif self.detail_column == "km":
                columns.append(("KM", 0.45 * inch))

            xs = [margin_left]
            for _, col_width in columns:
                xs.append(xs[-1] + col_width)

            def draw_page_header(page_num):
                self.draw_preliminary_watermark(c, width, height, watermark)
                c.setFont("Helvetica-Bold", 8)
                header_name = (
                    f"RaceDB-{sanitize_filename_part(self.competition_name, compact=True)}-{sanitize_filename_part(event['event_name'])}_"
                    f"{self.date}-{event['event_start_time'].strftime('%H%M%S')}-"
                    f"{generated_at.strftime('%Y-%m-%d-%H%M%S')}"
                )
                c.drawString(margin_left, height - 0.22 * inch, header_name)
                c.drawString(width - 1.05 * inch, height - 0.22 * inch, f"Page {page_num}")
                c.setFont("Helvetica", 8)
                c.drawString(margin_left, height - 0.38 * inch, f"Generated: {generated_at.strftime('%Y-%m-%d %H:%M:%S')}")

                c.setFont("Helvetica-Bold", 8)
                for i, (title, _) in enumerate(columns):
                    c.drawString(xs[i] + 2, top_y + 5, title)

                c.setStrokeColor(colors.black)
                for x in xs:
                    c.line(x, top_y, x, table_bottom_y)
                c.line(xs[0], top_y, xs[-1], top_y)

                c.setFont("Helvetica-Bold", 8)
                c.drawString(margin_left + 0.2 * inch, 0.62 * inch, 'Notes: __________________________________________________________________________________________')
                c.drawString(margin_left + 0.2 * inch, 0.38 * inch, '________________________________________________________________________________________________')
                c.drawString(margin_left + 0.2 * inch, 0.12 * inch, 'Starter: _______________________________________________   Actual Start Time: __________________')

            def draw_row(index, row):
                y = top_y - (index + 1) * row_height
                c.line(xs[0], y, xs[-1], y)

                values = [
                    row["Stopwatch"],
                    row["Bib"],
                    row["LastName"],
                    row["FirstName"],
                    row["Notes/Delay"],
                    row["Start Time"],
                ]
                if self.detail_column in ("laps", "km"):
                    values.append(row["Detail"])

                fonts = [
                    ("Helvetica", 16),
                    ("Helvetica", 16),
                    ("Helvetica", 16),
                    ("Helvetica", 16),
                    ("Helvetica", 14),
                    ("Helvetica", 16),
                ]
                if self.detail_column in ("laps", "km"):
                    fonts.append(("Helvetica", 16))

                for i, value in enumerate(values):
                    font_name, font_size = fonts[i]
                    c.setFont(font_name, font_size)
                    if i == 1:
                        c.drawCentredString(
                            xs[i] + (xs[i + 1] - xs[i]) / 2,
                            y + row_height / 2 - 0.11 * inch,
                            str(value),
                        )
                    elif self.detail_column in ("laps", "km") and i == len(values) - 1:
                        c.drawCentredString(
                            xs[i] + (xs[i + 1] - xs[i]) / 2,
                            y + row_height / 2 - 0.11 * inch,
                            str(value),
                        )
                    else:
                        c.drawString(xs[i] + 2, y + row_height / 2 - 0.11 * inch, str(value))

            for page_num in range(total_pages):
                if page_num:
                    c.showPage()
                draw_page_header(page_num + 1)
                page_rows = slots[page_num * rows_per_page:(page_num + 1) * rows_per_page]
                for row_index, row in enumerate(page_rows):
                    draw_row(row_index, row)
                c.line(xs[0], table_bottom_y, xs[-1], table_bottom_y)

            c.save()
            print(f"Generated TT PDF: {filename} interval={interval_seconds}s rows={len(slots)}")

        return "TT PDF files generated."
