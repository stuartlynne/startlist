#!/usr/bin/env python3
# vim: shiftwidth=4 tabstop=4 expandtab


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
from libs.download import download_file
from libs.savefile import save_file
#from pager import open_pager, close_pager, PagerContext

# https://racedb.wimsey.online/RaceDB/Competitions/CompetitionDashboard/395/   

def login_and_download(
    base_url,
    username,
    password,
    outdir=".",
    filename=None,
    competition_id=None,
):
    #next_path = f"RaceDB/NumberSets/NumberSetManage/{competition_id}/NumberSetUploadExcel/{competition_id}/"
    download_path = f"RaceDB/Competitions/CompetitionExport/{competition_id}/"

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
    final_response = download_file(session, base_url, download_path, 
            data = {
                'export_as_template': 'on',
                'remove_ftp_info': 'on',
                'excel-export-submit': 'Export to Excel',
                },
                )
    if not final_response:
        print("No response from download_file", file=sys.stderr)
        return
    
    # 4) Determine filename from 'Content-Disposition' if present
    filename = save_file(final_response, outdir=outdir, filename=filename)
    print(f"Saved to {filename}")


epilog = """

The temploate script will download a competition template from RaceDB.

This is the equivalent to:
    RaceDB / Competitions / Competition Export

With these options:
    export_as_template: on
    remove_ftp_info: on

This can be used to save a competition template to a file for later use
with the competition script.

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
    parser.add_argument('--template_date', type=str, help='Copy the competition from this date.')
    parser.add_argument('--template_format', type=str, default=None, help='Copy the most recent competition with this category format.')
    parser.add_argument('--name', type=str, help='Name of the competition.')
    parser.add_argument('--outdir', type=str, default=".", help='Optional directory for downloaded file.')
    parser.add_argument('--stderr', "--debug", action='store_true', help='Enable stderr output.')
    parser.add_argument('--stderrdup', "--debugdup", action='store_true', help='Enable stderr output.')

    #parser.add_argument('--xlsx', type=str, default='', help='Pre-Registration Data XLSX file for upload')

    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])
    
          
    base_url = args.host   # e.g. http://192.168.250.51:9080
    username = args.username   # e.g. super
    password = args.password   # e.g. super
    template_date = args.template_date
    template_format = args.template_format
    #file_path = args.xlsx  # e.g. /path/to/file.xlsx

    if base_url is None:
        base_url = os.environ.get("RACEDB_URL", "http://localhost:8000")

    host = base_url.removeprefix("https://").removeprefix("http://").split(":")[0]
    name = None
    print(f"Host: {host} Name: {name} Date: {template_date} Format: {template_format} ")
    try:
        conn, cur, competition_id, competition_name, competition_long_name, competition_start_date, number_set_id = find_competition(host, name, 
                date=template_date, category_format=template_format)
    except (TypeError, ValueError) as e:
        print(f"Competition not found: {name} {template_date} {template_format}")
        exit(1)

    filename = f"{competition_name}-{competition_start_date}.gz".replace(" ", "_")


    with AutoPagerEx(stderr=args.stderr, stderrdup=args.stderrdup, line_buffering=autopage.line_buffer_from_input()) as (sys.stdout, sys.stderr):
        login_and_download(
            base_url=base_url,
            username=username,
            password=password,
            outdir=args.outdir,
            filename=filename,
            competition_id=competition_id,
        )

if __name__ == "__main__":
    main()
    exit(0)

