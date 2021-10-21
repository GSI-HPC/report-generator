#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2019 Gabriele Iannetti <g.iannetti@gsi.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


import re
import os
import sys
import logging
import subprocess
from decimal import Decimal
from enum import IntEnum

from dataset.item_handler import GroupInfoItem

from utils.getent_group import get_user_groups


LFS_BIN = 'lfs'

#TODO: Remove and use the one below?
REGEX_STR_QUOTA_CAPTION = r"^\s+Filesystem\s+kbytes\s+quota\s+limit\s+grace\s+files\s+quota\s+limit\s+grace$"
REGEX_PATTERN_QUOTA_CAPTION = re.compile(REGEX_STR_QUOTA_CAPTION)

REGEX_QUOTA_STR_HEADER = r"^Disk\s+quotas\s+for\s+grp\s+(group\d+)\s+\(gid\s+(\d+)\):$"
REGEX_QUOTA_STR_INFO = r"^Filesystem\s+kbytes\s+quota\s+limit\s+grace\s+files\s+quota\s+limit\s+grace$"
REGEX_QUOTA_STR_DATA = r"^(/[\d|\w|/]+)\s+([\d+|\*]+)\s+([\d+|\*]+)\s+([\d+|\*]+)\s+([\d|\w|-]+)\s+([\d+|\*]+)\s+([\d+|\*]+)\s+([\d+|\*]+)\s+([\d|\w|-]+)$"
REGEX_QUOTA_PATTERN_HEADER = re.compile(REGEX_QUOTA_STR_HEADER)
REGEX_QUOTA_PATTERN_INFO = re.compile(REGEX_QUOTA_STR_INFO)
REGEX_QUOTA_PATTERN_DATA = re.compile(REGEX_QUOTA_STR_DATA)

REGEX_STORAGE_STR_HEADER = r"UUID\s+1K-blocks\s+Used\s+Available\s+Use%\s+Mounted on\s*$"
REGEX_STORAGE_STR_MDT = r"([\d|\w]+-MDT[\d|\w]+_UUID)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)%\s+(/[\d|\w|/]+)\[MDT:[\d|\w]+\]$"
REGEX_STORAGE_STR_OST = r"([\d|\w]+-OST[\d|\w]+_UUID)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)%\s+(/[\d|\w|/]+)\[OST:[\d|\w]+\]$"
REGEX_STORAGE_STR_TAIL = r"filesystem_summary:\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)%\s+(/[\d|\w]+)$"
REGEX_STORAGE_PATTERN_HEADER = re.compile(REGEX_STORAGE_STR_HEADER)
REGEX_STORAGE_PATTERN_MDT = re.compile(REGEX_STORAGE_STR_MDT)
REGEX_STORAGE_PATTERN_OST = re.compile(REGEX_STORAGE_STR_OST)
REGEX_STORAGE_PATTERN_TAIL = re.compile(REGEX_STORAGE_STR_TAIL)

class GroupQuotaCatching(IntEnum):
    FILE_SYSTEM = 1
    KBYTES_USED = 2
    KBYTES_QUOTA = 3
    KBYTES_LIMIT = 4
    KBYTES_GRACE = 5
    FILES_COUNT = 6
    FILES_QUOTA = 7
    FILES_LIMIT = 8
    FILES_GRACE = 9


