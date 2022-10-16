#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""multiunpackrecursive.py - Unpacks multiple RAR archives with passwords in file/folder name".

Unpacks multiple Usenet NZB downloads using the password stored in 
the file/folder name, e.g. ".../foobar {{password}}/somearchive.rar".

Usage:
  multiunpackrecursive.py [options] <directory>
  multiunpackrecursive.py -h | --help
  multiunpackrecursive.py --version

Arguments:
  directory         Starting root directory for recursive scan.

Options:
  -h --help         Show this screen.
  --logfile=FILE    Logging to FILE, otherwise use STDOUT.
  --no-color        No colored log output.
  -v --verbose      Be more verbose.
  --version         Show version.
"""
##
## LICENSE:
##
## Copyright (c) 2020-2022 by Ixtalo, ixtalo@gmail.com
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU Affero General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Affero General Public License for more details.
##
## You should have received a copy of the GNU Affero General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
import os
import sys
import fnmatch
import re
import logging
from docopt import docopt
import colorlog

__version__ = "1.3.0"
__date__ = "2020-09-02"
__updated__ = "2022-10-16"
__author__ = "Ixtalo"
__license__ = "AGPL-3.0+"
__email__ = "ixtalo@gmail.com"
__status__ = "Production"

# file size threshold which triggers sleep
SLEEP_THRESHOLD_MB = 300
# sleep time
SLEEP_SECONDS = 60

LOGGING_STREAM = sys.stderr
DEBUG = bool(os.environ.get("DEBUG", "").lower() in ("1", "true", "yes"))

# RegEx to find the archive password between curly brackets
PWD_REGEX = r"\{\{([^}]+)\}\}"

# check for Python3
if sys.version_info < (3, 0):
    sys.stderr.write("Minimum required version is Python 3.x!\n")
    sys.exit(1)


def __setup_logging(log_file: str = None, verbose=False, no_color=False):
    if log_file:
        # pylint: disable=consider-using-with
        stream = open(log_file, "a", encoding="utf8")
        no_color = True
    else:
        stream = LOGGING_STREAM
    handler = colorlog.StreamHandler(stream=stream)

    format_string = "%(log_color)s%(asctime)s %(levelname)-8s %(message)s"
    formatter = colorlog.ColoredFormatter(format_string,
                                          datefmt="%Y-%m-%d %H:%M:%S",
                                          no_color=no_color)
    handler.setFormatter(formatter)

    logging.basicConfig(level=logging.WARNING, handlers=[handler])
    if verbose or log_file:
        logging.getLogger("").setLevel(logging.INFO)
    if DEBUG:
        logging.getLogger("").setLevel(logging.DEBUG)


def main():
    """Run main program entry.

    :return: exit/return code
    """
    version_string = f"NzbDownloadsMultiUnpack {__version__} ({__updated__})"
    arguments = docopt(__doc__, version=version_string)
    arg_root = arguments["<directory>"]
    arg_logfile = arguments["--logfile"]
    arg_nocolor = arguments["--no-color"]
    arg_verbose = arguments["--verbose"]

    __setup_logging(arg_logfile, arg_verbose, arg_nocolor)
    logging.info(version_string)

    for root, _, files in os.walk(arg_root):
        archives = []

        # single RAR files
        rars = fnmatch.filter(files, '*.rar')
        for filename in rars:
            fn = os.path.splitext(filename)[0]

            # do not consider if it's part of a set (here we only consider single RARs)
            if re.search(r"\.part[0-9]+\.rar$", filename):
                continue

            # make sure that no FILENAME.r00...0 exists
            if [f for f in files if re.search(rf"{fn}\.r0+$", f)]:
                # FILENAME.r00...0 exists -> stop here
                continue

            # just a simple single RAR file -> OK, add it to the list
            archives.append(filename)

        # find first file in sequence, e.g. '...part01.rar' or '...part1.rar'
        archives += [f for f in files if re.search(r"\.part0*1\.rar$", f)]

        # handle old RAR naming style
        # find all those ending with *.r0...0
        rars_old = [f for f in files if re.search(r"\.r0+$", f)]
        if rars_old:
            for filename in rars_old:
                rarname = f"{os.path.splitext(filename)[0]}.rar"
                if rarname not in rars:
                    archives.append(rarname)

        logging.debug("%s, archives: %s", root, archives)

        if not archives:
            # no RAR files in this folder...
            continue

        for filename in archives:
            # check if password in filename or in folder name
            pwd = None
            m = re.search(PWD_REGEX, root)
            if m:
                pwd = m.group(1)
            else:
                # look in filename
                m = re.search(PWD_REGEX, filename)
                if m:
                    pwd = m.group(1)
                else:
                    logging.warning("No password found for %s/%s", root, filename)
                    continue

            logging.debug("pwd: %s", pwd)
            assert pwd

            # full file path input + output directory
            filepath = os.path.abspath(os.path.join(root, filename))
            targetdir = os.path.abspath(root)  # target directory = RAR file directory

            # file size
            filesize_mb = os.stat(filepath).st_size / 1024.0 / 1024.0
            logging.debug("filesize_mb: %.2f", filesize_mb)

            if sys.platform == "win32":
                # MS Windows command
                cmd = f"""7z x -o"{targetdir}/" -p"{pwd}" "{filepath}" && move "{filepath}" "{filepath}.done" """
                # MS Windows sleep command
                sleep_cmd = "timeout"
                comment = "REM"
            else:
                # Linux command
                cmd = f"""unrar x -o- -p"{pwd}" "{filepath}" "{targetdir}/" && mv "{filepath}" "{filepath}.done" """
                # Linux sleep command
                sleep_cmd = "sleep"
                comment = "#"

            # if file has a relevant size then add some sleep time
            if filesize_mb > SLEEP_THRESHOLD_MB:
                cmd += f" && {sleep_cmd} {SLEEP_SECONDS}"

            # print
            print(cmd)
            print(comment, "-"*60)

    return 0


if __name__ == '__main__':
    if DEBUG:
        # sys.argv.append('--verbose')
        pass
    if os.environ.get("PROFILE", "").lower() in ("true", "1", "yes"):
        import cProfile
        import pstats
        profile_filename = f"{__file__}.profile"
        cProfile.run('main()', profile_filename)
        with open(f'{profile_filename}.txt', 'w', encoding="utf8") as statsfp:
            profile_stats = pstats.Stats(profile_filename, stream=statsfp)
            stats = profile_stats.strip_dirs().sort_stats('cumulative')
            stats.print_stats()
        sys.exit(0)
    sys.exit(main())
