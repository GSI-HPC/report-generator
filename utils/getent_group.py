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
import subprocess

def get_user_groups():

    user_groups = list()
    output = subprocess.check_output(['getent', 'group']).decode()

    output_lines = output.strip().split('\n')

    for line in output_lines:

        fields = line.split(':', 3)
        group = fields[0]
        gid = int(fields[2])

        if gid > 999:
            logging.debug("Found User Group %s:%s" % (group, gid))
            user_groups.append(group)
        else:
            logging.debug("Ignoring User Group: %s:%s" % (group, gid))

    return user_groups
