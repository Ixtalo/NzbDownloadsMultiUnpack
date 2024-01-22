#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""multiunpackrecursive.py - Recursively unpacks archives files with passwords in file/folder name".

Unpacks multiple Usenet NZB downloads using the password stored in
the file/folder name, e.g. ".../foobar {{password}}/somearchive.rar".

Works for RAR and 7zip archives.

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
#
# LICENSE:
#
# Copyright (c) 2020-2024 by Ixtalo, ixtalo@gmail.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import os
import re
import sys
import io
import logging
from datetime import datetime
from pathlib import Path
import colorlog
from docopt import docopt

__version__ = "1.7.0"
__date__ = "2020-09-02"
__updated__ = "2024-01-20"
__author__ = "Ixtalo"
__license__ = "AGPL-3.0+"
__email__ = "ixtalo@gmail.com"
__status__ = "Production"

# file size threshold which triggers sleep
COOLDOWN_THRESHOLD_MB = 300
# sleep time
COOLDOWN_SECONDS = 60

LOGGING_STREAM = sys.stderr
DEBUG = bool(os.getenv("DEBUG", "").lower() in ("1", "true", "yes"))

# RegEx to find the archive password between curly brackets
PASSWORD_REGEX = r"\{\{([^}]+)\}\}"

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


class Archiver:
    """Base class for archives handling (e.g., RAR, 7zip)."""

    def __init__(self):
        """Handle archiving."""
        self.rm_command = "del /q" if _is_ms_windows() else "rm -fv"

    def build_rm_command(self, filepath: Path) -> str:
        """Construct remove commands."""

    def find_archive_files(self, files: list[str]) -> set[str]:
        """Find the filenames of single or multi-volume archives.

        :param files: list of filenames
        :return set of only the 1st filename of multi-volume archives
        """


class ArchiverRar(Archiver):
    """RAR archives handling."""

    @staticmethod
    def is_volume_primer(filename: str) -> bool:
        """Check if the filename is the first part of a multi-volume RAR archive."""
        return re.search(r"\.part0*1\.rar$", filename, re.IGNORECASE) is not None

    @staticmethod
    def is_volume_part(filename: str) -> bool:
        """Check if the filename is part of a v5 multi-volume RAR archive."""
        return re.search(r"\.part[0-9]+\.rar$", filename, re.IGNORECASE) is not None

    @staticmethod
    def get_basename(filename: str) -> str:
        """Return the archive's basename, i.e., without multi-volume parts."""
        # strip partX, e.g., "xyz.part1.rar" --> "xyz"
        return re.sub(r"(\.part\d+)?\.rar$", "", filename, count=1, flags=re.IGNORECASE)

    def build_rm_command(self, filepath: Path) -> str:
        """Construct remove commands."""
        assert filepath.suffix == ".rar"

        # "xyz.rar" -> ["xyz.rar", "xyz.r*", "xyz.par2"]
        if not ArchiverRar.is_volume_part(filepath.name):
            if Path(filepath.with_suffix(".r00")).exists():
                # 'rm "/absolute/xyz.rar" "/absolute/xyz.r*" "/absolute/xyz.par2'
                return (f'{self.rm_command} "{filepath.resolve()}" '
                        f'"{filepath.with_suffix("").resolve()}".r* '
                        f'"{filepath.with_suffix("").resolve()}.par2"')
            # else
            return f'{self.rm_command} "{filepath.resolve()}" "{filepath.with_suffix(".par2").resolve()}"'

        # strip partX, e.g., "xyz.part1.rar" --> "xyz"
        # "xyz.partNNN.rar" -> "xyz.part*.rar"
        basename = ArchiverRar.get_basename(filepath.name)
        basefilepath = filepath.with_name(f"{basename}").resolve()
        return f'{self.rm_command} "{basefilepath}".part*.rar "{basefilepath}.par2"'

    def find_archive_files(self, files: list[str]) -> set[str]:
        """Find the filenames of single or multi-volume archives.

        :param files: list of filenames
        :return set of only the 1st filename of multi-volume archives
        """
        result = set()

        # single files, no multi-volume
        for filename in files:
            if filename.lower().endswith(".rar") and not self.is_volume_part(filename):
                result.add(filename)

        # multi-volumes
        for filename in files:
            if self.is_volume_primer(filename):
                result.add(filename)

        return result


class Archiver7z(Archiver):
    """7zip archives handling."""

    @staticmethod
    def is_7zip(filename: str) -> bool:
        """Check if the filename is a 7zip single or 7zip multi-volume."""
        return re.search(r"\.7z(\.0*1)?$", filename, re.IGNORECASE) is not None

    @staticmethod
    def get_basename(filename: str) -> str:
        """Return the archive's basename, i.e., without multi-volume parts."""
        # e.g., "xyz.7z.001" -> "xyz"
        return re.sub(r"\.7z(\.[0-9]+)?$", "", filename, count=1, flags=re.IGNORECASE)

    def build_rm_command(self, filepath: Path) -> str:
        """Construct remove commands."""
        assert filepath.suffix in (".7z", ".001")
        basename = Archiver7z.get_basename(filepath.name)
        basefilepath = filepath.with_name(f"{basename}").resolve()
        return f'{self.rm_command} "{basefilepath}".7z* "{basefilepath}.par2"'

    def find_archive_files(self, files: list[str]) -> set[str]:
        """Find the filenames of single or multi-volume archives.

        :param files: list of filenames
        :return set of only the 1st filename of multi-volume archives
        """
        result = set()
        for filename in files:
            if self.is_7zip(filename):
                result.add(filename)
        return result


