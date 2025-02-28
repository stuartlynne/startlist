#!/usr/bin/env python3
# vim: shiftwidth=4 tabstop=4 expandtab

import sys
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

import autopage
from autopage import argparse

from libs.autopageex import AutoPagerEx
from libs.login import session_login
from libs.upload import upload_file
from libs.findsql import find_numberset
from libs.download import download_file
from libs.savefile import save_file

def login_and_upload(
    base_url,
    username,
    password,
    outdir=".",
    file_path=None,
    numberset_id=None,
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

    if file_path:
        upload_path = f"RaceDB/NumberSets/NumberSetEdit/{numberset_id}/NumberSetManage/{numberset_id}/NumberSetUploadExcel/{numberset_id}/"
        upload_file(session, base_url, upload_path, preCheck=True, 
                    files= { 'excel_file': open(file_path, 'rb'), },
                    data={
                        'ok-submit': 'Ok'
                    },)
    else:
        download_path = f"RaceDB/NumberSets/NumberSetEdit/{numberset_id}/NumberSetManage/{numberset_id}/"
        final_response = download_file(session, base_url, download_path, 
                    data={
                        "search_text": '',
                        'search_bib': '',
                        'excel-export-submit': 'Export to Excel'
                    },)
        if not final_response:
            print("No response from download_file", file=sys.stderr)
            return
        
        # 4) Determine filename from 'Content-Disposition' if present
        save_file(final_response, outdir=outdir, filename=None)


epilog = """
The numberset script can be used to download or upload number set data.

This is the equivalent to:
    - RaceDB / Number Sets / Number Set Manage / Export to Excel
    - RaceDB / Number Sets / Number Set Manage / Update from Excel


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
    parser.add_argument('--numberset', type=str, default=None, help='Number Set name')
    parser.add_argument('--xlsx', type=str, default=None, help='License Holder XLSX file for upload')
    parser.add_argument('--stderr', "--debug", action='store_true', help='Enable stderr output.')
    parser.add_argument('--outdir', type=str, default=".", help='Optional directory for downloaded file.')
    parser.add_argument('--stderrdup', "--debugdup", action='store_true', help='Enable stderr output.')

    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])
    
    base_url = args.host        # e.g. http://192.168.250.51:9080
    username = args.username    # e.g. super
    password = args.password    # e.g. super
    numberset = args.numberset  # e.g. LMCX2022
    file_path = args.xlsx       # e.g. /path/to/file.xlsx

    host = base_url.removeprefix("https://").removeprefix("http://").split(":")[0]

    try:
        conn, cur, numberset_id, numberset_name, numberset_description, numberset_sponsor = find_numberset(host, numberset)
    except TypeError as e:
        print(f"Numberset not found: {name} {date}")
        exit(1)

    with AutoPagerEx(stderr=args.stderr, stderrdup=args.stderrdup, line_buffering=autopage.line_buffer_from_input()) as (sys.stdout, sys.stderr):
        login_and_upload(
            base_url=base_url,
            username=username,
            password=password,
            outdir=args.outdir,
            file_path=file_path,
            numberset_id=numberset_id,
        )

if __name__ == "__main__":
    main()
    exit(0)


