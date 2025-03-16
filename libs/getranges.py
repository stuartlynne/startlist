def get_ranges(bib_list):
    """Convert a list of bibs into a compact range string, merging decade-aligned and 100-range blocks properly."""
    if not bib_list:
        return "N/A"

    bib_list = sorted(set(bib_list))  # Ensure uniqueness and sorting
    temp_ranges = []
    start = bib_list[0]
    end = start

    # Step 1: Identify contiguous blocks
    for bib in bib_list[1:]:
        if bib == end + 1:  # Extend contiguous range
            end = bib
        else:
            temp_ranges.append((start, end))
            start = bib
            end = bib

    temp_ranges.append((start, end))  # Add final range

    # Step 2: Expand to decade ranges
    decade_ranges = []
    for start, end in temp_ranges:
        decade_start = start - (start % 10)  # Snap to decade start
        decade_end = (end - (end % 10)) + 9  # Snap to decade end

        # If previous range is in the same 100-block, merge
        if decade_ranges and decade_ranges[-1][1] + 1 >= decade_start and (decade_ranges[-1][0] // 100 == decade_start // 100):
            prev_start, prev_end = decade_ranges.pop()
            decade_ranges.append((prev_start, max(prev_end, decade_end)))
        else:
            decade_ranges.append((decade_start, decade_end))

    # Step 3: Coalesce full hundred-based ranges if no other category bibs exist between them
    final_ranges = []
    current_start, current_end = decade_ranges[0]

    for new_start, new_end in decade_ranges[1:]:
        if new_start // 100 == current_start // 100:  # Merge if within the same hundred block
            current_end = max(current_end, new_end)
        else:
            final_ranges.append(f"{current_start}-{current_end}")
            current_start, current_end = new_start, new_end

    final_ranges.append(f"{current_start}-{current_end}")  # Add last range

    return ",".join(final_ranges)


if __name__ == "__main__":
    category_bibs = {
        "Elite (Open)": {0, 9, 10, 15, 20, 30, 40, 45},
        "Master A (Men)": {700, 710, 720, 730, 740, 750, 751, 752, 753, 754, 755, 756, 757, 758, 759, 801, 810, 820,},
        "Cat 3 (Men)": {300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 
                        320, 321, 322, 323, 324, 325, 326, 327, 328, 329}
    }

    print("Category".ljust(20), "Bibs")
    for category, bibs in category_bibs.items():
        print(category.ljust(20), get_ranges(bibs))

