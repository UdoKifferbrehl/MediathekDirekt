#!/usr/bin/env python

"""
MediathekDirekt - Serverskript

Copyright 2014, martin776
Copyright 2014, Markus Koschany

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see
<http://www.gnu.org/licenses/>.
"""

#Requires:
# Ubuntu/Debian:   sudo apt-get install python3 #requires Python >= 3.3
# Arch Linux:      pacman -S python xz

import os
import json
import time
import logging
import random
from urllib.request import urlopen, urlretrieve
import urllib.error
from xml.dom import minidom
from datetime import datetime, timedelta
import lzma

# Use nice on UNIX systems and print a warning for all other
# operating systems.

try:
    os.nice(5)
except OSError:
    print("The nice command is only available on UNIX systems."
                   "Proceeding without it.")


#Paths
LOG_FILENAME = 'mediathek.log'
URL_SOURCE = 'http://zdfmediathk.sourceforge.net/update-json.xml'


#Settings:
FILM_MIN_DURATION = "00:03:00"
MIN_FILESIZE_MB = 20
MEDIUM_MINUS_SEC = 50*60*60*24
MEDIUM_PLUS_SEC = 50*60*60*24
GOOD_MINUS_SEC = 7*60*60*24
GOOD_PLUS_SEC = 1*60*60*24

#Logging
logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO)
logger = logging.getLogger("mediathek")

logger.info("***")
logger.info(str(datetime.now()))
logger.info("MediathekDirekt: Starting download")

#Download list of filmservers and extract the URLs of the filmlists
try:
    server_list = urlopen(URL_SOURCE)
except urllib.error.URLError as e:
    logger.error(e.reason)

xmldoc = minidom.parse(server_list)
itemlist = xmldoc.getElementsByTagName('URL')

#Retry downloading the filmlist n times
#Reverse order to download the latest list first
for item in itemlist[::-1]:
    try:
        url = item.firstChild.nodeValue
        response = urlopen(url)
        html = response.read()
        logger.info("Downloaded {} bytes from {}.".format(len(html), url))
        data = lzma.decompress(html)
        logger.info("Extracted {} bytes with {} lines.".format(len(data),
                                                         data.count(b"\n")))
        if data.count(b"\n") > 10000:
            fout = open('full.json', 'wb')
            fout.write(data)
            fout.close()
            break
        else:
            logger.warning("Too little data, retry.")
    except (TypeError, IOError, ValueError, AttributeError):
            logger.error("Failed to download the filmlist. Will retry .")

#Convert and select
with open('full.json', encoding='utf-8') as fin:
    fail = 0
    sender = ''
    thema = ''
    sender2num = {}
    output = []
    lines = 0
    urls = {}
    url_duplicates = 0
    for line in fin:
        lines+=1
        try:
            l = json.loads(line[8:-2])
        except ValueError:
            fail+=1
            continue
        if(l[0] != ''):
            sender = str(l[0].encode("ascii","ignore").decode('ascii'))
            sender2num[sender] = 1
        else:
            sender2num[sender] += 1
        if(l[1] != ''):
            thema = l[1]
        titel = l[2]
        datum = l[3]
        zeit = l[4]
        dauer = l[5]
        beschreibung = l[7]
        url = l[8]
        website = l[9]
        bild = l[10]
        try:
            datum_tm = time.strptime(datum, "%d.%m.%Y")
            #convert duration to struct_time
            duration_film = time.strptime(dauer, "%H:%M:%S")
            #convert duration to datetime and subtract it from another datetime
            #object that represents the Unix epoch
            #fixes an OverflowError on 32bit systems
            t1 = datetime(*duration_film[:6])
            epoch = datetime(1970, 1, 1)
            film_duration = t1 - epoch
            groesse_mb = float(l[6])
        except ValueError:
            fail+=1
            continue
        medium_from = time.localtime(time.time() - MEDIUM_MINUS_SEC)
        medium_to = time.localtime(time.time() + MEDIUM_PLUS_SEC)
        good_from = time.localtime(time.time() - GOOD_MINUS_SEC)
        good_to = time.localtime(time.time() + GOOD_PLUS_SEC)

        #convert to datetime object, see film_duration above
        duration_min = time.strptime(FILM_MIN_DURATION, "%H:%M:%S")
        t2 = datetime(*duration_min[:6])
        min_duration = t2 - epoch

        if(groesse_mb > MIN_FILESIZE_MB and film_duration > min_duration):
            if(url in urls):
                url_duplicates+=1
                continue
            urls[url] = True
            relevance = groesse_mb * 0.01
            relevance += film_duration.seconds * 0.0005
            if(datum_tm > good_from and datum_tm < good_to):
                relevance += 100
            elif(datum_tm > medium_from and datum_tm < medium_to):
                relevance += 20
            dline = [sender, titel, thema, datum, dauer,
                     beschreibung[:80], url, website, relevance]
            output.append(dline)

#Sort by relevance
sorted_output = sorted(output, key=lambda tup: tup[-1], reverse=True)
output_good = sorted_output[:10000]

logger.info('Selected {} good ones and wrote them to json files.'
      .format(len(output_good)))
logger.info('Ignored {} url duplicates and failed to parse {} out of {} lines.'
      .format(url_duplicates, fail, lines))

#Write data to JSON files
with open('good.json', mode='w', encoding='utf-8') as fout:
    json.dump(output_good, fout)

logger.info("MediathekDirekt: Download finished")
logger.info(str(datetime.now()))

