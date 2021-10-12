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

from dataset.item_handler import GroupInfoItem


LFS_BIN = 'lfs'

REGEX_STR_QUOTA_CAPTION = r"^\s+Filesystem\s+kbytes\s+quota\s+limit\s+grace\s+files\s+quota\s+limit\s+grace$"
REGEX_PATTERN_QUOTA_CAPTION = re.compile(REGEX_STR_QUOTA_CAPTION)


class StorageInfo:
    """Class for storing MDT and OST information"""

    def __init__(self, mount_point):
        self._mount_point = mount_point
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
                #pass
                raise TypeError("Total argument must be int type")

            self._total = total

        @used.setter
        def used(self, used):
            """Set used storage"""

            if not isinstance(used, int):
                raise TypeError("Used argument must be int type")

            self._used = used

        @free.setter
        def free(self, free):
            """Set free storage"""

            if not isinstance(free, int):
                raise TypeError("Free argument must be int type")

            self._free = free

        def used_percentage(self):
            """Calculate total used storage percentage"""

            used_percentage = (self.used / self.total) * 100.0

            if used_percentage > 100:
                raise RuntimeError("Percentage cannot be greater than 100")

            return used_percentage


def check_path_exists(path):

    if not os.path.exists(path):
        raise RuntimeError("File path does not exist: %s" % path)


def lustre_total_size(file_system, input_data=None):

    lfs_df_output = None

    if not input_data:

        check_path_exists(file_system)

        lfs_df_output = subprocess.check_output([LFS_BIN, "df", file_system]).decode()

    else:
        lfs_df_output = input_data

    storage_info = create_storage_info(lfs_df_output)

    if not file_system in storage_info:
        raise RuntimeError("Storage information doesn't hold file system: %s" % file_system)

    total_size = storage_info[file_system].ost.total

    logging.debug("Lustre total size: %d" % total_size)

    return total_size


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


def create_group_info_item(gid, fs):

    check_path_exists(fs)

    # Example output of 'lfs quota -g rz /lustre':
    #
    ## Disk quotas for grp rz (gid 1002):
    ## Filesystem  kbytes   quota   limit   grace   files   quota   limit   grace
    ## /lustre/hebe 8183208892  107374182400 161061273600       - 2191882       0       0       -

    logging.debug("Querying Quota Information for Group: %s" % (gid))

    output = subprocess.check_output(\
        ['sudo', LFS_BIN, 'quota', '-g', gid, fs]).decode()

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

    return GroupInfoItem(gid, bytes_used, bytes_quota, files)


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

    header_reg_pattern = r"UUID\s+1K-blocks\s+Used\s+Available\s+Use%\s+Mounted on\s*"
    header_reg_comp = re.compile(header_reg_pattern)
    mdt_reg_pattern = r"([\d|\w]+-MDT[\d|\w]+_UUID)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)%\s+(/[\d|\w|/]+)\[MDT:[\d|\w]+\]"
    mdt_reg_comp = re.compile(mdt_reg_pattern)
    ost_reg_pattern = r"([\d|\w]+-OST[\d|\w]+_UUID)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)%\s+(/[\d|\w|/]+)\[OST:[\d|\w]+\]"
    ost_reg_comp = re.compile(ost_reg_pattern)
    tail_reg_pattern = r"filesystem_summary:\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)%\s+(/[\d|\w]+)"
    tail_reg_comp = re.compile(tail_reg_pattern)

    header_found = False
    tail_found = False
    mount_point_info = None

    for line in input_data.splitlines():

        stripped_line = line.strip()

        if not stripped_line:
            continue

        header_result = header_reg_comp.match(stripped_line)
        mdt_result = mdt_reg_comp.match(stripped_line)
        ost_result = ost_reg_comp.match(stripped_line)
        tail_result = tail_reg_comp.match(stripped_line)

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
