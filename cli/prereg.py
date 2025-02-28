#!/usr/bin/env python3

import sys
import os
import subprocess
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

import autopage
from autopage import argparse

from libs.autopageex import AutoPagerEx
from libs.login import session_login
from libs.upload import upload_file
from libs.findsql import find_competition
#from pager import open_pager, close_pager, PagerContext

# https://racedb.wimsey.online/RaceDB/Competitions/CompetitionDashboard/395/   

def login_and_upload(
    base_url,
    username,
    password,
    file_path,
    competition_id,
):
    next_path = f"RaceDB/Competitions/CompetitionDashboard/{competition_id}/UploadPrereg/{competition_id}/"
    """
    1) Logs into RaceDB (Django) by:
       - GETing the login form to retrieve the CSRF cookie + token.
       - POSTing username, password, next, plus that CSRF token.
    2) Navigates to the next_path page (upload form).
    3) Parses the <form> action properly (handling blank or relative).
    4) Uploads a file with the new CSRF token from the upload form.
    5) Extracts the <pre> text from the server's response.
    """

    # 1 and 2
    session = session_login(base_url, username, password)

    # 3, 4, and 5
    upload_file(session, base_url, next_path, preCheck=True,
                files={'excel_file': open(file_path, 'rb')},
                data = { 'clear_existing': 'on', 'ok-submit': 'OK'},
                )
epilog = """

The prereg.py script will upload a pre-registration XLSX file to RaceDB.

This is the equivalant to:

    - RaceDB / Competitions / Competition Dashboard / Upload Prereg

With these options:
    - assign_bib_numbers: off
    - clear_existing: on

The licenseholder script should be used to update license holders prior to this script
because Prereg data is intended to match existing license holders to the competition. 

The startlists script should be used to generate CrossMgr and startlists files
after this script has been run.

The startlists script can also be used to show information about the competition 
participants.


The environment variables RACEDB_USERNAME and RACEDB_PASSWORD will be used 
if to set the authentication username and secret.
"""

def main():
    parser = argparse.ArgumentParser(
            description="Import RaceDB competition pre-registration xlsx file.", 
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=epilog)
    parser.add_argument('--host', type=str, default=None, help='database host')
    parser.add_argument('--username', type=str, default=None, help='authentication username')
    parser.add_argument('--password', type=str, default=None, help='authentication password')
    parser.add_argument('--date', type=str, help='Start date of the competition in YYYY-MM-DD format.')
    parser.add_argument('--format', type=str, default=None, help='Copy the most recent competition with this category format.')
    parser.add_argument('--name', type=str, help='Name of the competition.')
    parser.add_argument('--xlsx', type=str, default='', help='Pre-Registration Data XLSX file for upload')
    parser.add_argument('--stderr', "--debug", action='store_true', help='Enable stderr output.')
    parser.add_argument('--stderrdup', "--debugdup", action='store_true', help='Enable stderr output.')

    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])
    
          
    base_url = args.host   # e.g. http://192.168.250.51:9080
    username = args.username   # e.g. super
    password = args.password   # e.g. super
    file_path = args.xlsx  # e.g. /path/to/file.xlsx
    date = args.date
    category_format = args.format

    if base_url is None:
        base_url = os.environ.get("RACEDB_URL", "http://localhost:8000")
    host = base_url.removeprefix("https://").removeprefix("http://").split(":")[0]
    name = None
    print(f"Host: {host} Name: {name} Date: {date}")
    try:
        conn, cur, competition_id, competition_name, competition_long_name, competition_start_date, number_set_id = find_competition(host, name, 
                date=date, category_format=category_format)
    except (TypeError, ValueError) as e:
        print(f"Competition not found: {name} {template_date} {template_format}")
        exit(1)
    print(f"Competition ID: {competition_id} Name: {competition_name} Long Name: {competition_long_name} Date: {date} Format: {category_format}")
    #competition_id = "396"

    
    with AutoPagerEx(stderr=args.stderr, stderrdup=args.stderrdup, line_buffering=autopage.line_buffer_from_input()) as (sys.stdout, sys.stderr):
        login_and_upload(
            base_url=base_url,
            username=username,
            password=password,
            file_path=file_path,
            competition_id=competition_id,
        )

if __name__ == "__main__":
    main()
    exit(0)

