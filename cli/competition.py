#!/usr/bin/env python3

import sys
import os
import subprocess
import requests
import io
import json
import gzip
#import argparse
import autopage, argparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from libs.login import session_login
from libs.upload import upload_file
from libs.findsql import find_competition
from libs.download import download_file
#from pager import open_pager, close_pager, PagerContext

# create competition
# Check if a competition exists with the specified name and date, if not create 
# a new competition with the specified name and date using a previous competiton
# as a template.

# https://racedb.wimsey.online/RaceDB/Competitions/CompetitionDashboard/395/   
# http://192.168.250.51:9080/RaceDB/Competitions/CompetitionImport/


import json
import gzip
import io
import requests

def dict_to_gzip_filelike(data_dict):
    """
    Converts a Python dictionary to gzipped JSON in memory
    and returns a file-like object (BytesIO).
    """
    # Convert dictionary to JSON string
    data_str = json.dumps(data_dict)
    
    # Compress JSON string to gzipped bytes
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='wb') as gz:
        gz.write(data_str.encode('utf-8'))
    
    # Reset the pointer to the beginning of the buffer
    buffer.seek(0)
    return buffer

# Example usage:
# 1. Create (or have) the Python dictionary
#data_dict = {"foo": "bar", "nested": {"x": 1, "y": 2}}

# 2. Get a file-like object for gzipped JSON
#gz_filelike = dict_to_gzip_filelike(data_dict)

# 3. Include that object in the 'files' dictionary
#    The key is the form field name. 
#    The value is a tuple of (filename, fileobj, content_type).
#files = {
#    'json_file': ('data.json.gz', gz_filelike, 'application/gzip'),
#}

# 4. Send via a POST request
#url = "https://example.com/your-upload-endpoint"
#response = requests.post(url, files=files)
#
#print(response.status_code)
#print(response.text)



def login_and_create(
    racedb,
    username,
    password,
    competition_id,
    template_file,
    start_date,
    new_name,
    replace,
):
    download_path = f"RaceDB/Competitions/CompetitionExport/{competition_id}/"
    upload_path = f"RaceDB/Competitions/CompetitionImport/"
    
    """
    1) Logs into RaceDB (Django) by:
       - GETing the login form to retrieve the CSRF cookie + token.
       - POSTing username, password, next, plus that CSRF token.
    2) Download template, unzip and return JSON
    3) Update JSON with new date and name
    4) Uploads a file with the new CSRF token from the upload form.
    5) Extracts the <pre> text from the server's response.
    """
    print('Create: {racedb} template competition_id: {competition_id} start_date: {start_date} new_name: {new_name}')

    # 1 
    session = session_login(racedb, username, password)

    # 2
    final_response = download_file(session, racedb, download_path, 
            data = {
                'export_as_template': 'on',
                'remove_ftp_info': 'on',
                'ok-submit': 'OK',
                },)

    # save response into BytesIO 
    # XXX read template_file if not None
    if template_file:
        files = { "excel_file": open(template_file, 'rb'), }
    else:
        buffer = io.BytesIO(final_response.content)
        buffer.seek(0)
        files = { "json_file": ('json.gz', io.BytesIO(final_response.content), 'application/gzip'), }
    upload_file(session, racedb, upload_path, preCheck=True,
                files=files,
                data={
                    'name': new_name,
                    'start_date': start_date,
                    'replace': 'on' if replace else 'off',
                    'import_as_template': 'on',
                    'ok-submit': 'OK',
                },)

    return

    with gzip.GzipFile(fileobj=io.BytesIO(final_response.content), mode='rb') as f:
        decompressed = f.read()
        jsondata = json.loads(decompressed)

    for d in jsondata:
        if d['model'] != 'core.competition':
            continue
        d['fields']['date'] = start_date
        d['fields']['name'] = new_name
    
    # 4
    gz_filelike = dict_to_gzip_filelike(jsondata)
    upload_file(session, racedb, upload_path, filename=None, 
                #files={'file': ('json_file', json.dumps(jsondata), 'application/json')},
                files={'file': gz_filelike, },
                data={
                    'name': new_name,
                    'start_date': start_date,
                    'replace': 'on' if replace else 'off',
                    'import_as_template': 'on',
                    'ok-submit': 'OK',
                },)


