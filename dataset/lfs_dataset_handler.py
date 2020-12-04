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


LFS_BIN = '/usr/bin/lfs'

REGEX_STR_QUOTA_CAPTION = r"^\s+Filesystem\s+kbytes\s+quota\s+limit\s+grace\s+files\s+quota\s+limit\s+grace$"
REGEX_PATTERN_QUOTA_CAPTION = re.compile(REGEX_STR_QUOTA_CAPTION)


def check_path_exists(path):

    if not os.path.exists(path):
        raise RuntimeError("File path does not exist: %s" % path)


def lustre_total_size(fs):

    check_path_exists(fs)

    total_size_ost = Decimal(0)

    output = subprocess.check_output([LFS_BIN, "df", fs]).decode()

    if output:

        for line in output.splitlines():

            if 'OST' in line:

                fields = line.split()

                ost_size = Decimal(fields[1]) * Decimal(1024.0)

                total_size_ost += ost_size

            else:
                logging.debug("Ignoring 'lfs df' line: %s" % line)

    if total_size_ost:
        return total_size_ost
    else:
        raise RuntimeError("Total OST size of '%s' is 0!" % fs)


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

            logging.error(
                "Skipped creation of GroupInfoItem for group: %s" % grp_name)

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


