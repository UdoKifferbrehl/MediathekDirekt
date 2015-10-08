#!/usr/bin/python3
"""
MediathekDirekt - Serverskript

Copyright 2014,      martin776
Copyright 2014-2015, Markus Koschany

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

# Requires  Python >= 3.3:
# Ubuntu/Debian:   sudo apt-get install python3
# Arch Linux:      pacman -S python xz

import sys
import os
import json
import time
import logging
import urllib.error
import lzma
from xml.dom import minidom
from datetime import datetime
from urllib.request import urlopen
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter



__all__ = []
__version__ = 0.6
__date__ = '04.02.2014'
__updated__ = '06.10.2015'

# Use nice on UNIX systems and print a warning for all other
# operating systems.

try:
    os.nice(5)
except OSError:
    print("The nice command is only available on UNIX systems."
          "Proceeding without it.")

# Paths
LOG_FILENAME = 'mediathek.log'
URL_SOURCE = 'http://zdfmediathk.sourceforge.net/update-json.xml'


# Logging
logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO)
logger = logging.getLogger("mediathek")


def main(argv=None):
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%s (%s)' % (
        program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

USAGE
''' % (program_shortdesc)

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license,
                                formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument(
            "-d", "--download", dest="download", action="store_true",
            help="download MediathekView's film list")
        parser.add_argument(
            "-c", "--convert", dest="convert", action="store_true",
            help="convert MediathekView's film list to MediathekDirekt format")
        parser.add_argument(
            '-v', '--version', action='version', version=program_version_message)
        parser.add_argument(
            dest="path", help="path to save or load MediathekView's film list [default: current working directory", metavar="path", nargs='?')

        # Process arguments
        args = parser.parse_args()

        # Show help message when no additional arguments are supplied
        if len(sys.argv) == 1:
            parser.print_help()
            sys.exit(1)

        download = args.download
        convert = args.convert
        path = args.path

        if download:
            get_filmlist(path)

        if convert:
            convert_filmlist(path)
    except KeyboardInterrupt:
        # handle keyboard interrupt ###
        return 0


def checkpath(path):
    if path == None:
        validpath = os.getcwd()
    else:
        if not os.path.isdir(path):
            print(
                "The path to this directory does not exist. Please create it first and try again.")
            sys.exit(1)
        else:
            validpath = path
    return validpath


def get_filmlist(path):
    path = checkpath(path)

    logger.info("***")
    logger.info(str(datetime.now()))
    logger.info("MediathekDirekt: Starting download")
    print("Downloading film list...please be patient")

    # Download list of film servers and extract the URLs of the film lists
    try:
        server_list = urlopen(URL_SOURCE)
    except urllib.error.URLError as e:
        logger.error(e.reason)

    xmldoc = minidom.parse(server_list)
    itemlist = xmldoc.getElementsByTagName('URL')

    # Retry downloading the film list n times
    # Reverse order to download the latest list first
    for item in itemlist[::-1]:
        try:
            url = item.firstChild.nodeValue
            response = urlopen(url)
            html = response.read()
            logger.info("Downloaded {} bytes from {}.".format(len(html), url))
            data = lzma.decompress(html)
            logger.info("Extracted {} bytes with {} lines."
                        .format(len(data), data.count(b"\n")))
            if data.count(b"\n") > 10000:
                with open(os.path.join(path, 'full.json'), mode='wb') as fout:
                    fout.write(data)
                    break
            else:
                logger.warning("Not enough data, will retry.")
        except (TypeError, IOError, ValueError, AttributeError) as e:
            logger.error("Failed to download the film list. Will retry .")
            logger.error(e.reason)

    logger.info("MediathekDirekt: Download finished")
    logger.info(str(datetime.now()))


def convert_filmlist(path):
    path = checkpath(path)
    if not os.path.isfile(os.path.join(path, 'full.json')):
        print("The film list does not exist. Please download it first.")
        sys.exit(1)

    logger.info("***")
    logger.info(str(datetime.now()))
    logger.info("MediathekDirekt: Starting conversion")
    print("Converting film list...please be patient")
    # Convert and select
    with open(os.path.join(path, 'full.json'), encoding='utf-8') as fin:
        fail = 0
        sender = ''
        thema = ''
        sender2num = {}
        output = []
        lines = 0
        urls = {}
        url_duplicates = 0
        for line in fin:
            lines += 1
            try:
                l = json.loads(line[8:-2])
            except ValueError:
                fail += 1
                continue
            if(l[0] != ''):
                sender = str(l[0].encode("ascii", "ignore").decode('ascii'))
                sender2num[sender] = 1
            else:
                sender2num[sender] += 1
            if(l[1] != ''):
                thema = l[1]
            titel = l[2]
            datum = l[3]
            dauer = l[5]
            beschreibung = l[7]
            url = l[8]
            website = l[9]

            # Ignore duplicate URLs and skip this line
            if(url in urls):
                url_duplicates += 1
                continue
            urls[url] = True

            # Create a valid Python tuple with all relevant broadcasting
            # information
            dline = (
                sender,
                titel,
                thema,
                datum,
                dauer,
                beschreibung[:80],
                url,
                website
            )
            # Append the broadcast to our converted film list
            output.append(dline)

    logger.info('Selected {} good ones and wrote them to good.json file.'
                .format(len(output)))
    logger.info('Ignored {} url duplicates and failed to parse {} out of {} lines.'
                .format(url_duplicates, fail, lines))

    # Write data to JSON file
    with open(os.path.join(path, 'good.json'), mode='w', encoding='utf-8') as fout:
        json.dump(output, fout, indent=4)

    logger.info("MediathekDirekt: successfully converted film list")
    logger.info(str(datetime.now()))

if __name__ == "__main__":
    sys.exit(main())