class StorageInfo:
    """Class for storing MDT and OST information"""

    def __init__(self, mount_point):
        self.mount_point = mount_point
        self.mdt = self.StorageComponent()
        self.ost = self.StorageComponent()

    @property
    def mount_point(self):
        """Get mount point"""
        return self._mount_point

    @mount_point.setter
    def mount_point(self, mount_point):
        if mount_point[0] == '/':
            self._mount_point = mount_point
        else:
            raise RuntimeError("Input file may be corrupt")

    class StorageComponent:
        """Class for initializing components"""

        def __init__(self):
            self.total = 0
            self.used = 0
            self.free = 0

        @property
        def total(self):
            """Get total storage"""
            return self._total

        @property
        def used(self):
            """Get used storage"""
            return self._used

        @property
        def free(self):
            """Get free storage"""
            return self._free

        @total.setter
        def total(self, total):
            """Set total storage"""
            if not isinstance(total, int):

                raise TypeError("Total argument must be int type")

            if total < 0:
                raise RuntimeError("Total argument cannot be negative")

            self._total = total

        @used.setter
        def used(self, used):
            """Set used storage"""
            if not isinstance(used, int):
                raise TypeError("Used argument must be int type")

            if used < 0:
                raise RuntimeError("Used argument cannot be negative")

            self._used = used

        @free.setter
        def free(self, free):
            """Set free storage"""
            if not isinstance(free, int):
                raise TypeError("Free argument must be int type")

            if free < 0:
                raise RuntimeError("Free argument cannot be negative")

            self._free = free

        def used_percentage(self):
            """Get used_percentage storage"""

            if (self.used / self.total) * 100.0 > 100:
                raise RuntimeError("Percentage cannot be over 100")

            return (self.used / self.total) * 100.0


def check_path_exists(path):

    if not os.path.exists(path):
        raise RuntimeError("File path does not exist: %s" % path)


def create_lfs_df_input_data(file_system, input_file=None):
    """Generates string out of `lfs df` output either by given input-file or by executing `lfs df`.

    Args:
        file_system (str): Path of filesystem.
        input_file (str): Path to the input file.

    Returns:
        str: A String with the output of `lfs df`.

    Raises:
        IOError: When input file doesn't exist or is not a file.
        RuntimeError: If path of file_system doesn't exist.
    """


    input_data = None

    if input_file:

        if not os.path.isfile(input_file):
            raise IOError("The input file does not exist or is not a file: %s" % input_file)

        with open(input_file, "r") as input_file:
            input_data = input_file.read()

    else:

        check_path_exists(file_system)

        input_data = subprocess.check_output([LFS_BIN, "df", file_system]).decode()

    return input_data


def create_lfs_quota_input_data(file_system, input_file=None):
    """Generates string out of `lfs quota` output either by given input-file or by executing `lfs quota`.

    Args:
        file_system (str): Path of filesystem.
        input_file (str): Path to the input file.

    Returns:
        str: A String with the output of `lfs quota`.

    Raises:
        IOError: When input file doesn't exist or is not a file.
        RuntimeError: If path of file_system doesn't exist.
    """


    input_data = ''

    if input_file:

        if not os.path.isfile(input_file):
            raise IOError("The input file does not exist or is not a file: %s" % input_file)

        with open(input_file, "r") as input_file:
            input_data = input_file.read()

    else:

        check_path_exists(file_system)

        for group_name in get_user_groups():

            output = subprocess.check_output(['sudo', LFS_BIN, 'quota', '-g', group_name, file_system]).decode()

            input_data += output

    return input_data


def lustre_total_size(file_system, input_file=None):

    lfs_df_output = None

    if not input_file:
        lfs_df_output = create_lfs_df_input_data(file_system)

    else:
        lfs_df_output = create_lfs_df_input_data(file_system, input_file)

    storage_info = create_storage_info(lfs_df_output)

    if not file_system in storage_info:
        raise RuntimeError("Storage information doesn't hold file system: %s" % file_system)

    total_size = storage_info[file_system].ost.total

    logging.debug("Lustre total size: %d" % total_size)

    return total_size

