#!/usr/bin/env python
"""
MediathekView Websuche - Serverskript

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

#Version: v0.2.1 2014-04-10

#Requires:
# Ubuntu/Debian:   sudo apt-get install python python-lzma  #python-lxml
# Arch Linux:      pacman -S python xz

#Settings:
min_duration_sec = 19*60
min_filesize_mb = 150
medium_minus_sec = 50*60*60*24
medium_plus_sec = 50*60*60*24
good_minus_sec = 7*60*60*24
good_plus_sec = 1*60*60*24

import os
os.nice(5)
import json
try:
    from urllib.request import urlopen
except ImportError: #Python 2.x
    from urllib2 import urlopen
from xml.dom import minidom
import lzma
import time
from datetime import datetime, timedelta



print("***")
print(str(datetime.now()))
print("Mediatheken - Suche: Starting download")

#Download
xmldoc = minidom.parse('mediathek.xml')
itemlist = xmldoc.getElementsByTagName('film-update-server-url')
for item in itemlist[:10]:
    try:
        url = item.firstChild.nodeValue
        response = urlopen(url)
        html = response.read()
        print("Downloaded {} bytes from {}.".format(len(html), url))
        data = lzma.decompress(html)
        print("Extracted {} bytes with {} lines.".format(len(data),
                                                         data.count(b"\n")))
        if data.count(b"\n") > 10000:
            fout = open('full.json', 'wb')
            fout.write(data)
            fout.close()
            break
        else:
            print("Seems too little data, retry.")
    except (TypeError, IOError, ValueError, AttributeError):
            print("Failed, retry up to 10 times.")

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
            zeit_s = (time.mktime(time.strptime(zeit, "%H:%M:%S")) -
                     time.mktime(time.strptime("00:00:00", "%H:%M:%S")))
            groesse_mb = float(l[6])
        except ValueError:
            fail+=1
            continue
        medium_from = time.localtime(time.time() - medium_minus_sec)
        medium_to = time.localtime(time.time() + medium_plus_sec)
        good_from = time.localtime(time.time() - good_minus_sec)
        good_to = time.localtime(time.time() + good_plus_sec)
        if(groesse_mb > min_filesize_mb and zeit_s > min_duration_sec):
            if(url in urls):
                url_duplicates+=1
                continue
            urls[url] = True
            relevance = groesse_mb * 0.01
            relevance += zeit_s * 0.0005
            if(datum_tm > good_from and datum_tm < good_to):
                relevance += 100
            elif(datum_tm > medium_from and datum_tm < medium_to):
                relevance += 40
            dline = [sender, thema, titel, datum, zeit, dauer,
                     beschreibung[:80], url, website, relevance]
            output.append(dline)

#Sort by relevance
sorted_output = sorted(output, key=lambda tup: tup[-1], reverse=True)
output_good = sorted_output[:600]
output_medium = sorted_output[601:10000]

print('Selected {} good ones and {} medium ones, wrote them to json files.'
      .format(len(output_good), len(output_medium)))
print('Ignored {} url duplicates and failed to parse {} out of {} lines.'
      .format(url_duplicates, fail, lines))

with open('good.json', mode='w', encoding='utf-8') as fout:
    json.dump(output_good, fout)
with open('medium.json', mode='w', encoding='utf-8') as fout:
    json.dump(output_medium, fout)

print("Mediatheken - Suche: Fertig")
print(str(datetime.now()))

