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
import os

def transfer_report(run_mode, time_point, path, config):

    if not path:
        raise RuntimeError('Empty path for report found!')

    remote_host = config.get('transfer', 'host')
    remote_path = config.get('transfer', 'path')
    service_name = config.get('transfer', 'service')

    remote_target = \
        remote_host + "::" + remote_path + "/" + time_point.strftime('%Y') + "/"

    if run_mode == 'weekly':
        remote_target += run_mode + "/" + time_point.strftime('%V') + "/"
    elif run_mode == 'monthly':
        remote_target += run_mode + "/" + time_point.strftime('%m') + "/"
    else:
        raise RuntimeError('Undefined run_mode detected: %s' % run_mode)

    remote_target += service_name + "/"

    if not os.path.isfile(path):
        raise RuntimeError('File was not found: %s' % path)

    try:

        subprocess.check_output(["rsync", path, remote_target]).decode()

        logging.debug('rsync %s - %s' % (path, remote_target))

    except subprocess.CalledProcessError as e:
        raise RuntimeError(e.output)