def create_group_info_list_dev(input_data):

    if not isinstance(input_data, str):
        raise RuntimeError("Expected input data to be string, got: %s" % type(input_data))

    group_info_item_list = list()

    group_header_found = False
    group_info_found = False

    current_group = None

    for line in input_data.splitlines():

        stripped_line = line.strip()

        if not stripped_line:
            continue

        group_header_result = REGEX_QUOTA_PATTERN_HEADER.match(stripped_line)
        group_info_result = REGEX_QUOTA_PATTERN_INFO.match(stripped_line)
        group_data_result = REGEX_QUOTA_PATTERN_DATA.match(stripped_line)

        if group_info_result:
            continue

        if group_header_result:

            if group_header_found and not group_info_found:
                raise RuntimeError("Group header found before group usage size")

            current_group = group_header_result.group(1)
            group_header_found = True

        elif group_data_result:

            if group_info_found and not group_header_found:
                raise RuntimeError("Group usage size found before group header")

            group_header_found = False
            group_info_found = True

            kbytes_used_raw = group_data_result.group(GroupQuotaCatching.KBYTES_USED)
            kbytes_quota = int(group_data_result.group(GroupQuotaCatching.KBYTES_QUOTA))
            files = int(group_data_result.group(GroupQuotaCatching.FILES_COUNT))

            # exclude '*' in kbytes field, if quota is exceeded!
            if kbytes_used_raw[-1] == '*':
                kbytes_used = int(kbytes_used_raw[:-1])
            else:
                kbytes_used = int(kbytes_used_raw)

            bytes_used = kbytes_used  * 1024
            bytes_quota = kbytes_quota * 1024

            if files > 0:
                group_info_item_list.append(GroupInfoItem(current_group, bytes_used, bytes_quota, files))
            else:
                logging.debug("Skipped group since it has no files: %s" % current_group)

        else:
            logging.error("Line mismatch, skipped line: %s", stripped_line)


    logging.debug(group_info_item_list)
    return group_info_item_list


def create_group_info_list(group_names, fs):

    check_path_exists(fs)

    group_info_item_list = list()

    for grp_name in group_names:

        try:

            group_info = create_group_info_item(grp_name, fs)

            if group_info.files > 0:
                group_info_item_list.append(group_info)
            else:
                logging.debug("Skipped group since it has no files: %s" % group_info.name)

        except Exception as e:

            logging.error("Skipped creation of GroupInfoItem for group: %s" % grp_name)

            exc_type, exc_obj, exc_tb = sys.exc_info()
            filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

            logging.error("Caught exception (%s):\n%s\n%s (line: %s)" %
                (exc_type, str(e), filename, exc_tb.tb_lineno))

    return group_info_item_list


def create_group_info_item(group_name, fs):

    check_path_exists(fs)

    # Example output of 'lfs quota -g rz /lustre':
    #
    ## Disk quotas for grp rz (gid 1002):
    ## Filesystem  kbytes   quota   limit   grace   files   quota   limit   grace
    ## /lustre/hebe 8183208892  107374182400 161061273600       - 2191882       0       0       -

    logging.debug("Querying Quota Information for Group: %s" % (group_name))

    output = subprocess.check_output(\
        ['sudo', LFS_BIN, 'quota', '-g', group_name, fs]).decode()

    logging.debug("Quota Information Output:\n%s" % (output))

    lines = output.rstrip().split('\n')

    if len(lines) < 3:
        raise RuntimeError("'lfs quota' output is to short:\n%s" % output)

    # Check caption line of 'lfs quota' fits the expected line:
    caption_line = lines[1]
    match = REGEX_PATTERN_QUOTA_CAPTION.fullmatch(caption_line)

    if not match:
        raise RuntimeError(
            f"lfs quota caption line: '{caption_line}' did not match the regex: '{REGEX_STR_QUOTA_CAPTION}'")

    fields_line = lines[2].strip()

    # Replace multiple whitespaces with one to split the fields on whitespace.
    fields = re.sub(r'\s+', ' ', fields_line).split(' ')

    kbytes_field = fields[1]
    kbytes_used = None

    # exclude '*' in kbytes field, if quota is exceeded!
    if kbytes_field[-1] == '*':
        kbytes_used = int(kbytes_field[:-1])
    else:
        kbytes_used = int(kbytes_field)

    bytes_used = kbytes_used * 1024

    kbytes_quota = int(fields[2])
    bytes_quota = kbytes_quota * 1024

    files = int(fields[5])

    return GroupInfoItem(group_name, bytes_used, bytes_quota, files)


