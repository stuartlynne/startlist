# startlist
# Thu Sep 26 03:58:26 PM PDT 2024

*startlist* is a Python script to generate an HTML interactive start list for 
races created in *RaceDB* and download CrossMgr files. 

## CrossMgr
The script will download all of the CrossMgr files for a specific date and competition.

## StartList
This script is self-contained, all processing is done client side making it
possible to host the file on a *Static Website.*

The rationale behind this is that generation of traditional paper start lists is 
time-consuming and difficult at events. 
Everyone has a cell phone capable of displaying a web page.

E.g. This is an S3 bucket configured as a static website:

   [Vanier Example](https://results.wimsey.co/2024/testing/2024-09-22-Vanier-startlist.html)


This is intended primarily for officials and commissaires running the competition
to replace paper start lists. Minimal notes can be entered and shared.

Officials will have:
- Competition name, when the list was generated
- All event start times
- All start waves for each start time, with start-offset
- Details (laps, distance, minutes), categories and starters for each wave
- List of participants with bib numbers for each start wave

Cookies maintain the notes and selections when the page is refreshed.

- for a specific date find the corresponding RaceDB competition using SQL
- generates an HTML page that has a list of the events for the competition
- each event also has a list of waves and the number of participants in each wave

That table can be used to select an event or wave. Clicking on an event or wave
will display the start list for that event or wave.

Features:
- portrait and landscape display
- iPhone and iPad display
- sorting by column
- competition notes
- sharing notes

N.B. This script will require network access to the computer running RaceDB. The RaceDB/Postgres
container must allow access to port 5432.

## Overview
There are three tables presented.
1. Event name, Bib Search, date file generated, share button, event times for selecting
2. Event information, show all waves with details, categories and number of starters.
3. Wave information, show all participants in an event, or specific wave (click on wave in Event information table)

### Bib Search
Enter a bib number in the bib search input, if found the riders information in the wave table will be highlighted in yellow.

### Rider Competition Notes
Click on a rider to open a competition note field. Riders that have notes will be highlighted in beige.

Click on the "share" button to create a markdown file of all competition notes for download or sharing.

## Screenshots

#### Portrait

![event-portrait](./img/vanier-portrait.png) 

### Landscape

![vanier-landscape](./img/vanier-landscape.png)

## Install

```
python setup.py install
```

## Use

```
startlist --date 20240923 --host racedb.wg
```

## Workflow

Especially for multi-event competitions, e.g. cyclocross, when downloading
the *CrossMgr* file, also run this script to re-generate the start-list
for the day. Then run whatever sync script you need to push it to
your website. 

We use our results website. Officials know that they can get the start-list
there, and reload it just before each race starts to get any updates since
the last race etc.

For my events I use a file hierarchy like:
```
   .../2024/series/LMCX2024/20200923-Vanier/
   .../2024/series/LMCX2024/20200923-Vanier/Makefile
   .../2024/series/LMCX2024/20200923-Vanier/2024-09-22-Vanier-Race 1.xlsx
   .../2024/series/LMCX2024/20200923-Vanier/2024-09-22-Vanier-Race 1-r1-.cmn
   .../2024/series/LMCX2024/20200923-Vanier/2024-09-22-Vanier-Race 1-r1-.html
   .../2024/series/LMCX2024/20200923-Vanier/2024-09-22-Vanier-Race 1-r1-.xlsx
   .../2024/series/LMCX2024/20200923-Vanier/2024-09-22-Vanier-startlist.html

```

A Makefile is used to generate the start-list, download the CrossMgr files, and sync the startlists and results to the website.

From the command line (typically Cygwin in Windows), I would run the following
before the first race, and then after each race after the results are generated,
and to get the startlist and CrossMgr files updated for the next race.

```
   cd .../2024/series/LMCX2024/20200923-Vanier/
   make 
```

Where Makefile is:
```
all: startlist crossmgr sync
   @echo "make startlist crossmgr sync"

startlist:
      startlist --html --host racedb.wg --date $$(expr $$(pwd) : '.*/\(.*\)-.*')

crossmgr:
      startlist --crossmgr --host racedb.wg --date $$(expr $$(pwd) : '.*/\(.*\)-.*')

sync:
      aws s3 sync . s3://results.wimsey.co/2024/series/LMCX2024/20200923-Vanier/ \
         --include='*.html' 
```

N.b. The actual makefile is slightly more complex, it determines the S3 path
based on the file hierarchy.










