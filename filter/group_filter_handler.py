#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

import logging

# TODO: Check list if contains instances of GorupInfoItem class.
def filter_group_info_items(group_info_list, size=0, quota=0):

    new_group_info_list = list()

    if group_info_list is None or len(group_info_list) == 0:
        raise RuntimeError("Empty group_info_list found!")

    for group_info_item in group_info_list:

        if group_info_item.size <= size and group_info_item.quota <= quota:

            logging.debug("Filtered group_info_item for group: %s"
                          % group_info_item.name)

        else:
            new_group_info_list.append(group_info_item)

    return new_group_info_list