def create_storage_info(input_data):
    """Generates data structure and calculates storage information of given file systems.

    Args:
        input_data (str): Output of `lfs df` command.

    Returns:
        dict: A Dictionary containing OST and MDT space usage information in bytes stored in a StorageInfo object.

    Raises:
        RuntimeError: If input_data is not a string and if it is corrupt e.g. header found before tail or tail found before header.
    """
    storage_dict = {}

    if not isinstance(input_data, str):
        raise RuntimeError("Expected input data to be string, got: %s" % type(input_data))

    header_found = False
    tail_found = False
    mount_point_info = None

    for line in input_data.splitlines():

        stripped_line = line.strip()

        if not stripped_line:
            continue

        header_result = REGEX_STORAGE_PATTERN_HEADER.match(stripped_line)
        mdt_result = REGEX_STORAGE_PATTERN_MDT.match(stripped_line)
        ost_result = REGEX_STORAGE_PATTERN_OST.match(stripped_line)
        tail_result = REGEX_STORAGE_PATTERN_TAIL.match(stripped_line)

        if header_result:

            if header_found:
                raise RuntimeError("Header found before tail")

            header_found = True
            tail_found = False

        elif mdt_result:

            if not mount_point_info:

                mount_point_info = mdt_result.group(6)
                storage_dict[mount_point_info] = StorageInfo(mount_point_info)
                storage_dict[mount_point_info].mdt.total += int(mdt_result.group(2)) * 1024
                storage_dict[mount_point_info].mdt.used += int(mdt_result.group(3)) * 1024
                storage_dict[mount_point_info].mdt.free += int(mdt_result.group(4)) * 1024

            else:

                storage_dict[mount_point_info].mdt.total += int(mdt_result.group(2)) * 1024
                storage_dict[mount_point_info].mdt.used += int(mdt_result.group(3)) * 1024
                storage_dict[mount_point_info].mdt.free += int(mdt_result.group(4)) * 1024

        elif ost_result:

            if not mount_point_info:

                mount_point_info = ost_result.group(6)
                storage_dict[mount_point_info] = StorageInfo(mount_point_info)
                storage_dict[mount_point_info].ost.total += int(ost_result.group(2)) * 1024
                storage_dict[mount_point_info].ost.used += int(ost_result.group(3)) * 1024
                storage_dict[mount_point_info].ost.free += int(ost_result.group(4)) * 1024

            else:

                storage_dict[mount_point_info].ost.total += int(ost_result.group(2)) * 1024
                storage_dict[mount_point_info].ost.used += int(ost_result.group(3)) * 1024
                storage_dict[mount_point_info].ost.free += int(ost_result.group(4)) * 1024

        elif tail_result:

            if tail_found or not header_found:
                raise RuntimeError("Tail found before header")

            header_found = False
            tail_found = True
            mount_point_info = None

        else:
            logging.error("Line mismatch, skipped line: %s", stripped_line)

    if logging.getLogger().isEnabledFor(logging.DEBUG):

        for key in storage_dict:

            logging.debug("""Mounted on: %s
            MDT-Total: %s
            MDT-Used: %s
            MDT-Free: %s
            MDT-Percentage: %s
            OST-Total: %s
            OST-Used: %s
            OST-Free: %s
            OST-Percentage: %s""",
            key, storage_dict[key].mdt.total, storage_dict[key].mdt.used,
            storage_dict[key].mdt.free, storage_dict[key].mdt.used_percentage(),
            storage_dict[key].ost.total, storage_dict[key].ost.used, storage_dict[key].ost.free,
            storage_dict[key].ost.used_percentage())

    return storage_dict
