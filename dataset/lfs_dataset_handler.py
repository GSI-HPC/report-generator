#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2021 Gabriele Iannetti <g.iannetti@gsi.de>
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
import logging
import subprocess
from enum import IntEnum

from dataset.item_handler import GroupInfoItem
from utils.getent_group import get_user_groups

LFS_BIN = 'lfs'

REGEX_QUOTA_STR_BLOCK = r"(?:(?:Disk quotas for grp .*?$).*?(?:(?:[\d\w\/]+){1}(?:(?:\s+[\d\*]+){3}\s+(?:[\d\w|-]+){1}){2}))"
REGEX_QUOTA_STR_HEADER = r"^Disk\s+quotas\s+for\s+grp\s+([\d\w\-_]+)\s+\(gid\s+\d+\):$"
REGEX_QUOTA_STR_INFO = r"^\s*Filesystem(:?\s+[kbytes|files]+\s+quota\s+limit\s+grace){2}$"
REGEX_QUOTA_STR_DATA = r"^\s*([\d\w\-/]+)\s+([\d\*]+)\s+([\d\*]+)\s+([\d\*]+)\s+([\d\w|-]+)\s+([\d\*]+)\s+([\d\*]+)\s+([\d\*]+)\s+([\d\w|-]+)$"
REGEX_QUOTA_PATTERN_BLOCK = re.compile(REGEX_QUOTA_STR_BLOCK, re.MULTILINE|re.DOTALL)
REGEX_QUOTA_PATTERN_HEADER = re.compile(REGEX_QUOTA_STR_HEADER)
REGEX_QUOTA_PATTERN_INFO = re.compile(REGEX_QUOTA_STR_INFO)
REGEX_QUOTA_PATTERN_DATA = re.compile(REGEX_QUOTA_STR_DATA)

REGEX_STORAGE_STR_BLOCK = r"(?:(?:UUID\s+1K-blocks\s+Used.*?$).*?(?:filesystem_summary:(?:\s+[\d]+){3}\s+\d+%\s+[\w\d\/]+))"
REGEX_STORAGE_STR_HEADER = r"UUID\s+1K-blocks\s+Used\s+Available\s+Use%\s+Mounted on\s*$"
REGEX_STORAGE_STR_DATA = r"(?:[\d\w]+-([OST|MDT]+)[\d\w]+_UUID)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)%\s+([\d\w\/]+)\[([OST|MDT]+):[\d\w]+\]"
REGEX_STORAGE_STR_TAIL = r"filesystem_summary:\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)%\s+([\d\w\/]+)$"
REGEX_STORAGE_PATTERN_BLOCK = re.compile(REGEX_STORAGE_STR_BLOCK, re.MULTILINE|re.DOTALL)
REGEX_STORAGE_PATTERN_HEADER = re.compile(REGEX_STORAGE_STR_HEADER)
REGEX_STORAGE_PATTERN_DATA = re.compile(REGEX_STORAGE_STR_DATA)
REGEX_STORAGE_PATTERN_TAIL = re.compile(REGEX_STORAGE_STR_TAIL)

class GroupQuotaCapturing(IntEnum):
    FILE_SYSTEM = 1
    KBYTES_USED = 2
    KBYTES_QUOTA = 3
    KBYTES_LIMIT = 4
    KBYTES_GRACE = 5
    FILES_COUNT = 6
    FILES_QUOTA = 7
    FILES_LIMIT = 8
    FILES_GRACE = 9

class StorageUsageCapturing(IntEnum):
    TARGET = 1
    KBYTES_TOTAL = 2
    KBYTES_USED = 3
    KBYTES_FREE = 4
    KBYTES_USED_PERCENTAGE = 5
    MOUNTPOINT = 6
    TARGET_END = 7


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

def lustre_total_size(file_system, input_file=None):

    if input_file:
        storage_info = create_storage_info(file_system, input_file)
    else:
        storage_info = create_storage_info(file_system)


    if not file_system in storage_info:
        raise RuntimeError("Storage information doesn't hold file system: %s" % file_system)

    total_size = storage_info[file_system].ost.total

    logging.debug("Lustre total size: %d" % total_size)

    return total_size