epilog = """
The competition script will quickly create a new RaceDB competition by using
either an existing competition as a template or by using a previously downloaded
competition template file. The competition will be created with the specified
start date and name. If the competition already exists, the script will exit
unless the --replace argument is used.

competition.py --host http://192.168.250.51:9080 \
        --category_format lmcx2024 \
        --start_date 2024-12-30 --new_name "LMCX Race" 

The new competition will be created with the specified start date and name
and have no pre-registration data. 

The environment variables RACEDB_USERNAME and RACEDB_PASSWORD will be used 
if to set the authentication username and secret.
"""

def main():
    parser = argparse.ArgumentParser(
            description="Import RaceDB competition pre-registration xlsx file.", 
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=epilog)
    parser.add_argument('--host', type=str, default='http://localhost:8000/', help='RaceDB Server URL')
    parser.add_argument('--username', type=str, default=None, help='authentication username')
    parser.add_argument('--password', type=str, default=None, help='authentication password')
    parser.add_argument('--template_date', type=str, help='Copy the competition from this date.')
    parser.add_argument('--category_format', type=str, default=None, help='Copy the most recent competition with this category format.')
    parser.add_argument('--template_file', type=str, default=None, help='Specify a template file.')
    parser.add_argument('--start_date', type=str, default=None, help='Start date of the competition in YYYY-MM-DD format.')
    parser.add_argument('--new_name', type=str, default=None, help='Name of the competition.')
    parser.add_argument('--replace', type=bool, default=False, help='Replace existing competition')
    parser.add_argument('--stderr', "--debug", action='store_true', help='Enable stderr output.')
                

    #parser.add_argument('--xlsx', type=str, default='', help='Pre-Registration Data XLSX file for upload')

    args = parser.parse_args()
    
          
    racedb = args.host   # e.g. http://192.168.250.51:9080
    username = args.username   # e.g. super
    password = args.password   # e.g. super
    template_date = args.template_date
    category_format = args.category_format
    template_file = args.template_file
    new_name = args.new_name
    start_date = args.start_date
    replace = args.replace
    #file_path = args.xlsx  # e.g. /path/to/file.xlsx

    # 1. If competition exists and replace flag is not set then exit
    # 2. Find the competition to copy and Download the previous competition, unzip and return JSON
    # 3. Update JSON with new date and name
    # 4. Compress JSON and Upload to create a new competition, possibly with replace: On

    dbHost = racedb.removeprefix("https://").removeprefix("http://").split(":")[0]
    print(f"DBHost: {dbHost} new_name: {new_name} start_date: {start_date} category_format: {category_format} {template_date} {template_file} {replace}", file=sys.stderr)

    os.environ['LESS'] += f" -F --quit-if-one-screen"
    stderr_context = sys.stderr if args.stderr else open('/dev/null', 'w') 
    with stderr_context as sys.stderr, autopage.AutoPager(line_buffering=autopage.line_buffer_from_input()) as sys.stdout:
        competition_id = None
        # check 
        if not replace:
            try:
                conn, cur, competition_id, competition_name, competition_long_name, competition_start_date, number_set_id = find_competition(dbHost, None, date=start_date)
            except TypeError as e:
                print(f"Competition not found: {start_date}")

            if competition_id:
                print(f"Competition: {competition_start_date} {competition_name} already exists.")
                exit(0)

        if not template_file:
            conn, cur, competition_id, competition_name, competition_long_name, competition_start_date, number_set_id = find_competition(dbHost, None, 
                    date=template_date, category_format=category_format)
        else:
            competition_id = None  

        if not competition_id:
            print("Competition: {template_date} not found.")
            exit(1)

        print(f"Competition ID: {competition_id} Name: {competition_name} Long Name: {competition_long_name} Date: {start_date}")

        #filename = f"{competition_name}-{date}.gz".replace(" ", "_")


        login_and_create(
            racedb=racedb,
            username=username,
            password=password,
            start_date=start_date,
            new_name=new_name,
            competition_id=competition_id,
            template_file=template_file,
            replace=args.replace,
        )

if __name__ == "__main__":
    main()
    exit(0)

