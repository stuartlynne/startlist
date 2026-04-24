import re


def sanitize_filename_part(value, compact=False):
    text = str(value or "").strip()
    text = re.sub(r"\s*[\[\(][^\]\)]*[\]\)]\s*", " ", text)
    text = re.sub(r"[^A-Za-z0-9._-]+", "_" if not compact else "", text)
    if compact:
        text = re.sub(r"_+", "", text)
        text = text.replace(" ", "")
    else:
        text = re.sub(r"_+", "_", text)
    return text.strip("._-")