def create_group_info_list(file_system, input_file=None):

    input_data = None
    group_info_item_list = list()

    if input_file:

        if not os.path.isfile(input_file):
            raise IOError("The input file does not exist or is not a file: %s" % input_file)

        with open(input_file, "r") as input_file:
            input_data = input_file.read()

    else:

        check_path_exists(file_system)

        output_list = list()

        for group_name in get_user_groups():
            output_list.append(subprocess.check_output(['sudo', LFS_BIN, 'quota', '-g', group_name, file_system]).decode())

        input_data = ''.join(output_list)

    if not isinstance(input_data, str):
        raise RuntimeError("Expected input data to be string, got: %s" % type(input_data))

    blocks = REGEX_QUOTA_PATTERN_BLOCK.findall(input_data)

    for block in blocks:

        lines = block.splitlines()

        if len(lines) != 3:
            raise RuntimeError("Invalid size for Block : %s" % block)

        if not REGEX_QUOTA_PATTERN_INFO.match(lines[1]):
            raise RuntimeError("Missing info line in block: %s" % block)

        group_name = REGEX_QUOTA_PATTERN_HEADER.match(lines[0]).group(1)

        data_result = REGEX_QUOTA_PATTERN_DATA.match(lines[2])
        kbytes_used_raw = data_result.group(GroupQuotaCapturing.KBYTES_USED)
        kbytes_quota = int(data_result.group(GroupQuotaCapturing.KBYTES_QUOTA))
        files = int(data_result.group(GroupQuotaCapturing.FILES_COUNT))

        # exclude '*' in kbytes field, if quota is exceeded!
        if kbytes_used_raw[-1] == '*':
            kbytes_used = int(kbytes_used_raw[:-1])
        else:
            kbytes_used = int(kbytes_used_raw)

        bytes_used = kbytes_used * 1024
        bytes_quota = kbytes_quota * 1024

        group_info_item_list.append(GroupInfoItem(group_name, bytes_used, bytes_quota, files))

    logging.debug(group_info_item_list)
    return group_info_item_list

def create_storage_info(file_system, input_file=None):
    """Generates data structure and calculates storage information of given file systems.

    Args:
        input_data (str): Output of `lfs df` command.

    Returns:
        dict: A Dictionary containing OST and MDT space usage information in bytes stored in a StorageInfo object.

    Raises:
        RuntimeError: If input_data is not a string and if it is corrupt e.g. header found before tail or tail found before header.
    """
    storage_dict = {}

    input_data = None

    if input_file:

        if not os.path.isfile(input_file):
            raise IOError("The input file does not exist or is not a file: %s" % input_file)

        with open(input_file, "r") as input_file:
            input_data = input_file.read()

    else:

        check_path_exists(file_system)

        input_data = subprocess.check_output([LFS_BIN, "df", file_system]).decode()

    if not isinstance(input_data, str):
        raise RuntimeError("Expected input data to be string, got: %s" % type(input_data))

    blocks = REGEX_STORAGE_PATTERN_BLOCK.findall(input_data)

    for block in blocks:

        mount_point_info = None

        for line in block.splitlines():

            if not line:
                continue

            result = REGEX_STORAGE_PATTERN_DATA.match(line)

            if result:

                if not mount_point_info:

                    mount_point_info = result.group(StorageUsageCapturing.MOUNTPOINT)
                    storage_dict[mount_point_info] = StorageInfo(mount_point_info)

                if result.group(StorageUsageCapturing.TARGET) == "MDT":

                    storage_dict[mount_point_info].mdt.total += int(result.group(StorageUsageCapturing.KBYTES_TOTAL)) * 1024
                    storage_dict[mount_point_info].mdt.used += int(result.group(StorageUsageCapturing.KBYTES_USED)) * 1024
                    storage_dict[mount_point_info].mdt.free += int(result.group(StorageUsageCapturing.KBYTES_FREE)) * 1024

                elif result.group(StorageUsageCapturing.TARGET) == "OST":

                    storage_dict[mount_point_info].ost.total += int(result.group(StorageUsageCapturing.KBYTES_TOTAL)) * 1024
                    storage_dict[mount_point_info].ost.used += int(result.group(StorageUsageCapturing.KBYTES_USED)) * 1024
                    storage_dict[mount_point_info].ost.free += int(result.group(StorageUsageCapturing.KBYTES_FREE)) * 1024

                else:
                    raise RuntimeError("Target is neither MDT or OST: %s" % line)

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
