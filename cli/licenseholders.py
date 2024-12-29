#!/usr/bin/env python3

import sys
import os
#import argparse
import autopage, argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from libs.login import session_login
from libs.upload import upload_file
from libs.findsql import find_competition

def login_and_upload(
    base_url,
    username,
    password,
    file_path,
):
    next_path = "RaceDB/LicenseHolders/LicenseHoldersImportExcel/"

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
    # set_team_all_disciplines = True
    # update_license_codes = True
    # ok-submit = OK
    upload_file(session, base_url, next_path, tableCheck=True, 
                files= { 'excel_file': open(file_path, 'rb'), },
                data={
                    "set_team_all_disciplines": "on",
                    "update_license_codes": "on",
                    "ok-submit": "OK",
                },
                )

epilog = """
The licenseholders.py script will upload a license holder XLSX file to RaceDB.

It is the equivalent to:
    - RaceDB / License Holders / License Holders Import Excel form

With these options:

    set_team_all_disciplines: on
    replace_seasons_RFID_TAGS: off
    replace_seasons_BIB_Numbers: off
    update_license_codes: on

This script should be used to update the license holders in the database prior
to importing pre-registration data.

The environment variables RACEDB_USERNAME and RACEDB_PASSWORD will be used 
if to set the authentication username and secret.
"""
def main():
    parser = argparse.ArgumentParser(
            description="RaceDB update license holders from xlsx.", 
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=epilog)
    parser.add_argument('--host', type=str, default='localhost', help='database host')
    parser.add_argument('--username', type=str, default=None, help='authentication username')
    parser.add_argument('--password', type=str, default=None, help='authentication password')
    parser.add_argument('--stderr', "--debug", action='store_true', help='Enable stderr output.')
    parser.add_argument('--xlsx', type=str, default='', help='License Holder XLSX file for upload')

    args = parser.parse_args()
    
    base_url = args.host        # e.g. http://192.168.250.51:9080
    username = args.username    # e.g. super
    password = args.password    # e.g. super
    file_path = args.xlsx       # e.g. /path/to/file.xlsx

    os.environ['LESS'] += f" -F --quit-if-one-screen"
    stderr_context = sys.stderr if args.stderr else open('/dev/null', 'w') 
    with stderr_context as sys.stderr, autopage.AutoPager(line_buffering=autopage.line_buffer_from_input()) as sys.stdout:
        login_and_upload(
            base_url=base_url,
            username=username,
            password=password,
            file_path=file_path,
        )

if __name__ == "__main__":
    main()
    exit(0)