def _is_ms_windows() -> bool:
    return sys.platform == "win32"


def _construct_quoted(remove_parts: set[str]) -> set[str]:
    # convert to strings, quoted
    return {f'"{str(part)}"' for part in remove_parts}


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

    arar = ArchiverRar()
    a7z = Archiver7z()

    if _is_ms_windows():
        sleep_cmd = "timeout"
        comment = "REM "
    else:
        sleep_cmd = "sleep"
        comment = "# "

    rootdir = Path(arg_root)
    logging.info("root dir: %s", rootdir.resolve())

    commands = []

    # recursive files scanning
    for root, _, files in os.walk(rootdir):

        # find relevant files
        archives = set()
        archives.update(arar.find_archive_files(files))
        archives.update(a7z.find_archive_files(files))
        logging.info("%s, archives: %s", root, ", ".join(archives))
        if not archives:
            # no archive files in this folder...
            continue

        # check for password in filename or folder-name
        pwd = None
        for filename in archives:
            # check if password is in filename or in folder-name
            match = re.search(PASSWORD_REGEX, root)
            if match:
                # password is in folder-name
                pwd = match.group(1)
            else:
                # look in filename
                match = re.search(PASSWORD_REGEX, filename)
                if match:
                    # password is in filename
                    pwd = match.group(1)

            logging.debug("pwd: %s", pwd)

            # full file path input + output directory
            filepath = Path(root, filename).resolve()
            # target directory := archive's directory, absolute
            targetdir = Path(root).resolve()

            # get file size
            filesize_mb = os.stat(filepath).st_size / 1024.0 / 1024.0
            logging.debug("filesize_mb: %.2f", filesize_mb)

            if a7z.is_7zip(filename) or _is_ms_windows():
                # use 7z for 7zip or if on MS Windows (I do not have unrar on my MS Windows)
                #   x       extract with paths
                #   -aos 	Skip extracting of existing files.
                if pwd:
                    cmd = f'7z x -aos -o"{targetdir}/" -p"{pwd}" "{filepath}"'
                else:
                    cmd = f'7z x -aos -o"{targetdir}/" "{filepath}"'
            else:
                # rar file, Linux
                #   x       extract with paths
                #   -o-     do not overwrite
                if pwd:
                    cmd = f'unrar x -o- -p"{pwd}" "{filepath}" "{targetdir}/"'
                else:
                    cmd = f'unrar x -o- "{filepath}" "{targetdir}/"'

            # remove commands
            # RAR
            #   posix:  rm "./some dir/xyz.rar" "./some dir/xyz.r"*
            #   win32:  del /q ".\some dir\xyz.rar" ".\some dir\xyz.r*"
            # 7z
            #   posix:  rm "./some dir/xyz.7z"*
            #   win32:  del /q ".\some dir\xyz.7z*"
            #
            if a7z.is_7zip(filename):
                cmd += f' && {a7z.build_rm_command(filepath)}'
            else:
                # rar
                cmd += f' && {arar.build_rm_command(filepath)}'

            # if file has a relevant size then add some sleep time for cooldown
            if filesize_mb > COOLDOWN_THRESHOLD_MB:
                cmd += f" ; {sleep_cmd} {COOLDOWN_SECONDS}"

            # print
            commands.append(cmd)

    logging.debug("#commands: %d", len(commands))

    if not commands:
        return 2

    output = io.StringIO()
    output.write(
        f"{comment}created by {version_string} at {datetime.now().isoformat()}")
    output.write(os.linesep)
    output.write(f"{comment}{len(commands)} entries")
    output.write(os.linesep)

    # check if any command has non-ASCII characters, e.g. Latin1/Latin15
    if _is_ms_windows():
        has_non_ascii = any([str.isascii(cmd) for cmd in commands])
        logging.debug("has_non_ascii: %s", has_non_ascii)
        if has_non_ascii:
            # switch MS Windows console codepage
            output.write("chcp 1252")
            output.write(os.linesep)
            output.write(f"{comment}{'-' * 50}")
            output.write(os.linesep)

    for i, cmd in enumerate(commands):
        output.write(f"{comment}-- {i+1}. {'-' * 50}")
        output.write(os.linesep)
        output.write(cmd)
        output.write(os.linesep)

    print(output.getvalue())

    return 0


if __name__ == '__main__':
    sys.exit(main())
